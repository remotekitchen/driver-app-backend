from django.contrib import admin

from apps.billing.models import Delivery, DeliveryFee

admin.site.register(Delivery)
admin.site.register(DeliveryFee)
