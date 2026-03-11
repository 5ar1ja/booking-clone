from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff or request.user.is_superuser)

class IsLandlord(permissions.BasePermission):
    def has_permission(self, request, view):
        # Rule: User must be logged in AND have the is_landlord flag
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_landlord
        )

class IsRenter(permissions.BasePermission):
    def has_permission(self, request, view):
        # Rule: User must be logged in AND have the is_renter flag
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_renter
        )