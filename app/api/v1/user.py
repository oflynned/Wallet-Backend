from random import randint

from flask import Blueprint

from app.helpers.handler import Handler

user = Blueprint("user", __name__)


@user.route("/", methods=["GET", "POST"])
def index():
    return Handler.get_json_res({"file": "user"})
