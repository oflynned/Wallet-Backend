from random import randint

from flask import Blueprint

from app.helpers.handler import Handler

message = Blueprint("message", __name__)


@message.route("/", methods=["GET", "POST"])
def index():
    return Handler.get_json_res({"file": "message"})
