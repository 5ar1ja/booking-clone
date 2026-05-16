# Python modules
from typing import Any

# Third-party modules
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request

# Project modules
from apps.core.permissions import IsOwnerOrReadOnly as IsReviewAuthorOrReadOnlyBase


class IsReviewAuthorOrReadOnly(IsReviewAuthorOrReadOnlyBase):
    '''Read access for everyone; write/delete access only for the review author.'''

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
