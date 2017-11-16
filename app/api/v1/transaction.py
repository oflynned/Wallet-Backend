from flask import Blueprint, request

from app.api.v1.user import User, Card
from app.app import mongo
from app.helpers.handler import Handler

transaction_endpoint = Blueprint("transaction", __name__)


@transaction_endpoint.route("/", methods=["GET", "POST"])
def index():
    return Handler.get_json_res({"file": "transaction"})


# make a transaction either to or from your account -- may be positive or negative
# POST { from_id: <string>, to_id: <string>, amount: <float>, description: <string> }
@transaction_endpoint.route("/make-individual-transaction", methods=["POST"])
def individual_transaction():
    data = request.json
    Transaction.make_transaction(data["from_id"], data["to_id"],
                                 data["amount"], data["description"],
                                 "individual_transaction")

    return Handler.get_json_res({"success": True})


# paying for an item via android pay -- take from balance
# POST { user_id: <string>, merchant_id: <string>, amount: <float>, description: <string> }
@transaction_endpoint.route("/make-card-payment", methods=["POST"])
def plynk_card_payment():
    data = request.json
    user_id = data["user_id"]
    card = Card.get_user_card(user_id)

    Transaction.make_transaction(user_id, card["merchant_id"],
                                 data["amount"], data["description"],
                                 "plynk_good_service_payment")
    return Handler.get_json_res({"success": True})


# adding balance via android pay or added card -- add to balance
# POST { user_id: <string>, bank_card_id: <string>, amount: <float>,
#        description: <string>, preload_type: [preload_card|preload_android_pay] }
@transaction_endpoint.route("/make-card-topup", methods=["POST"])
def load_card_money():
    data = request.json
    Transaction.make_transaction(data["bank_card_id"], data["user_id"],
                                 data["amount"], data["description"],
                                 data["preload_type"])
    return Handler.get_json_res({"success": True})


@transaction_endpoint.route("/withdraw-to-bank", methods=["POST"])
def withdraw_to_bank():
    data = request.json
    user = User.get_user(data["user_id"])
    Transaction.make_transaction(data["user_id"], user["bank_card_id"],
                                 data["amount"], data["description"],
                                 "withdrawal_to_bank")


# POST { user_id: <string> }
@transaction_endpoint.route("/query", methods=["POST"])
def query_transactions():
    user_id = request.json["user_id"]
    if User.does_user_exist(user_id):
        transactions = list(mongo.db.transactions.find({"$or": [{"from_id": user_id}, {"to_id": user_id}]}))
        return Handler.get_json_res(transactions)
    return Handler.get_json_res({"success": False})


# POST { user_id: <string> }
@transaction_endpoint.route("/balance", methods=["POST"])
def get_user_balance():
    user_id = request.json["user_id"]

    if User.does_user_exist(user_id):
        pay_transaction_to_user = list(mongo.db.transactions.find({"$and": [
            {"from_id": user_id},
            {"transaction_type": "individual_transaction"}]
        }))

        receive_transaction_from_user = list(mongo.db.transactions.find({"$and": [
            {"to_id": user_id},
            {"transaction_type": "individual_transaction"}]
        }))

        preloadings_to_card = list(mongo.db.transactions.find({
            "$and": [
                {"user_id": user_id},
                {"$or": [
                    {"transaction_type": "preload_card"},
                    {"transaction_type": "preload_android_pay"}
                ]}
            ]
        }))

        user_card_numbers = []
        user_bank_cards = Card.get_user_bank_cards(user_id)
        for card in user_bank_cards:
            user_card_numbers.append(card["card_number"])

        payments_from_card = list(mongo.db.transactions.find({
            "$and": [
                {"user_id": user_id},
                {"from_id": {"$in": user_card_numbers}},
                {"transaction_type": "plynk_good_service_payment"}
            ]
        }))

        withdrawals_to_bank = list(mongo.db.transactions.find({
            "$and": [
                {"user_id": user_id},
                {"to_id": {"$in": user_card_numbers}},
                {"transaction_type": "withdrawal_to_bank"}
            ]
        }))

        balance = 0

        for t in pay_transaction_to_user:
            balance -= t["amount"]
        for t in receive_transaction_from_user:
            balance += t["amount"]

        for t in preloadings_to_card:
            balance += t["amount"]
        for t in payments_from_card:
            balance -= t["amount"]

        for t in withdrawals_to_bank:
            balance -= t["amount"]

        return Handler.get_json_res({"balance": float("{:.2f}".format(balance))})

    return Handler.get_json_res({"success": False})


class Transaction:
    @staticmethod
    def make_transaction(from_id, to_id, amount, description, transaction_type):
        if User.does_user_exist(from_id) and User.does_user_exist(to_id):
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
            return Handler.get_json_res({"success": True})

        return Handler.get_json_res({"success": False})
