from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsRenterOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_renter
    
class IsBookingTenant(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.tenant == request.user
    
class IsApartmentOwnerForBooking(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.apartment.owner == request.user