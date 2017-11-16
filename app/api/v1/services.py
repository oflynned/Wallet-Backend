from flask import Blueprint

from app.helpers.handler import Handler

debug = Blueprint("services", __name__)


@debug.route("/", methods=["GET", "POST"])
def get_all_users():
    return Handler.get_json_res({"success": True})
