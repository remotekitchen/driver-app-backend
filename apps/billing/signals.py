from django.db.models.signals import post_save, pre_save

from apps.billing.models import Delivery
from apps.billing.utils.client_status_update import client_status_updater
from django.dispatch import receiver
from apps.firebase.utils.fcm_helper import get_dynamic_message, send_push_notification
from apps.firebase.models import TokenFCM
from django.contrib.auth import get_user_model

User = get_user_model()


def delivery_instance(sender, instance: Delivery, created, **kwargs):
    if not instance.status in [
        Delivery.STATUS_TYPE.CREATED,
        # Delivery.STATUS_TYPE.DRIVER_ASSIGNED,
        Delivery.STATUS_TYPE.WAITING_FOR_DRIVER,
    ]:
        client_status_updater(instance)


post_save.connect(delivery_instance, sender=Delivery)





PREVIOUS_DELIVERY_STATUSES = {}


@receiver(pre_save, sender=Delivery)
def track_status_change(sender, instance, **kwargs):
    """
    Tracks the previous delivery status and marks changes.
    Also marks new instances for post-save signal logic.
    """
    if instance.pk:
        try:
            previous_instance = Delivery.objects.get(pk=instance.pk)
            PREVIOUS_DELIVERY_STATUSES[instance.pk] = previous_instance.status

            if previous_instance.status != instance.status:
                instance._status_changed = True
                print(f"[PRE_SAVE] Status changed from {previous_instance.status} → {instance.status}")
            else:
                print("[PRE_SAVE] Status did not change.")
        except Delivery.DoesNotExist:
            PREVIOUS_DELIVERY_STATUSES[instance.pk] = None
            print("[PRE_SAVE] Delivery record not found (new?).")
    else:
        # New delivery object, mark as created
        instance._is_new = True
        PREVIOUS_DELIVERY_STATUSES[instance.pk] = None
        print("[PRE_SAVE] New delivery instance detected (no PK).")


@receiver(post_save, sender=Delivery)
def handle_delivery_update(sender, instance: Delivery, created, **kwargs):
    print("[POST_SAVE] Delivery signal triggered.")
    print(f"→ Delivery ID: {instance.id}")
    print(f"→ Delivery Status: {instance.status}")
    print(f"→ Raw created flag: {created}")

    # Our safe fallback flags
    truly_created = getattr(instance, '_is_new', False)
    status_changed = getattr(instance, '_status_changed', False)

    if not truly_created and not status_changed:
        print("[POST_SAVE] Skipping: no creation or status change.")
        return

    # If needed, update client (e.g. tracking updates)
    if instance.status not in [
        Delivery.STATUS_TYPE.CREATED,
        Delivery.STATUS_TYPE.WAITING_FOR_DRIVER,
    ]:
        print("[POST_SAVE] Triggering client status updater.")
        client_status_updater(instance)

    event_type = instance.status.lower()

    # Determine user to notify: driver or customer
    user = instance.driver
    if not user and instance.customer_info.get("user_id"):
        user = User.objects.filter(id=instance.customer_info["user_id"]).first()

    if not user:
        print("[POST_SAVE] No user (driver or customer) found. Skipping notification.")
        return

    tokens = list(TokenFCM.objects.filter(user=user).values_list("token", flat=True))
    if not tokens:
        print(f"[POST_SAVE] No FCM tokens found for user ID: {user.id}")
        return

    # Dynamic push message
    restaurant_name = instance.pickup_address.name if instance.pickup_address else "Pickup Location"
    title, body = get_dynamic_message(instance, event_type, restaurant_name)

    data = {
        "campaign_title": title,
        "campaign_message": body,
    }

    send_push_notification(tokens, data)
    print(f"🔔 Notification sent to user ID {user.id}: {title} - {body}")

    # Clean up memory cache
    PREVIOUS_DELIVERY_STATUSES.pop(instance.pk, None)