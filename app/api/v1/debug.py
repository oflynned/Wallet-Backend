from flask import Blueprint

from app.app import mongo
from app.helpers.handler import Handler

debug_endpoint = Blueprint("debug", __name__)


@debug_endpoint.route("/get-all-users", methods=["GET", "POST"])
def get_all_users():
    return Handler.get_json_res(list(mongo.db.users.find()))


@debug_endpoint.route("/get-all-transactions", methods=["GET", "POST"])
def get_all_transactions():
    return Handler.get_json_res(list(mongo.db.transactions.find()))


@debug_endpoint.route("/get-all-messages", methods=["GET", "POST"])
def get_all_messages():
    return Handler.get_json_res(list(mongo.db.messages.find()))


@debug_endpoint.route("/get-all-cards", methods=["GET", "POST"])
def get_all_cards():
    return Handler.get_json_res(list(mongo.db.card.find()))
