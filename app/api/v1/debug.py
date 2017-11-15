from random import randint

from flask import Blueprint

from app.helpers.handler import Handler

debug = Blueprint("debug", __name__)


@debug.route("/", methods=["GET", "POST"])
def index():
    return Handler.get_json_res({"file": "debug"})
