import base64
import os


def load_logo():

    path = "assets/logo.png"

    if not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
