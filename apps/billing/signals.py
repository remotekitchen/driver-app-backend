from django.db.models.signals import post_save, pre_save

from apps.billing.models import Delivery, DeliveryIssue
from apps.billing.utils.client_status_update import client_status_updater
from apps.billing.utils.send_sms import send_sms_bd
from django.dispatch import receiver
from apps.firebase.utils.fcm_helper import get_dynamic_message, send_push_notification
from apps.firebase.models import TokenFCM
from django.contrib.auth import get_user_model
from django.utils import timezone
import pytz
User = get_user_model()


def delivery_instance(sender, instance: Delivery, created, **kwargs):
    if not instance.status in [
        Delivery.STATUS_TYPE.CREATED,
        # Delivery.STATUS_TYPE.DRIVER_ASSIGNED,
        Delivery.STATUS_TYPE.WAITING_FOR_DRIVER,
    ]:
        client_status_updater(instance)


post_save.connect(delivery_instance, sender=Delivery)




# Cache for previous statuses

PREVIOUS_DELIVERY_STATUSES = {}


@receiver(pre_save, sender=Delivery)
def track_status_change(sender, instance, **kwargs):
    """
    Detect if delivery status is changing.
    """
    if instance.pk:
        try:
            previous_instance = Delivery.objects.get(pk=instance.pk)
            PREVIOUS_DELIVERY_STATUSES[instance.pk] = previous_instance.status

            if previous_instance.status != instance.status:
                instance.status_changed = True
                print(f"[PRE_SAVE] Status changed from {previous_instance.status} → {instance.status}")
            else:
                print("[PRE_SAVE] Status unchanged.")
        except Delivery.DoesNotExist:
            PREVIOUS_DELIVERY_STATUSES[instance.pk] = None
            print("[PRE_SAVE] Delivery not found.")
    else:
        instance.is_new = True  # Optional if you're setting this manually
        PREVIOUS_DELIVERY_STATUSES[instance.pk] = None
        print("[PRE_SAVE] New Delivery detected (no PK).")


@receiver(post_save, sender=Delivery)
def handle_delivery_update(sender, instance: Delivery, **kwargs):
    print("[POST_SAVE] Delivery signal triggered.", instance.pickup_customer_name)
    print(f"→ Delivery ID: {instance.id}")
    print(f"→ Status: {instance.status}")

    is_new = getattr(instance, "is_new", False)
    status_changed = getattr(instance, "status_changed", False)

    if not is_new and not status_changed:
        print("[POST_SAVE] Skipping — neither new nor status changed.")
        return

    event_type = instance.status.lower()



    tokens = list(TokenFCM.objects.values_list("token", flat=True))
    if not tokens:
        print(f"[POST_SAVE] No tokens found for all user.")
        return

    restaurant_name = instance.pickup_customer_name
    title, body = get_dynamic_message(instance, event_type, restaurant_name)

    data = {
        "campaign_title": title,
        "campaign_message": body,
    }

    print("[POST_SAVE] Sending push notification...")
    print("tokens", tokens)
    send_push_notification(tokens, data)

    PREVIOUS_DELIVERY_STATUSES.pop(instance.pk, None)


@receiver(post_save, sender=Delivery)
def update_driver_timestamps(sender, instance, created, **kwargs):
    """
    Set EST timestamps based on delivery status:
    - Set rider_accepted_time when status is DRIVER_ASSIGNED.
    - Set rider_pickup_time when status is ORDER_PICKED_UP.
    """
    now_est = timezone.now()
    bdt = pytz.timezone('Asia/Dhaka')
    bdt_time = timezone.now().astimezone(bdt)
    if instance.status == Delivery.STATUS_TYPE.DRIVER_ASSIGNED and not instance.rider_accepted_time:
        
        instance.rider_accepted_time = bdt_time
        instance.save(update_fields=["rider_accepted_time"])

    elif instance.status == Delivery.STATUS_TYPE.ORDER_PICKED_UP and not instance.rider_pickup_time:
        instance.rider_pickup_time = bdt_time
        instance.save(update_fields=["rider_pickup_time"])


@receiver(post_save, sender=DeliveryIssue)
def notify_delivery_issue(sender, instance, created, **kwargs):
    if created:
        issue = instance
        message = f"New delivery issue reported!\nType: {issue.get_issue_type_display()}\nReported by: {issue.get_reported_by_display()}\nDelivery ID: {issue.delivery.id}"
        phone_number = "01711690821"
        send_sms_bd(phone_number, message)