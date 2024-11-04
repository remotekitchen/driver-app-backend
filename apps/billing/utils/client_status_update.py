import requests
from decouple import config

from apps.billing.models import Delivery


def client_status_updater(instance: Delivery):
    url = config("CHATCHEFS_URL")
    data = {
        "event": "status",
        "client_id": instance.client_id,
        "uid": f"{instance.uid}",
        "status": instance.status,
    }
    res = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
        },
        json=data,
        allow_redirects=False,
    )
    print(res)
    return
