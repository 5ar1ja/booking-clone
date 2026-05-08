from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class IsAdmin(permissions.BasePermission):
    '''Grants access only to staff and superusers.'''

    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(
            request.user
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsLandlord(permissions.BasePermission):
    '''Grants access only to authenticated users with the landlord role.'''

    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_landlord
        )


class IsRenter(permissions.BasePermission):
    '''Grants access only to authenticated users with the renter role.'''

    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_renter
        )
