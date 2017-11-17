from flask import Blueprint, request

from app.api.v1.user import User, Card
from app.app import mongo
from app.helpers.handler import Handler

transaction_endpoint = Blueprint("transaction", __name__)


@transaction_endpoint.route("/", methods=["GET", "POST"])
def index():
    return Handler.get_json_res(list(mongo.db.transactions.find()))


# make a transaction either to or from your account -- may be positive or negative
# POST { from_id: <string>, to_id: <string>, amount: <float>, description: <string> }
@transaction_endpoint.route("/make-individual-transaction", methods=["POST"])
def individual_transaction():
    data = request.json
    outcome = Transaction.make_transaction(data["from_id"], data["to_id"],
                                           data["amount"], data["description"],
                                           "individual_transaction")

    return Handler.get_json_res({"success": outcome})


# paying for an item via android pay -- take from balance
# POST { user_id: <string>, merchant_id: <string>, amount: <float>, description: <string> }
@transaction_endpoint.route("/make-card-payment", methods=["POST"])
def plynk_card_payment():
    data = request.json
    user_id = data["user_id"]
    amount = data["amount"]

    if User.does_user_exist(user_id):
        if Transaction.get_user_balance(user_id) >= amount:
            outcome = Transaction.make_transaction(user_id, data["merchant_id"],
                                                   data["amount"], data["description"],
                                                   "plynk_good_service_payment")
            return Handler.get_json_res({"success": outcome})

        return Handler.get_json_res({"success": False, "reason": "insufficient_funds"})

    return Handler.get_json_res({"success": False, "reason": "user_not_found"})


# adding balance via android pay or added card -- add to balance
# POST { user_id: <string>, bank_card_id: <string>, amount: <float>,
#        description: <string>, preload_type: [preload_card|preload_android_pay] }
@transaction_endpoint.route("/make-card-topup", methods=["POST"])
def load_card_money():
    data = request.json
    Transaction.make_institution_transaction(data["bank_card_id"], data["user_id"],
                                             data["amount"], data["description"],
                                             data["preload_type"])
    return Handler.get_json_res({"success": True})


@transaction_endpoint.route("/withdraw-to-bank", methods=["POST"])
def withdraw_to_bank():
    data = request.json
    user_id = data["user_id"]

    if Card.did_user_add_bank_card(user_id):
        bank_card = Card.get_user_card(user_id)
        amount = data["amount"]

        if Transaction.get_user_balance(user_id) > amount:
            Transaction.make_institution_transaction(user_id, bank_card["card_number"],
                                                     data["amount"], data["description"],
                                                     "withdrawal_to_bank")
            return Handler.get_json_res({"success": True})
        else:
            return Handler.get_json_res({"success": False, "reason": "insufficient_funds"})
    return Handler.get_json_res({"success": False, "reason": "no_card_added"})


# POST { user_id: <string> }
@transaction_endpoint.route("/query", methods=["POST"])
def query_transactions():
    user_id = request.json["user_id"]
    if User.does_user_exist(user_id):
        transactions = list(
            mongo.db.transactions.find({"$or": [
                {"user_id": user_id},
                {"from_id": user_id},
                {"to_id": user_id}
            ]}))

        for t in transactions:
            if User.does_user_exist(t["from_id"]):
                t["paid_from"] = User.get_user(t["from_id"])
            else:
                t["paid_from"] = {
                    "user_id": t["transaction_type"],
                    "name": t["transaction_type"],
                    "picture_url": ""
                }

            if User.does_user_exist(t["to_id"]):
                t["paid_to"] = User.get_user(t["to_id"])
            else:
                t["paid_to"] = {
                    "user_id": t["transaction_type"],
                    "name": t["transaction_type"],
                    "picture_url": ""
                }

        return Handler.get_json_res(transactions)
    return Handler.get_json_res({"success": False})


# POST { user_id: <string> }
@transaction_endpoint.route("/balance", methods=["POST"])
def get_user_balance():
    user_id = request.json["user_id"]

    if User.does_user_exist(user_id):
        balance = Transaction.get_user_balance(user_id)
        return Handler.get_json_res({"balance": float("{:.2f}".format(balance))})

    return Handler.get_json_res({"success": False})


class Transaction:
    @staticmethod
    def get_money_institutions():
        # android pay, bank
        return [{
            "user_id": "android_pay"
        }, {
            "user_id": "bank"
        }]

    @staticmethod
    def make_transaction(from_id, to_id, amount, description, transaction_type):
        if User.does_user_exist(from_id):
            transaction = {
                "from_id": str(from_id),
                "to_id": str(to_id),
                "amount": float(amount),
                "currency": "euro",
                "description": str(description),
                "transaction_type": transaction_type,
                "time": Handler.get_current_time_in_millis()
            }

            mongo.db.transactions.save(transaction)
            return True

        return False

    @staticmethod
    def make_institution_transaction(from_id, to_id, amount, description, transaction_type):
        transaction = {
            "from_id": str(from_id),
            "to_id": str(to_id),
            "amount": float(amount),
            "currency": "euro",
            "description": str(description),
            "transaction_type": transaction_type,
            "time": Handler.get_current_time_in_millis()
        }

        mongo.db.transactions.save(transaction)

        return True

    @staticmethod
    def get_transaction_log(user_id):
        return list(mongo.db.transactions.find({"$or": [
            {"to_id": user_id},
            {"from_id": user_id}
        ]}))

    @staticmethod
    def get_user_balance(user_id):
        if User.does_user_exist(user_id):
            balance = 0

            pay_transaction_to_user = list(mongo.db.transactions.find({"$and": [
                {"from_id": user_id},
                {"transaction_type": "individual_transaction"}]
            }))

            for t in pay_transaction_to_user:
                balance -= t["amount"]

            receive_transaction_from_user = list(mongo.db.transactions.find({"$and": [
                {"to_id": user_id},
                {"transaction_type": "individual_transaction"}]
            }))

            for t in receive_transaction_from_user:
                balance += t["amount"]

            preloadings_via_android_pay = list(mongo.db.transactions.find({
                "$and": [
                    {"to_id": user_id},
                    {"transaction_type": "preload_android_pay"}
                ]
            }))

            for t in preloadings_via_android_pay:
                balance += t["amount"]

            user_card = Card.get_user_bank_card(user_id)
            if "card_number" in user_card:
                user_card_number = user_card["card_number"]
                preloadings_via_card = list(mongo.db.transactions.find({
                    "$and": [
                        {"from_id": user_card_number},
                        {"to_id": user_id},
                        {"transaction_type": "preload_card"}
                    ]
                }))

                for t in preloadings_via_card:
                    balance += t["amount"]

            payments_from_card = list(mongo.db.transactions.find({
                "$and": [
                    {"from_id": user_id},
                    {"transaction_type": "plynk_good_service_payment"}
                ]
            }))

            for t in payments_from_card:
                balance -= t["amount"]

            withdrawals_to_bank = list(mongo.db.transactions.find({
                "$and": [
                    {"from_id": user_id},
                    {"transaction_type": "withdrawal_to_bank"}
                ]
            }))

            for t in withdrawals_to_bank:
                balance -= t["amount"]

            return balance
