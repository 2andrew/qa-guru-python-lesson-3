import os


class Server:
    def __init__(self, env):
        self.user_service = {
            "dev": os.getenv("APP_URL")
        }[env]
