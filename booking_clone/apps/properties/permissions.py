from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsLandlordOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        # Anyone allowed to read
        if request.method in SAFE_METHODS:
            return True

        # Only landlords can create, landlord=True
        return request.user.is_authenticated and request.user.is_landlord


class IsApartmentOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        # Anyone can read
        if request.method in SAFE_METHODS:
            return True

        # Only owner can edit/delete
        return obj.owner == request.user