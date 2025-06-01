from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from apps.store.models import Store, MenuItem
from apps.core.models import BaseModel

User = get_user_model()

class Voucher(models.Model):
    VOUCHER_TYPE_CHOICES = [
        ('coupon', 'Coupon'),
        ('percentage', 'Percentage'),
        ('flat', 'Flat'),
        ('bxgy', 'Buy X Get Y'),
        ('bogo', 'Buy One Get One'),
        ('spend_x_save_y', 'Spend X Save Y'),
    ]

    TARGET_TYPE_CHOICES = [
        ('platform', 'Platform'),
        ('store', 'Store'),
    ]

    RESPONSIBILITY_CHOICES = [
        ('platform', 'Platform'),
        ('store', 'Store'),
        ('shared', 'Shared'),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    voucher_type = models.CharField(max_length=20, choices=VOUCHER_TYPE_CHOICES)
    target_type = models.CharField(max_length=10, choices=TARGET_TYPE_CHOICES, verbose_name="Target Type", help_text="The voucher applies to the entire platform, across all stores or to a specific store.")
    responsible_party = models.CharField(max_length=10, choices=RESPONSIBILITY_CHOICES)
    
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    store = models.ForeignKey("store.Store", on_delete=models.CASCADE, null=True, blank=True)
    users = models.ManyToManyField(User, blank=True, related_name="vouchers")

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    is_active = models.BooleanField(default=True)
    usage_limit = models.IntegerField(default=1)
    usage_limit_per_user = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Maximum number of times a single user can use this voucher. Leave blank for unlimited."
    )
    total_used_count = models.PositiveIntegerField(default=0)

    def is_valid_for_user(self, user):
        if not self.is_active or self.usage_count >= self.usage_limit:
            return False
        if self.users.exists() and user not in self.users.all():
            return False
        return True

    def __str__(self):
        return f"{self.code} ({self.voucher_type})"
      
      
class VoucherUsage(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    usage_count = models.PositiveIntegerField(default=0)


class VoucherRedemption(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("voucher", "user") 
        
        
class LocalDeal(BaseModel):
  
    class DealType(models.TextChoices):
        SPECIAL_DISCOUNT = "special_discount", ("Special Discount")
        NORMAL_DISCOUNT = "normal_discount", ("Normal Discount")
    class OfferType(models.TextChoices):
        PERCENTAGE = "percentage", ("Percentage")
        FLAT = "flat", ("Flat")
        BOGO = "bogo", ("BOGO")
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    main_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Base price of the menu item")
    discount_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Total discount amount applied to the item")
    deal_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Final price user pays")
    offer_type = models.CharField(max_length=20, choices=OfferType.choices, default=OfferType.PERCENTAGE)
    deal_type = models.CharField(max_length=20, choices=DealType.choices, default=DealType.NORMAL_DISCOUNT, help_text="Type of the deal || special discount must be special then normal discount")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    purchase_limit = models.PositiveIntegerField(null=True, blank=True)
    times_purchased = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.menu_item.name} ({self.restaurant.name})"

    def is_expired(self):
        return timezone.now() > self.end_time

    def save(self, *args, **kwargs):
        try:
            # Safely get the base price from the related MenuItem
            base_price = Decimal(str(self.menu_item.base_price))
        except (AttributeError, InvalidOperation):
            base_price = Decimal('0.00')  # fallback if missing or invalid

        self.main_price = base_price

        # Calculate deal_price
        try:
            if self.offer_type == self.OfferType.PERCENTAGE:
                self.deal_price = base_price * (1 - Decimal(self.discount_amount) / 100)
            elif self.offer_type == self.OfferType.FLAT:
                self.deal_price = max(base_price - Decimal(self.discount_amount), Decimal('0.00'))
            elif self.offer_type == self.OfferType.BOGO:
                self.deal_price = base_price
            else:
                self.deal_price = base_price
        except (InvalidOperation, ZeroDivisionError):
            self.deal_price = base_price  # fallback

        super().save(*args, **kwargs)