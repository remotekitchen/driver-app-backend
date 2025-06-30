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
        ARRIVED = "arrived", _("ARRIVED")
        DELIVERY_SUCCESS = "delivery_success", _("DELIVERY_SUCCESS")
        DELIVERY_FAILED = "delivery_failed", _("DELIVERY_FAILED")
        DRIVER_REJECTED = "driver_rejected", _("DRIVER_REJECTED")
        CANCELED = "canceled", _("CANCELED")

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
        Address,
        on_delete=models.CASCADE,
        verbose_name=_("pickup address"),
        related_name="pickup_address",
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
        Address, on_delete=models.CASCADE, verbose_name=_("pickup address")
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
    est_delivery_completed_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("estimated delivery completed time")
    )
    actual_delivery_completed_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("actual delivery completed time")
    )
    rider_accepted_time = models.DateTimeField(
        verbose_name=_("Rider Accepted Time"), blank=True, null=True
    )
    rider_pickup_time = models.DateTimeField(
        verbose_name=_("Rider Pickup Time"), blank=True, null=True
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
    ride_duration = models.FloatField(default=0)
    distance = models.FloatField(default=0)
    fees = models.FloatField(default=0)
    tips = models.FloatField(default=0)
    discount = models.FloatField(default=0)
    cash_collected = models.FloatField(default=0)
    amount = models.FloatField(default=0)
    driver_earning = models.FloatField(default=0)

    payment_type = models.CharField(
        max_length=50,
        default=PAYMENT_METHOD_TYPE.CARD,
        choices=PAYMENT_METHOD_TYPE.choices,
        verbose_name=_("payment type"),
    )
    use_google = models.BooleanField(default=True)

    cancel_reason = models.CharField(max_length=255, blank=True, null=True)

    items = models.JSONField(default=dict)
    
    assigned = models.BooleanField(default=False)
    
    delivered_product_image = models.ImageField(upload_to="delivery_product_images", blank=True, null=True)
    customer_info = models.JSONField(default=dict)


   # Add Opt-In Fields for Guarantee
    on_time_guarantee_opted_in = models.BooleanField(default=False)
    on_time_guarantee_fee = models.FloatField(default=0)
    # def calculate_driver_earning(self):
    #     """
    #     Automatically calculate the driver's earnings when a Delivery instance is created/updated.
    #     """

    #     # Define the base values (these can be customized)
    #     base_fee = 7  # Tk
    #     peak_hour_bonus = 0  # Default to 0, can be updated dynamically
    #     incentives = 0  # Default to 0, can be updated dynamically
    #     additional_bonuses = 0  # Default to 0, can be updated dynamically
    #     print(self.fees, 'fees----------->')

    #     # Calculate driver earnings
    #     self.driver_earning = base_fee + self.fees + peak_hour_bonus + incentives + additional_bonuses

    # def save(self, *args, **kwargs):
    #     """
    #     Override the save method to calculate driver earnings automatically before saving.
    #     """
    #     self.calculate_driver_earning()  # Call earning calculation before saving
    #     super().save(*args, **kwargs)  # Proceed with saving the instance

   

    def update_final_earning(self):
        from apps.billing.utils.earning_calculation import calculate_total_driver_earning  # imported only when called
        result = calculate_total_driver_earning(self)

        # Update the driver_earning field with the calculated final earning
        self.driver_earning = result["final_earning"]

        # Optionally, update other fields if necessary (e.g., penalty percentage)
        self.penalty_percentage = result["penalty_percentage"]  # Assuming you want to save the penalty percentage as well
        
        # Save the updated instance to persist the changes
        self.save()

        return result  # Optional: contains final earning and penalty

    def __str__(self):
        return f"{self.id} :: {self.client_id}"

    class Meta:
        ordering = ["-id"]


class DeliveryFee(BaseModel):
    distance = models.PositiveIntegerField(default=0)
    per_km = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.id} {self.distance}"



class DeliveryIssue(BaseModel):
    CUSTOMER_ISSUE_TYPE = (
        ("missing_item", "Missing Item"),
        ("wrong_item", "Wrong Item"),
        ("damaged_item", "Damaged Item"),
        ("late_delivery", "Late Delivery"),
        ("other", "Other"),
    )
    
    DRIVER_ISSUE_TYPE = (
        ("vehicle_issue", "Vehicle Issue"),
        ("traffic_delay", "Traffic Delay"),
        ("route_issue", "Route Issue"),
        ("other", "Other"),
    )
    REPORTED_BY_CHOICES = (
        ("customer", "Customer"),
        ("driver", "Driver"),
        ("store", "Store"),
    )
    
    STATUS_CHOICES = (
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    )
    reported_by = models.CharField(
        max_length=20, choices=REPORTED_BY_CHOICES, default="customer"
    )
    proof_image = models.ImageField(upload_to="delivery_issue_proofs", blank=True, null=True)
    issue_type = models.CharField(max_length=50, default="other")
    description = models.TextField(blank=True, null=True)
    delivery = models.ForeignKey(
        Delivery, on_delete=models.CASCADE, related_name="issues", verbose_name="Delivery"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open", verbose_name="Status"
    )
    order_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Order ID"
        
        
    )
    
    
    
    
    def __str__(self):
        return f"Issue {self.id} for Delivery {self.delivery.id} - {self.get_issue_type_display()}"
      
    @classmethod
    def get_issue_type_choices(cls, reported_by):
        if reported_by == "customer":
            return cls.CUSTOMER_ISSUE_TYPE
        elif reported_by == "driver":
            return cls.DRIVER_ISSUE_TYPE
        return [("other", "Other")]
    class Meta:
        ordering = ["-id"]
        verbose_name = "Delivery Issue"
        verbose_name_plural = "Delivery Issues"
    



class DeliveryEarningConfig(models.Model):
    estimated_time_per_km = models.FloatField(default=3.5)
    base_distance_km = models.FloatField(default=10)
    base_earning = models.FloatField(default=25)
    extra_per_km = models.FloatField(default=3)

    grace_period_minutes = models.IntegerField(default=5)
    penalty_6_10 = models.FloatField(default=50)
    penalty_11_15 = models.FloatField(default=50)
    penalty_above_15 = models.FloatField(default=70)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Delivery Earning & Penalty Config"
