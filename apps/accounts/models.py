import hashlib
import uuid

from accounts.managers import UserManager
from allauth.socialaccount.models import SocialAccount
from core.models import BaseAddress, BaseModel
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class RoleType(models.TextChoices):
        OWNER = "owner", _("Owner")
        DRIVER = "driver", _("Driver")
        NA = "n/a", _("N/A")

    username = None
    email = models.EmailField(verbose_name=_("Email address"), unique=True)
    phone = models.CharField(max_length=20, verbose_name=_("Phone number"), blank=True)

    role = models.CharField(
        max_length=15,
        verbose_name=_("Role"),
        choices=RoleType.choices,
        default=RoleType.NA,
    )
    address = models.TextField(verbose_name=_("Address"), blank=True)

    date_of_birth = models.DateField(
        verbose_name=_("date of birth"), blank=True, null=True
    )

    reward_points = models.PositiveIntegerField(
        verbose_name=_("Reward points"), default=0
    )
    is_email_verified = models.BooleanField(
        verbose_name=_("is email verified"), default=False
    )
    uid = models.UUIDField(
        verbose_name=_("verify id"), unique=True, blank=True, null=True
    )
    lat = models.FloatField(verbose_name=_("Latitude"), blank=True, null=True)
    lng = models.FloatField(verbose_name=_("Longitude"), blank=True, null=True)
    is_verified_rider = models.BooleanField(
        verbose_name=_("is verified rider"), default=False
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_full_name(self):
        return super().get_full_name()

    def get_google_profile_data(self):
        social_account = SocialAccount.objects.filter(user=self).first()
        try:
            return social_account.extra_data
        except (AttributeError, Exception):
            return {}

    def is_old_user(self, restaurant):
        from billing.models import Order

        q_exp = Q(user=self, restaurant=restaurant)
        q_exp &= Q(payment_method=Order.PaymentMethod.CASH) | Q(is_paid=True)
        return Order.objects.filter(q_exp).exists()


class UserAddress(BaseAddress):
    is_default = models.BooleanField(verbose_name=_("Is default"), default=False)
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name=_("Phone"), blank=True)

    class Meta:
        verbose_name = _("User Address")
        verbose_name_plural = _("User Addresses")

    def __str__(self):
        return f"{self.user.email} :: {self.id}"


class Otp(BaseModel):
    otp = models.PositiveIntegerField(default=0)
    phone = models.CharField(max_length=15)
    is_used = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name = _("OTP")
        verbose_name_plural = _("OTPs")

    def __str__(self) -> str:
        return f"{self.otp} | is_used: {self.is_used}"

    def validate_lat_lng(lat, lng):
      if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValidationError(_("Invalid latitude/longitude values"))
class Meta:
    indexes = [
        models.Index(fields=['email']),
        models.Index(fields=['phone']),
    ]