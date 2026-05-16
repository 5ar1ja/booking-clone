# Python modules
from typing import Any

# Third-party modules
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

# Project modules
from apps.core.permissions import IsLandlord
from apps.core.permissions import IsOwnerOrReadOnly as IsApartmentOwner


class IsLandlordOrReadOnly(BasePermission):
    '''Read access for everyone; write access only for authenticated landlords.'''

    def has_permission(self, request: Request, view: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return IsLandlord().has_permission(request, view)
