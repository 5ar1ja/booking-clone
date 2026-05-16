from functools import wraps
from rest_framework.exceptions import PermissionDenied

def require_role(role_attr: str):
    """
    Decorator to check if the authenticated user has a specific role attribute.
    Usage:
    @require_role('is_landlord')
    def my_view(request, ...):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required.")
            if not getattr(request.user, role_attr, False):
                raise PermissionDenied(f"User must have {role_attr} role.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
