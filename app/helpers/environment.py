import os


class Environment:
    @staticmethod
    def get_fcm_key():
        return os.environ["FCM_API_KEY"]
