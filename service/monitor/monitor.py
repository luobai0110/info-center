import os

import requests
from dotenv import load_dotenv

load_dotenv()
notify_url = os.getenv("HTTP_NOTICE_URL")


def warning(message: str, module: str, from_="@system", to_="@doomer", type_=3):
    params = {
        "message": message,
        "from": from_,
        "to": to_,
        "type": type_,
        "title": module + "告警"
    }
    resp = requests.post(notify_url + "/notice", json=params)
    if resp.status_code != 200:
        # TODO 重试机制
        print(resp.text)
