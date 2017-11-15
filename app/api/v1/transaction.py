from random import randint

from flask import Blueprint

from app.helpers.handler import Handler

transaction = Blueprint("transaction", __name__)


@transaction.route("/", methods=["GET", "POST"])
def index():
    return Handler.get_json_res({"file": "transaction"})
