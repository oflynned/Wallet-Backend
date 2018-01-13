import os

from flask import Flask
from flask_pymongo import PyMongo

frontend_dir = os.path.abspath("../../templates")
static_dir = os.path.abspath("../../static/")

# use __init__.py to initialise any DB connections and create a singleton object if required
# also used to register new endpoints for API
app = Flask(__name__, template_folder=frontend_dir, static_folder=static_dir)

if "MONGODB_URI" in os.environ:
    app.config["MONGO_URI"] = os.environ["MONGODB_URI"]
    print("Using remote server")
else:
    app.config["MONGO_URI"] = "mongodb://localhost:27017/card_service"
    print("Using local server")

mongo = PyMongo(app)
