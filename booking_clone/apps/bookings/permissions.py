from typing import Any

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request


class IsRenterOrReadOnly(BasePermission):
    '''Read access for all authenticated users; write access only for renters.'''

    def has_permission(self, request: Request, view: Any) -> bool:
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_renter


class IsBookingTenant(BasePermission):
    '''Object-level access only for the tenant who created the booking.'''

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return obj.tenant == request.user


class IsApartmentOwnerForBooking(BasePermission):
    '''Object-level access only for the owner of the booked apartment.'''

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return obj.apartment.owner == request.user
