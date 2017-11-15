import os

from flask import Flask

frontend_dir = os.path.abspath("../../templates")
static_dir = os.path.abspath("../../static/")

# use __init__.py to initialise any DB connections and create a singleton object if required
# also used to register new endpoints for API
app = Flask(__name__, template_folder=frontend_dir, static_folder=static_dir)
