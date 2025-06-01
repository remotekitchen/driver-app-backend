# Updated Models for Store and Location
from django.db import models
from django.conf import settings
from django.utils.timezone import localtime

class Store(models.Model):
    STORE_TYPE_CHOICES = (
        ('restaurant', 'Restaurant'),
        ('salons', 'Salons'),
        ('hotels', 'Hotels'),
        ('medicine', 'Medicine'),
    )
    ORDER_METHOD_CHOICES = (
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('local_deal', 'Local Deal'),
        ('dine_in', 'Dine In'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online Payment'),
        ('wallet', 'Wallet'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_stores",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=100)
    store_logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    store_banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    store_type = models.CharField(max_length=20, choices=STORE_TYPE_CHOICES, default='restaurant')
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    utensil_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_method = models.CharField(max_length=20, choices=ORDER_METHOD_CHOICES, default='delivery')
    payment_methods = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cash')
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    address = models.ForeignKey("Address", on_delete=models.CASCADE, related_name="stores", blank=True, null=True)
    latitude = models.CharField(max_length=20, blank=True, null=True)
    longitude = models.CharField(max_length=20, blank=True, null=True)
    is_temporarily_closed = models.BooleanField(default=False)
    operating_hours = models.ManyToManyField(
        "StoreOperatingHour",
        related_name="stores",
        blank=True,
        help_text="Define the operating hours for each day of the week."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At", blank=True, null=True)
    
    @property
    def is_store_open(self):
        if self.is_temporarily_closed:
            return False

        now = localtime()
        current_day = now.weekday()
        current_time = now.time()

        hours_today = self.operating_hours.filter(day_of_week=current_day).first()
        if not hours_today:
            return False

        return hours_today.open_time <= current_time <= hours_today.close_time
      
    

    def __str__(self):
        return f"{self.name} ({self.store_type})"


class Address(models.Model):
    city = models.CharField(max_length=100)
    street_name = models.CharField(max_length=100)
    street_number = models.CharField(max_length=20)
    zip_code = models.CharField(max_length=20)
    label = models.CharField(max_length=100, blank=True, null=True)
  
    def __str__(self):
        return f"{self.street_name} {self.street_number}, {self.city} - {self.zip_code}"



class StoreOperatingHour(models.Model):
    DAYS_OF_WEEK = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
        (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")
    ]
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    open_time = models.TimeField()
    close_time = models.TimeField()

    class Meta:
        ordering = ["day_of_week"]

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.open_time} to {self.close_time}"


class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True)
    store= models.ForeignKey("Store", on_delete=models.CASCADE, related_name="cuisines")

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    store = models.ForeignKey("Store", on_delete=models.CASCADE, related_name="categories")

    def __str__(self):
        return f"{self.name} ({self.store.name})"


class Menu(models.Model):
    name = models.CharField(max_length=100)
    store = models.ForeignKey("Store", on_delete=models.CASCADE, related_name="menus")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.store.name}"


class MenuItem(models.Model):
  
    STATUS_CHOICES = (
        ("in_stock", "In Stock"),
        ("sold_out", "Sold Out"),
        ("unavailable_today", "Unavailable Today"),
    )
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    cuisine = models.ForeignKey(Cuisine, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    status= models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_stock")
    
    def __str__(self):
        return f"{self.name} ({self.menu.store.name})"
      
class ModifierGroup(models.Model):
    REQUIREMENT_CHOICES = (
        ("optional", "Optional"),
        ("required", "Required"),
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="modifier_groups")
    modifiers = models.ManyToManyField("Modifier", related_name="modifier_groups")
    name = models.CharField(max_length=100)
    requirement = models.CharField(max_length=20, choices=REQUIREMENT_CHOICES, default="optional")

    def __str__(self):
        return f"{self.name} - {self.menu_item.name}"
      
class Modifier(models.Model):
    AVAILABILITY_CHOICES = (
        ("available", "Available"),
        ("unavailable", "Unavailable"),
        ("unavailable_for_today", "Unavailable for Today"),
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    availability = models.CharField(max_length=50, choices=AVAILABILITY_CHOICES, default="available")
    
    def __str__(self):
        return f"{self.name} - {self.price} ({self.availability})"
