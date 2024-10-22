from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Profile, User, Vehicle


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
        [_("Important dates"), {"fields": ["last_login", "date_joined"]}],
    ]
    date_hierarchy = "date_joined"
    ordering = ["-id"]
    search_fields = ("first_name", "last_name", "email")


admin.site.register(Profile)
admin.site.register(Vehicle)
