# Django modules
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

# Project modules
from apps.users.models import CustomUser


@register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'email', 'first_name', 'last_name',
        'is_landlord', 'is_renter', 'is_active', 'is_staff', 'is_superuser',
    )
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_landlord', 'is_renter', 'is_active', 'is_staff')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Roles'), {'fields': ('is_landlord', 'is_renter')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'is_landlord', 'is_renter'),
        }),
    )
