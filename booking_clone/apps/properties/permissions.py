from typing import Any

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request


class IsLandlordOrReadOnly(BasePermission):
    '''Read access for everyone; write access only for authenticated landlords.'''

    def has_permission(self, request: Request, view: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_landlord)


class IsApartmentOwner(BasePermission):
    '''Object-level write access only for the apartment owner.'''

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(obj.owner == request.user)
