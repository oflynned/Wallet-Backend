from flask import Blueprint, request

from app.app import mongo
from app.helpers.handler import Handler

user = Blueprint("user", __name__)


# POST
# {
# user_details: { user_id: <string>, forename: <string>, surname: <string>, birthday: <date>, gender: [male|female] }
# }
@user.route("/create", methods=["POST"])
def create_user():
    data = request.json

    if User.does_user_exist(data["user_id"]):
        return Handler.get_json_res({"success": False, "reason": "user_already_exists"})

    mongo.db.users.save(data)
    return Handler.get_json_res({"success": True})


# POST { user_id: <string> }
@user.route("/get", methods=["POST"])
def get_user():
    data = request.json
    return User.get_user(data["user_id"])


# POST { user_id: <string>, passport_details: { passport_number: <string> }
@user.route("/add-passport-details", methods=["POST"])
def add_passport_details():
    pass


# POST {
# user_id:  <string>,
# address:  {
#               house_number: <string>, street: <string>, city: <string>,
#               county: <string>, country: <string>, postcode: <string>
#           }
# }
@user.route("/add-address-details", methods=["POST"])
def add_address_details():
    pass


# POST { user_id: <string>, fcm_token: <string> }
@user.route("/edit-fcm", methods=["POST"])
def edit_user_fcm():
    user_id = request.json["user_id"]

    if User.does_user_exist(user_id):
        user = User.get_user(user_id)
        user["fcm_token"] = user_id
        mongo.db.users.save(user)
        return Handler.get_json_res({"success": True})

    return Handler.get_json_res({"success": False})


@user.route("/delete", methods=["POST"])
def delete_user():
    pass


class User:
    @staticmethod
    def get_user(user_id):
        if User.does_user_exist(user_id):
            return list(mongo.db.users.find({"user_id": user_id}))[0]
        return {}

    @staticmethod
    def does_user_exist(user_id):
        return mongo.db.users.find({"user_id": user_id}).count() > 0
