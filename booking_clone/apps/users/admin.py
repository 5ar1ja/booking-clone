from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin
from apps.users.models import CustomUser

@register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin panel for User"""

    list_display = (
        "email",
        "first_name",
        "last_name",
        "avatar",
        "is_landlord",
        "is_renter",
        "is_active",
        "is_staff",
        "is_superuser"
    )

    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_landlord", "is_renter", "is_active", "is_staff")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "avatar")}),
        ("Roles", {"fields": ("is_landlord", "is_renter")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password", "first_name", "last_name", "is_landlord", "is_renter"),
        }),
    )