from typing import Any

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request


class IsReviewAuthorOrReadOnly(BasePermission):
    '''Read access for everyone; write/delete access only for the review author.'''

    def has_permission(self, request: Request, view: Any) -> bool:
        '''Allow read access for everyone; write/delete access only for authenticated users.'''

        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        '''Allow object-level write/delete access only for the review author. Read access for everyone.'''

        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
