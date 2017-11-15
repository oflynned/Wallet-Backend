from random import randint

from flask import Blueprint

from app.helpers.handler import Handler

points = Blueprint("points", __name__)


@points.route("/", methods=["GET", "POST"])
def index():
    data = []
    for i in range(10):
        data.append(randint(0, 100))

    return Handler.get_json_res(data)
