from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager, ProfileManager
from apps.core.models import Address, BaseModel


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
    address = models.TextField(verbose_name=_("delivery zone"), blank=True)

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


class Profile(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("user"),
        related_name="rider_profile",
    )
    dp = models.ImageField(
        upload_to="users/dp/%Y/%m/%d/", verbose_name=_("profile picture")
    )

    present_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("raider present address"),
        related_name="present_address",
    )
    permanent_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("raider permanent address"),
        related_name="permanent_address",
    )

    nid = models.CharField(max_length=50, verbose_name=_("nid"))
    nid_front = models.ImageField(
        upload_to="verification/nid/%Y/%m/%d/", verbose_name=_("nid front")
    )
    nid_back = models.ImageField(
        upload_to="verification/nid/%Y/%m/%d/", verbose_name=_("nid back")
    )

    driving_license = models.CharField(
        max_length=100, verbose_name=_("driving license"), blank=True, null=True
    )
    driving_license_front = models.ImageField(
        upload_to="verification/dl/%Y/%m/%d/", verbose_name=_("driving license front")
    )
    driving_license_back = models.ImageField(
        upload_to="verification/dl/%Y/%m/%d/", verbose_name=_("driving license back")
    )

    is_verified = models.BooleanField(default=False)


    objects = ProfileManager() 

    def __str__(self):
        return f"{self.user.email} :: {self.id}"


class Vehicle(BaseModel):
    class TYPE(models.TextChoices):
        CAR = "car", _("CAR")
        BIKE = "bike", _("BIKE")
        CYCLE = "cycle", _("CYCLE")
        WALKER = "walker", _("WALKER")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("user"))

    dp = models.ImageField(
        upload_to="vehicle/%Y/%m/%d/",
        verbose_name=_("vehicle picture"),
        blank=True,
        null=True,
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=TYPE.choices,
        default=TYPE.BIKE,
        verbose_name=_("vehicle type"),
    )
    registration_number = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("registration number")
    )
    brand = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("brand")
    )
    model = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("model")
    )

    def __str__(self):
        return f"{self.user.email} :: {self.id}"
