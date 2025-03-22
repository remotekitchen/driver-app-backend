from django.utils import timezone
from django.db.models import F
from apps.accounts.models import DriverWorkHistory, DriverSession
from decimal import Decimal


def update_driver_work_history(driver, delivery):
    """ Updates Driver Work History when a delivery is completed """

    if not driver:
        return  # No driver assigned

    today = timezone.now().date()

    # Get or create today's work history record
    work_history, created = DriverWorkHistory.objects.get_or_create(
        user=driver,
        defaults={
            "total_deliveries": 0,
            "total_earnings": 0.00,
            "offline_count": 0,
            "on_time_deliveries": 0,
            "total_active_hours": 0.00,
            "online_duration": 0.00,
        },
    )

    # Update total deliveries and earnings
    work_history.total_deliveries = F("total_deliveries") + 1
    work_history.total_earnings = F("total_earnings") + Decimal(str(delivery.driver_earning))

    # Check if the delivery was on time
    if delivery.est_delivery_completed_time and delivery.actual_delivery_completed_time <= delivery.est_delivery_completed_time:
        work_history.on_time_deliveries = F("on_time_deliveries") + 1

    # Calculate online duration (assuming driver is active)
    last_session = DriverSession.objects.filter(user=driver, is_active=True).order_by("-created_at").first()
    if last_session:
        time_online = timezone.now() - last_session.created_at
        work_history.online_duration = F("online_duration") + time_online.total_seconds() / 3600

    # Save updates
    work_history.save(update_fields=["total_deliveries", "total_earnings", "on_time_deliveries", "online_duration"])