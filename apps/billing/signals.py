from django.db.models.signals import post_save, pre_save

from apps.billing.models import Delivery
from apps.billing.utils.client_status_update import client_status_updater
from django.dispatch import receiver
from apps.firebase.utils.fcm_helper import get_dynamic_message, send_push_notification

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
        restaurant_name = instance.pickup_address.name  
        title, body = get_dynamic_message(instance, event_type, "restaurant_name")

        # Send push notification
        send_push_notification(["eARqwgn909Od2l537qeQM6:APA91bF5VXcZO1UqApaIu2eV5iboOPSlnqdU61svFL4zWtqrMAf4GtDwpK15NWHBaImRFcTKnMITrQsbxtagsT35M2VBr7S6uJCUqj6Me1sTuP_0ho2pusA"], title, body)

        print(f"🔔 Notification Sent: {title} - {body}")  # For debugging