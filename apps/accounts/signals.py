from allauth.account.utils import perform_login
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.db.models import Sum
from apps.billing.models import Delivery
from apps.accounts.models import DriverSession
from allauth.socialaccount.signals import pre_social_login
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models import F
from decimal import Decimal
from apps.billing.models import Delivery
from .utils import update_driver_work_history  # Import the function

User = get_user_model()


@receiver(pre_social_login)
def link_to_local_user(sender, request, sociallogin, **kwargs):
    email_address = sociallogin.account.extra_data.get("email")
    if email_address:
        users = User.objects.filter(email=email_address)
        if users:
            perform_login(request, users[0], email_verification="optional")



@receiver(post_save, sender=Delivery)
def order_delivered_update_history(sender, instance, **kwargs):
    """ Updates driver work history when an order is marked as delivered """
    if instance.status == Delivery.STATUS_TYPE.DELIVERY_SUCCESS:
        update_driver_work_history(instance.driver, instance)