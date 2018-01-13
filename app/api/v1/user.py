from datetime import datetime
from random import randint

from flask import Blueprint, request

from app.app import mongo
from app.helpers.handler import Handler

user_endpoint = Blueprint("user", __name__)


# POST
# user_details: { user_id: <string>, forename: <string>, surname: <string>, gender: [male|female] }
@user_endpoint.route("/create", methods=["POST"])
def create_user():
    data = request.json
    user_id = data["user_id"]

    if User.does_user_exist(user_id):
        return Handler.get_json_res({"success": False, "reason": "user_already_exists"})

    data["profile_pic"] = "https://graph.facebook.com/" + data["user_id"] + "/picture?type=large"
    data["creation_time"] = Handler.get_current_time_in_millis()

    mongo.db.users.save(data)
    Card.generate_user_card(user_id)

    return Handler.get_json_res({"success": True})


# POST { user_id: <string> }
@user_endpoint.route("/add-bank-card", methods=["POST"])
def add_user_bank_card():
    data = request.json
    user_id = data["user_id"]

    if not Card.did_user_add_bank_card(user_id):
        Card.add_user_bank_card(
            user_id,
            Card.generate_card_number(),
            Card.generate_card_cvv(),
            Card.generate_card_expiry()
        )
        return Handler.get_json_res({"success": True})
    return Handler.get_json_res({"success": False, "reason": "bank_card_already_added"})


# POST { user_id: <string> }
@user_endpoint.route("/get-bank-card", methods=["POST"])
def get_bank_cards():
    data = request.json
    user_id = data["user_id"]

    if User.does_user_exist(user_id):
        return Handler.get_json_res(Card.get_user_bank_card(user_id))

    return Handler.get_json_res({"success": False})


# POST { user_id: <string> }
@user_endpoint.route("/get-digital-card", methods=["POST"])
def get_digital_card():
    data = request.json
    user_id = data["user_id"]

    if User.does_user_exist(user_id):
        return Handler.get_json_res(Card.get_user_card(user_id))

    return Handler.get_json_res({"success": False})


# POST { user_id: <string> }
@user_endpoint.route("/get", methods=["POST"])
def get_user():
    data = request.json
    return Handler.get_json_res(User.get_user(data["user_id"]))


@user_endpoint.route("/get-all", methods=["GET"])
def get_all_users():
    return Handler.get_json_res(list(mongo.db.users.find()))


@user_endpoint.route("/get-other-users", methods=["POST"])
def get_other_users():
    my_id = request.json["user_id"]
    users = list(mongo.db.users.find({"user_id": {"$nin": [my_id]}}))
    return Handler.get_json_res(users)


@user_endpoint.route("/delete", methods=["POST"])
def delete_user():
    mongo.db.users.remove({"user_id": "1686100871401476"})
    return Handler.get_json_res({})


# POST { user_id: <string>, fcm_token: <string> }
@user_endpoint.route("/edit-fcm", methods=["POST"])
def edit_user_fcm():
    user_id = request.json["user_id"]

    if User.does_user_exist(user_id):
        user = User.get_user(user_id)
        user["fcm_token"] = user_id
        mongo.db.users.save(user)
        return Handler.get_json_res({"success": True})

    return Handler.get_json_res({"success": False})


class User:
    @staticmethod
    def get_user(user_id):
        if User.does_user_exist(user_id):
            return list(mongo.db.users.find({"user_id": user_id}))[0]
        return {}

    @staticmethod
    def does_user_exist(user_id):
        return mongo.db.users.find({"user_id": user_id}).count() > 0


class Card:
    @staticmethod
    def generate_user_card(user_id):
        if User.does_user_exist(user_id):
            if not Card._was_user_allocated_card(user_id):
                card_cvv = Card.generate_card_cvv()
                card_number = Card.generate_card_number()
                card_expiry = Card.generate_card_expiry()

                mongo.db.card.save({
                    "user_id": user_id,
                    "is_digital_card": True,
                    "card_number": card_number,
                    "card_cvv": card_cvv,
                    "card_expiry": card_expiry
                })

    @staticmethod
    def add_user_bank_card(user_id, card_number, card_cvv, card_expiry):
        if User.does_user_exist(user_id):
            if not Card._does_bank_card_exist(user_id, card_number, card_cvv, card_expiry):
                mongo.db.card.save({
                    "user_id": user_id,
                    "is_digital_card": False,
                    "card_number": card_number,
                    "card_cvv": card_cvv,
                    "card_expiry": card_expiry
                })

    @staticmethod
    def _does_bank_card_exist(user_id, number, cvv, expiry):
        return mongo.db.card.find({"$and": [
            {"user_id": user_id},
            {"card_number": number},
            {"card_expiry": expiry},
            {"card_cvv": cvv}
        ]}).count() > 0

    @staticmethod
    def get_user_bank_card(user_id):
        bank_card = list(mongo.db.card.find({"$and": [
            {"user_id": user_id},
            {"is_digital_card": False}
        ]}))

        if len(bank_card) == 0:
            return {"success": False}

        bank_card = bank_card[0]
        bank_card["user"] = User.get_user(user_id)
        return bank_card

    @staticmethod
    def get_user_card(user_id):
        card = list(mongo.db.card.find({"$and": [
            {"user_id": user_id},
            {"is_digital_card": True}
        ]}))[0]
        card["user"] = User.get_user(user_id)
        return card

    @staticmethod
    def generate_card_cvv():
        return randint(100, 999)

    @staticmethod
    def generate_card_number():
        output = ""

        for i in range(4):
            for j in range(4):
                output += str(randint(0, 9))

        return output

    @staticmethod
    def generate_card_expiry():
        current_time = datetime.now()
        year = current_time.year + 2
        month = current_time.month
        day = current_time.day
        return str(day) + "/" + str(month) + "/" + str(year)

    @staticmethod
    def did_user_add_bank_card(user_id):
        return mongo.db.card.find({"user_id": user_id, "is_digital_card": False}).count() > 0

    @staticmethod
    def _was_user_allocated_card(user_id):
        return mongo.db.card.find({"user_id": user_id, "is_digital_card": True}).count() > 0
