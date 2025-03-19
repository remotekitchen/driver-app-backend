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



@receiver(pre_save, sender=Delivery)
def track_status_change(sender, instance, **kwargs):
    """Track if the status of a delivery is being updated."""
    if instance.pk:  # Ensure it's an update, not a new object
        previous_instance = Delivery.objects.get(pk=instance.pk)
        if previous_instance.status != instance.status:
            instance._status_changed = True  # Mark the status as changed

@receiver(post_save, sender=Delivery)
def handle_delivery_update(sender, instance: Delivery, created, **kwargs):
    if created:
        client_status_updater(instance)

    if not created and getattr(instance, "_status_changed", False):
        event_type = instance.status.lower()
        
        # Use driver or extract user from customer_info
        user = instance.driver or None  # If driver exists, use it
        if not user and instance.customer_info.get("user_id"):  # Try to get user from customer_info
            user = User.objects.filter(id=instance.customer_info["user_id"]).first()

        if not user:
            return  # No user found, no need to proceed

        tokens = list(TokenFCM.objects.filter(user=user).values_list("token", flat=True))
        restaurant_name = instance.pickup_address.name  

        if not tokens:
            return

        title, body = get_dynamic_message(instance, event_type, restaurant_name)

        # Send push notification
        send_push_notification(tokens, title, body)

        print(f"🔔 Notification Sent: {title} - {body}")  # For debugging
