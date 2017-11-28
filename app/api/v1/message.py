from flask import Blueprint, request

from app.api.v1.user import User
from app.helpers.fcm import FCM

from app.helpers.handler import Handler
from app.app import mongo

message_endpoint = Blueprint("message", __name__)


# POST { from_id: <string>, to_id: <string> }
@message_endpoint.route("/send", methods=["POST"])
def send_message():
    data = request.json
    from_id = data["from_id"]
    to_id = data["to_id"]

    is_transaction = "amount" in data

    message = {
        "from_id": from_id,
        "to_id": to_id,
        "time": Handler.get_current_time_in_millis(),
        "type": data["type"],
        "message": data["message"],
        "was_seen": False
    }

    mongo.db.messages.insert(message)
    # FCM.notify_partner_chat_update(User.get_user(from_id), User.get_user(to_id))

    return Handler.get_json_res({"success": True})


# POST { my_id: <string>, partner_id: <string> }
@message_endpoint.route("/get", methods=["POST"])
def get_messages():
    data = request.json
    my_id = str(data["my_id"])
    partner_id = str(data["partner_id"])

    participants = [my_id, partner_id]
    query = {"from_id": {"$in": participants}, "to_id": {"$in": participants}}
    messages = list(mongo.db.messages.find(query).sort("time", -1))

    returned_messages = []
    for m in messages:
        returned_messages.append({"message": m, "user": User.get_user(m["from_id"])})

    sorted_list = sorted(returned_messages, key=lambda k: k["message"]["time"], reverse=False)

    return Handler.get_json_res(sorted_list)


# POST { my_id: <string>, partner_id: <string> }
@message_endpoint.route("/mark-seen", methods=["POST"])
def mark_seen():
    data = request.json
    my_id = data["my_id"]
    partner_id = data["partner_id"]
    curr_time = Handler.get_current_time_in_millis()

    query = {"from_id": partner_id, "to_id": my_id, "time": {"$lte": curr_time}}
    messages = list(mongo.db.messages.find(query).sort("time", -1))

    for m in messages:
        m["was_seen"] = True
        mongo.db.messages.save(m)

    # FCM.notify_seen_message(User.get_user(my_id), User.get_user(partner_id))

    return Handler.get_json_res({"success": True})


# POST { id: <string> }
@message_endpoint.route("/get-message-previews", methods=["POST"])
def get_message_preview():
    data = request.json
    my_id = data["user_id"]

    output = []
    users = list(mongo.db.users.find({"user_id": {"$nin": [my_id]}}))

    for user in users:
        preview_message = list(mongo.db.messages.find({
            "$or": [
                {"from_id": my_id},
                {"to_id": my_id}
            ]
        }).sort("time", -1).limit(1))

        if len(preview_message) > 0:
            preview_message = preview_message[0]
            preview_message["type"] = "user_transaction" if "amount" in preview_message else "user_message"
            user["preview_message"] = preview_message
        else:
            user["preview_message"] = {
                "from_id": user["user_id"],
                "to_id": my_id,
                "time": User.get_user(user["user_id"])["creation_time"],
                "type": "new_contact"
            }

        user["unread_count"] = Message.get_unread_count(my_id, user["user_id"])
        output.append(user)

    return Handler.get_json_res(output)


class Message:
    @staticmethod
    def get_unread_count(my_id, partner_id):
        preview_message = list(mongo.db.messages.find({"$and": [{"from_id": partner_id, "to_id": my_id},
                                                                {"was_seen": False}]}))
        return len(preview_message)
