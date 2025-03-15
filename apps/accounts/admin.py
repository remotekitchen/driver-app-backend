from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Profile, User, Vehicle, DriverSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "is_staff"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    fieldsets = [
        [None, {"fields": ["password"]}],
        [_("Personal info"), {"fields": ["first_name", "last_name", "email"]}],
        [
            _("Permissions"),
            {
                "fields": [
                    "is_email_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "role",
                ],
            },
        ],
        [
            _("Important dates"),
            {"fields": ["last_login", "date_joined", "latitude", "longitude"]},
        ],
    ]
    date_hierarchy = "date_joined"
    ordering = ["-id"]
    search_fields = ("first_name", "last_name", "email")
    

@admin.register(DriverSession)
class DriverSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active"]
    search_fields = ("user__first_name", "user__last_name", "user__email")
    list_filter = ["is_active"]
    actions = ["make_inactive"]
    
# @admin.register(DriverWorkHistory)
# class DriverWorkHistoryAdmin(admin.ModelAdmin):
#     list_display = ["user", "total_deliveries", "total_earnings", "offline_count", "on_time_deliveries"]
#     search_fields = ("user__first_name", "user__last_name", "user__email")
#     ordering = ["-total_deliveries"]
    
# @admin.register(DriverSessionHistory)
# class DriverSessionHistoryAdmin(admin.ModelAdmin):
#     list_display = ["user", "session", "date", "weekday"]
#     search_fields = ("user__first_name", "user__last_name", "user__email")
#     ordering = ["-date"]

admin.site.register(Profile)
admin.site.register(Vehicle)
