import os

from flask import Flask
from flask_pymongo import PyMongo

from app.api.v1.debug import debug
from app.api.v1.message import message
from app.api.v1.transaction import transaction_endpoint
from app.api.v1.user import user

frontend_dir = os.path.abspath("templates/")
static_dir = os.path.abspath("static/")

app = Flask(__name__, template_folder=frontend_dir, static_folder=static_dir)

app.register_blueprint(debug, url_prefix="/api/v1/debug")
app.register_blueprint(message, url_prefix="/api/v1/message")
app.register_blueprint(transaction_endpoint, url_prefix="/api/v1/transaction")
app.register_blueprint(user, url_prefix="/api/v1/user")

app.config["MONGO_URI"] = "mongodb://localhost:27017/plynk"
mongo = PyMongo(app)
