from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from accounts.models import Company, RestaurantUser, User, UserAddress, Otp


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name',
                    'last_name', 'company', 'role', 'is_staff']
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
        [None, {'fields': ['password']}],
        [_('Personal info'), {'fields': ['first_name', 'last_name', 'email']}],
        [_('Permissions'), {
            'fields': ['is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'],
        }],
        [_('Company info'), {
            'fields': ['company', 'role'],
        }],
        [_('Important dates'), {'fields': ['last_login', 'date_joined']}],
    ]
    date_hierarchy = 'date_joined'
    ordering = ['-id']
    search_fields = ("first_name", "last_name", "email")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner']

    @display(description='Owner')
    def owner(self, obj: Company):
        return ', '.join(list(obj.user_set.values_list('email', flat=True)))


@admin.register(RestaurantUser)
class RestaurantUserAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'user','rewards_category','reward_points','points_spent','next_level','remain_point']

    @display(description='Restaurant')
    def restaurant(self, obj: RestaurantUser):
        return obj.Restaurant.name

    @display(description='User')
    def user(self, obj: RestaurantUser):
        return obj.user.email


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street_number', 'street_name', 'city', 'country']
    search_fields = ['user__username']


@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    list_display = ['otp', 'phone', 'is_used']
    search_fields = ['phone']