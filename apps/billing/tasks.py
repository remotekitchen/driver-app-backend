from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.billing.models import Delivery
from apps.firebase.models import TokenFCM
from apps.firebase.utils.fcm_helper import send_push_notification

@shared_task
def auto_cancel_deliveries_task():
    now = timezone.now()

    # Fetch deliveries that are waiting for a driver and have no driver assigned
    deliveries = Delivery.objects.filter(
        status=Delivery.STATUS_TYPE.WAITING_FOR_DRIVER,
        assigned=False
    )

    for delivery in deliveries:
        try:
            # Calculate the cancel time (pickup_ready_at - 5 minutes + 30 minutes)
            started_time = delivery.pickup_ready_at - timedelta(minutes=5)
            cancel_time = started_time + timedelta(minutes=30)

            # If the current time exceeds the cancel time, we proceed to cancel the delivery
            if now >= cancel_time:
                # Change the delivery status to 'DELIVERY_FAILED'
                delivery.status = Delivery.STATUS_TYPE.DELIVERY_FAILED
                delivery.cancel_reason = "No driver available after 30 mins"
                delivery.save()

                print(f"✅ Auto-cancelled delivery {delivery.client_id}")

                # Fetch the customer information and send a push notification
                customer_info = delivery.customer_info or {}
                user_id = customer_info.get("user_id")
                if user_id:
                    tokens = list(TokenFCM.objects.filter(user_id=user_id).values_list("token", flat=True))
                    if tokens:
                        send_push_notification(tokens, {
                            "campaign_title": "Delivery Failed",
                            "campaign_message": "We couldn’t assign a delivery person. Your order has been cancelled and refunded.",
                        })

                # If you are integrating a refund system (like bKash), you can call the respective function here
                # trigger_bkash_refund(delivery.client_id)

        except Exception as e:
            # Catch any exceptions and log them
            print(f"❌ Error while cancelling delivery {delivery.client_id}: {str(e)}")
