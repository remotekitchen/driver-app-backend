import requests
from decouple import config


SMS_API_KEY = config("SMS_API_KEY", default="")
URL = "https://api.sms.net.bd/sendsms"


def send_sms_bd(number, text):
    print("Sending SMS to", number)
    payload = {'api_key': SMS_API_KEY, 'msg': f'{text}', 'to': f'{number}'}
    response = requests.request("POST", URL, data=payload)
    return response
  