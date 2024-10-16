from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager


class User(AbstractUser):
    class RoleType(models.TextChoices):
        OWNER = "owner", _("Owner")
        EMPLOYEE = "employee", _("Employee")
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
        verbose_name=_("Date of birth"), blank=True, null=True
    )

    reward_points = models.PositiveIntegerField(
        verbose_name=_("Reward points"), default=0
    )
    is_email_verified = models.BooleanField(
        verbose_name=_("Is email verified"), default=False
    )
    is_verified_driver = models.BooleanField(
        verbose_name=_("Is verified driver"), default=False
    )
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    uid = models.UUIDField(
        verbose_name=_("Verify ID"), unique=True, blank=True, null=True
    )

    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",  # Custom related name to avoid conflict
        blank=True,
        verbose_name=_("Groups"),
        help_text=_(
            "The groups this user belongs to. A user will get all permissions granted to each of their groups."
        ),
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions_set",  # Custom related name to avoid conflict
        blank=True,
        verbose_name=_("User permissions"),
        help_text=_("Specific permissions for this user."),
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
