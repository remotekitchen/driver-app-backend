from django.contrib import admin

from apps.store.models import Store, Address, StoreOperatingHour

# Register your models here.


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'store_type', 'average_rating')
    search_fields = ('name', 'store_type', 'address__city')
    list_filter = ('store_type', 'order_method', 'payment_methods')
    ordering = ('-average_rating',)
    readonly_fields = ('average_rating',)
      
@admin.register(StoreOperatingHour)
class StoreOperatingHourAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'open_time', 'close_time')
    search_fields = ('store__name', 'day_of_week')
    list_filter = ('day_of_week',)

    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('location__store')
      
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('city', 'street_name', 'street_number', 'zip_code')
    search_fields = ('city', 'street_name', 'street_number', 'zip_code')
    ordering = ('city', 'street_name')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related()
