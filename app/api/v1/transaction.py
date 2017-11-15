from flask import Blueprint, request

from app.api.v1.user import User
from app.app import mongo
from app.helpers.handler import Handler

transaction_endpoint = Blueprint("transaction", __name__)


@transaction_endpoint.route("/", methods=["GET", "POST"])
def index():
    return Handler.get_json_res({"file": "transaction"})


# POST { from_id: <string>, to_id: <string>, amount: <float>, currency: <string>, description: <string> }
@transaction_endpoint.route("/make-individual-transaction", methods=["POST"])
def individual_transaction():
    data = request.json
    Transaction.make_transaction(data["from_id"], data["to_id"], data["amount"], data["currency"], data["description"])


# POST {  }
@transaction_endpoint.route("/make-card-payment", methods=["POST"])
def plynk_card_payment():
    pass


# POST {  }
@transaction_endpoint.route("/make-card-transaction", methods=["POST"])
def load_card_money():
    pass


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
        # 4 situations to summate to get balance
        # paying someone (negative),
        # getting paid (positive),
        # paying for an item from balance (negative),
        # adding a balance from card (positive)

        pay_transaction_to_user = list(mongo.db.transactions.find({"from_id": user_id}))
        receive_transaction_from_user = list(mongo.db.transactions.find({"to_id": user_id}))

        pay_from_card = list(mongo.db.transactions.find())
        preload_to_card = list(mongo.db.transactions.find())

        balance = 0

        for t in pay_transaction_to_user:
            balance -= t["amount"]
        for t in receive_transaction_from_user:
            balance += t["amount"]

        return Handler.get_json_res({"balance": float("{:.2f}".format(balance))})

    return Handler.get_json_res({"success": False})


class Transaction:
    @staticmethod
    def make_transaction(from_id, to_id, amount, currency, description):
        if User.does_user_exist(from_id) and User.does_user_exist(to_id):
            transaction = {
                "from_id": str(from_id),
                "to_id": str(to_id),
                "amount": float(amount),
                "currency": str(currency),
                "description": str(description),
                "time": Handler.get_current_time_in_millis()
            }

            mongo.db.transactions.save(transaction)
            return Handler.get_json_res({"success": True})

        return Handler.get_json_res({"success": False})
