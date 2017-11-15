import time

from bson import json_util
from flask import Response


class Handler:
    @staticmethod
    def get_current_time_in_millis():
        return int(round(time.time() * 1000))

    @staticmethod
    def get_json_res(data):
        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )
