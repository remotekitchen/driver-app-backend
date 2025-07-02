from datetime import timedelta
from django.utils import timezone
import requests
from apps.billing.models import Delivery

class OnTimeGuaranteeService:
    def __init__(self, delivery):
        self.delivery = delivery

    def run(self):
        if not self.delivery.est_delivery_completed_time or not self.delivery.actual_delivery_completed_time:
            print("Error: Missing delivery time data.")
            return

        delay = self.delivery.actual_delivery_completed_time - self.delivery.est_delivery_completed_time
        delay_minutes = delay.total_seconds() / 60

        if delay_minutes <= 0:
            return  # No delay, no reward

        reward_amount = 0
        if delay_minutes <= 10:
            reward_amount = 10
        elif delay_minutes <= 15:
            reward_amount = 15
        elif delay_minutes <= 30:
            reward_amount = 20

        if reward_amount > 0:
            self.issue_reward(reward_amount)

    def issue_reward(self, reward_amount):
        customer_info = self.delivery.customer_info[0] if isinstance(self.delivery.customer_info, list) else self.delivery.customer_info
        user_id = customer_info.get("user_id")

        if not user_id:
            print("❌ No user_id found in customer_info")
            return

        payload = {
            "user_id": user_id,
            "reward_amount": reward_amount,
            "reward_type": "coupon",
            "order_id": self.delivery.id,
           "expiry_date": (timezone.now() + timedelta(days=7)).date().isoformat()

        }

        print(f"📤 Payload: {payload}")
        print(f"📡 Sending reward request to API...")

        try:
            response = requests.post(
                # "http://127.0.0.1:8000/api/reward/v1/reward/issue/",
                "https://api.chatchefs.com/api/reward/v1/reward/issue/",
                json=payload,
                timeout=5
            )
            print(f"✅ Status Code: {response.status_code}")
            print(f"📩 Response Text: {response.text}")

            if response.status_code in [200, 201]:
                print(f"✅ Reward issued to user {user_id}")
            else:
                print(f"❌ Failed to issue reward: {response.status_code} → {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Exception while issuing reward: {e}")
