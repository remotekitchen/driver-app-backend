from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.billing.models import Delivery
from apps.firebase.models import TokenFCM
from apps.firebase.utils.fcm_helper import send_push_notification
import requests

@shared_task(name="delivery.auto_cancel_deliveries_task")
def auto_cancel_deliveries_task():
    now = timezone.now()

    deliveries = Delivery.objects.filter(
        status=Delivery.STATUS_TYPE.WAITING_FOR_DRIVER,
        assigned=False
    )

    for delivery in deliveries:
        try:
            cancel_time = delivery.pickup_ready_at + timedelta(minutes=30)
            remaining = cancel_time - now
            print(f"⏳ Delivery ID {delivery.id} (Client: {delivery.client_id}) will be auto-cancelled in {remaining}")

            if now >= cancel_time:
                delivery.status = Delivery.STATUS_TYPE.DELIVERY_FAILED
                delivery.cancel_reason = "No driver available after 30 mins"
                delivery.save()

                print(f"✅ Auto-cancelled delivery {delivery.client_id}")

                # 🔔 Notify Chatchef webhook
                try:
                    requests.post("http://127.0.0.1:8000/api/webhook/v1/raider/", json={
                        "event": "status",
                        "client_id": delivery.client_id,
                        "status": delivery.status,
                        "cancel_reason": delivery.cancel_reason,
                    })
                    print(f"📤 Notified Chatchef for cancelled delivery {delivery.client_id}")
                except Exception as e:
                    print(f"❌ Failed to notify Chatchef webhook: {str(e)}")

        except Exception as e:
            print(f"❌ Error while cancelling delivery {delivery.client_id}: {str(e)}")
