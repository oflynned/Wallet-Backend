import os

from flask import Flask

from app.api.v1.points import points
from app.api.v1.debug import debug
from app.api.v1.message import message
from app.api.v1.transaction import transaction
from app.api.v1.user import user

frontend_dir = os.path.abspath("templates/")
static_dir = os.path.abspath("static/")

app = Flask(__name__, template_folder=frontend_dir, static_folder=static_dir)

app.register_blueprint(points, url_prefix="/api/v1/points")
app.register_blueprint(debug, url_prefix="/api/v1/debug")
app.register_blueprint(message, url_prefix="/api/v1/message")
app.register_blueprint(transaction, url_prefix="/api/v1/transaction")
app.register_blueprint(user, url_prefix="/api/v1/user")
