from allauth.account.utils import perform_login
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.db.models import Sum
from apps.billing.models import Delivery
from apps.accounts.models import DriverSession, DriverWorkHistory
from django.utils import timezone
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
        work_history, created = DriverWorkHistory.objects.get_or_create(user=instance.driver)

        work_history.total_deliveries += 1
        if not isinstance(work_history.total_earnings, Decimal):
            work_history.total_earnings = Decimal(str(work_history.total_earnings))

        driver_earning_decimal = Decimal(str(instance.driver_earning))
        work_history.total_earnings += driver_earning_decimal

        if instance.actual_delivery_completed_time and instance.est_delivery_completed_time:
            if instance.actual_delivery_completed_time <= instance.est_delivery_completed_time:
                work_history.on_time_deliveries += 1

        # Look for the most recent active DriverSession with last_online_time
        session = (
            DriverSession.objects.filter(user=instance.driver, is_active=True)
            .order_by("-last_online_time")
            .first()
        )

        if session and session.last_online_time:
            time_online = (timezone.now() - session.last_online_time).total_seconds() / 3600
            work_history.online_duration += round(Decimal(time_online), 2)

        work_history.save()