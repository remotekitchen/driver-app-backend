from django.db.models.signals import post_save

from apps.billing.models import Delivery
from apps.billing.utils.client_status_update import client_status_updater


def delivery_instance(sender, instance: Delivery, created, **kwargs):
    if not instance.status in [
        Delivery.STATUS_TYPE.CREATED,
        Delivery.STATUS_TYPE.DRIVER_ASSIGNED,
        Delivery.STATUS_TYPE.WAITING_FOR_DRIVER,
    ]:
        client_status_updater(instance)


post_save.connect(delivery_instance, sender=Delivery)
