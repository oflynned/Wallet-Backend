from datetime import datetime
from random import randint

from flask import Blueprint, request

from app.app import mongo
from app.helpers.handler import Handler

user = Blueprint("user", __name__)


# POST
# user_details: { user_id: <string>, forename: <string>, surname: <string>, gender: [male|female] }
@user.route("/create", methods=["POST"])
def create_user():
    data = request.json
    user_id = data["user_id"]

    if User.does_user_exist(user_id):
        return Handler.get_json_res({"success": False, "reason": "user_already_exists"})

    mongo.db.users.save(data)
    Card.generate_user_card(user_id)

    return Handler.get_json_res({"success": True})


# POST { user_id: <string>, card_number: <string>, card_cvv: <int>, card_expiry: <dd/mm/yyyy> }
@user.route("/add-bank-card", methods=["POST"])
def add_user_bank_card():
    data = request.json
    Card.add_user_bank_card(data["user_id"], data["card_number"], data["card_cvv"], data["card_expiry"])
    return Handler.get_json_res({"success": True})


# POST { user_id: <string> }
@user.route("/get-bank-cards", methods=["POST"])
def get_bank_cards():
    data = request.json
    user_id = data["user_id"]

    if User.does_user_exist(user_id):
        return Handler.get_json_res(Card.get_user_bank_cards(user_id))

    return Handler.get_json_res({"success": False})


# POST { user_id: <string> }
@user.route("/get-plynk-card", methods=["POST"])
def get_plynk_card():
    data = request.json
    user_id = data["user_id"]

    if User.does_user_exist(user_id):
        return Handler.get_json_res(Card.get_user_card(user_id))

    return Handler.get_json_res({"success": False})


# POST { user_id: <string> }
@user.route("/get", methods=["POST"])
def get_user():
    data = request.json
    return Handler.get_json_res(User.get_user(data["user_id"]))


# POST { user_id: <string>, fcm_token: <string> }
@user.route("/edit-fcm", methods=["POST"])
def edit_user_fcm():
    user_id = request.json["user_id"]

    if User.does_user_exist(user_id):
        user = User.get_user(user_id)
        user["fcm_token"] = user_id
        mongo.db.users.save(user)
        return Handler.get_json_res({"success": True})

    return Handler.get_json_res({"success": False})


@user.route("/delete", methods=["POST"])
def delete_user():
    pass


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
                card_cvv = Card._generate_card_cvv()
                card_number = Card._generate_card_number()
                card_expiry = Card._generate_card_expiry()

                mongo.db.card.save({
                    "user_id": user_id,
                    "is_plynk_card": True,
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
                    "is_plynk_card": False,
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
    def get_user_bank_cards(user_id):
        bank_cards = list(mongo.db.card.find({"$and": [
            {"user_id": user_id},
            {"is_plynk_card": False}
        ]}))

        for card in bank_cards:
            card["user"] = User.get_user(user_id)
        return bank_cards

    @staticmethod
    def get_user_card(user_id):
        card = list(mongo.db.card.find({"$and": [
            {"user_id": user_id},
            {"is_plynk_card": True}
        ]}))[0]
        card["user"] = User.get_user(user_id)
        return card

    @staticmethod
    def _generate_card_cvv():
        return randint(100, 999)

    @staticmethod
    def _generate_card_number():
        output = ""

        for i in range(4):
            for j in range(4):
                output += str(randint(0, 9))

        return output

    @staticmethod
    def _generate_card_expiry():
        current_time = datetime.now()
        year = current_time.year + 2
        month = current_time.month
        day = current_time.day
        return str(day) + "/" + str(month) + "/" + str(year)

    @staticmethod
    def _was_user_allocated_card(user_id):
        return mongo.db.card.find({"user_id": user_id}).count() > 0
