from django.contrib import admin

from apps.billing.models import Delivery, DeliveryFee,DeliveryEarningConfig


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "uid",
        "client_id",
        "pickup_address",
        "status",
        "driver_earning",
        "platform",
    )
    search_fields = ("client_id", 'driver__email')


admin.site.register(DeliveryFee)


@admin.register(DeliveryEarningConfig)
class DeliveryEarningConfigAdmin(admin.ModelAdmin):
    list_display = ('base_distance_km', 'base_earning', 'extra_per_km', 'updated_at')