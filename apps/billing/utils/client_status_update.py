import requests
from decouple import config

from apps.billing.models import Delivery
from django.forms.models import model_to_dict
from datetime import datetime
from apps.billing.api.base.serializers import DeliveryGETSerializer

def serialize_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value

def client_status_updater(instance: Delivery):
    print("client_status_updater----------->")
    url = config("CHATCHEFS_URL")
    print(url, 'url------------>')
    
  
    # print(instance.driver.rider_profile, 'instance.driver')
    # Check if the driver is assigned (not None)
    if instance.driver:
        print(instance.driver.rider_profile, 'instance.driver')  # Only access rider_profile if driver exists
    else:
        print("No driver assigned to this delivery", instance.client_id)
    
    serializer = DeliveryGETSerializer(instance)
    
    print(serializer.data, 'serializer.data')

        
    data = {
        "event": "status",
        "client_id": instance.client_id,
        "uid": f"{instance.uid}",
        "status": instance.status,
        "actual_delivery_completed_time": serialize_datetime(instance.actual_delivery_completed_time),
        "rider_accepted_time": serialize_datetime(instance.rider_accepted_time),
        "rider_pickup_time":serialize_datetime(instance.rider_pickup_time),
        # "driver_info": [serializer.data['driver']],
    }

    # If a driver exists, include driver info in the request payload
    if instance.driver:
        data["driver_info"] = [serializer.data['driver']]
    else:
        data["driver_info"] = []

    res = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
        },
        json=data,
        allow_redirects=False,
    )
    print(res, 'res----------->')
    return
