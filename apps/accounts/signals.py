from allauth.account.utils import perform_login
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.db.models import Sum
from apps.billing.models import Delivery
from apps.accounts.models import DriverSession, DriverWorkHistory
from allauth.socialaccount.signals import pre_social_login
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models import F
from decimal import Decimal

User = get_user_model()


@receiver(pre_social_login)
def link_to_local_user(sender, request, sociallogin, **kwargs):
    email_address = sociallogin.account.extra_data.get("email")
    if email_address:
        users = User.objects.filter(email=email_address)
        if users:
            perform_login(request, users[0], email_verification="optional")

@receiver(post_save, sender=DriverSession)
def handle_driver_offline(sender, instance, **kwargs):
    if not instance.is_active:
        if instance.last_active_time:
            active_duration = now() - instance.last_active_time
            active_hours = round(active_duration.total_seconds() / 3600, 2)
            instance.total_active_hours += Decimal(str(active_hours))
            instance.offline_count += 1
            instance.last_active_time = now()
        else:
            instance.last_active_time = now()

        # Temporarily disconnect the signal to prevent recursion
        post_save.disconnect(handle_driver_offline, sender=DriverSession)
        instance.save()
        # Reconnect the signal
        post_save.connect(handle_driver_offline, sender=DriverSession)
    else:
        instance.last_active_time = now()
        post_save.disconnect(handle_driver_offline, sender=DriverSession)
        instance.save()
        post_save.connect(handle_driver_offline, sender=DriverSession)

@receiver(post_save, sender=Delivery)
def update_driver_work_history(sender, instance, **kwargs):
    if instance.status == Delivery.STATUS_TYPE.DELIVERY_SUCCESS:
        work_history, _ = DriverWorkHistory.objects.get_or_create(user=instance.driver)
        deliveries = Delivery.objects.filter(driver=instance.driver, status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS)

        work_history.total_deliveries = deliveries.count()
        work_history.total_earnings = deliveries.aggregate(total_earnings=Sum('driver_earning'))['total_earnings'] or 0.00
        work_history.on_time_deliveries = deliveries.filter(
            actual_delivery_completed_time__lte=F('est_delivery_completed_time')
        ).count()

        # Sync with the latest session data
        driver_session = DriverSession.objects.filter(user=instance.driver).order_by('-last_active_time').first()
        if driver_session:
            work_history.offline_count = driver_session.offline_count
            work_history.total_active_hours = driver_session.total_active_hours

        work_history.save()

@receiver(post_save, sender=DriverSession)
def update_driver_work_history_on_session_change(sender, instance, **kwargs):
    """
    Updates the DriverWorkHistory when a DriverSession changes state (e.g., goes offline).
    """
    current_date = now().date()

    # Ensure there is a work history for today
    print(instance.user, 'instance----------->')
    work_history, created = DriverWorkHistory.objects.get_or_create(
        user=instance.user,
        defaults={
            'total_deliveries': 0,
            'total_earnings': 0.0,
            'offline_count': 0,
            'online_duration': 0,
        }
    )

    # Handle the offline event
    if not instance.is_active:
        # Increase the offline count
        work_history.offline_count += 1

        # Calculate the total online duration for today
        print(instance.user, 'instance.user----------->')
        driver_sessions = DriverSession.objects.filter(
            user=instance.user,
            created_at__date=current_date
        )
        
        total_online_duration = sum(
            (session.updated_at - session.created_at).total_seconds() 
            for session in driver_sessions if session.is_active
        )
        
        work_history.online_duration = total_online_duration

        # Update the work history
        work_history.save()

