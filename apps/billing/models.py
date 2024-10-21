import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import Address, BaseModel

User = get_user_model()


class Delivery(BaseModel):

    class CURRENCY_TYPE(models.TextChoices):
        USD = "usd", _("USD")
        CAD = "CAD", _("CAD")
        BDT = "bdt", _("BDT")

    class STATUS_TYPE(models.TextChoices):
        CREATED = "created", _("CREATED")
        WAITING_FOR_DRIVER = "waiting_for_driver", _("WAITING_FOR_DRIVER")
        DRIVER_ASSIGNED = "driver_assign", _("DRIVER_ASSIGNED")
        ORDER_PICKED_UP = "order_picked_up", _("ORDER_PICKED_UP")
        ON_THE_WAY = "on_the_way", _("ON_THE_WAY")
        DELIVERY_SUCCESS = "delivery_success", _("DELIVERY_SUCCESS")
        DELIVERY_FAILED = "delivery_failed", _("DELIVERY_FAILED")
        DRIVER_REJECTED = "driver_rejected", _("DRIVER_REJECTED")

    class PLATFORM_TYPE(models.TextChoices):
        CHATCHEFS = "chatchefs", _("CHATCHEFS")
        NA = "na", _("NA")

    class PAYMENT_METHOD_TYPE(models.TextChoices):
        CASH = "cash", _("CASH")
        CARD = "card", _("CARD")

    uid = models.UUIDField(verbose_name=_("Order ID"), default=uuid.uuid4, unique=True)

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("driver"),
        related_name="driver",
        blank=True,
        null=True,
    )
    client_id = models.CharField(max_length=255, verbose_name=_("client id"))
    platform = models.CharField(
        max_length=50,
        verbose_name=_("platform"),
        default=PLATFORM_TYPE.CHATCHEFS,
        choices=PLATFORM_TYPE.choices,
    )

    pickup_address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, verbose_name=_("pickup address")
    )
    pickup_customer_name = models.CharField(
        max_length=255, verbose_name=_("pickup customer name")
    )
    pickup_latitude = models.FloatField(default=0)
    pickup_longitude = models.FloatField(default=0)
    pickup_phone = models.CharField(max_length=20, verbose_name="pickup phone number")
    pickup_ready_at = models.DateTimeField(verbose_name=_("pickup ready at"))
    pickup_last_time = models.DateTimeField(verbose_name=_("pickup last time"))

    drop_off_address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, verbose_name=_("pickup address")
    )
    drop_off_customer_name = models.CharField(
        max_length=255, verbose_name=_("drop of customer name")
    )
    drop_off_latitude = models.FloatField(default=0)
    drop_off_longitude = models.FloatField(default=0)
    drop_off_phone = models.CharField(
        max_length=20, verbose_name=_("drop off phone number")
    )
    drop_off_last_time = models.DateTimeField(verbose_name=_("drop off last time"))
    delivery_completed_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("delivery completed time")
    )

    status = models.CharField(
        max_length=100,
        choices=STATUS_TYPE.choices,
        default=STATUS_TYPE.WAITING_FOR_DRIVER,
        verbose_name=_("status"),
    )

    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_TYPE.choices,
        default=CURRENCY_TYPE.BDT,
        verbose_name=_("currency"),
    )
    ride_duration = models.PositiveIntegerField(default=0)
    distance = models.PositiveIntegerField(default=0)
    fees = models.PositiveIntegerField(default=0)
    tips = models.PositiveIntegerField(default=0)
    discount = models.PositiveIntegerField(default=0)
    cash_collected = models.PositiveIntegerField(default=0)
    amount = models.PositiveIntegerField(default=0)

    payment_type = models.CharField(
        max_length=50,
        default=PAYMENT_METHOD_TYPE.CARD,
        choices=PAYMENT_METHOD_TYPE.choices,
        verbose_name=_("payment type"),
    )
