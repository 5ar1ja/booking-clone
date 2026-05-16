# Django modules
from django.shortcuts import get_object_or_404


class SerializerMixin:
    """Adds serializer helpers for plain DRF ViewSets."""

    serializer_class = None

    def get_serializer_class(self):
        if self.serializer_class is None:
            raise AssertionError(
                f'{self.__class__.__name__} must define serializer_class '
                'or override get_serializer_class().'
            )
        return self.serializer_class

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
        }

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)


class ActionSerializerMixin(SerializerMixin):
    """
    Mixin to allow specifying different serializers for different actions.
    Example:
    serializer_action_classes = {
        'list': MyListSerializer,
        'retrieve': MyRetrieveSerializer,
        'create': MyCreateSerializer,
    }
    """

    serializer_action_classes = {}

    def get_serializer_class(self):
        if self.action in self.serializer_action_classes:
            return self.serializer_action_classes[self.action]
        return super().get_serializer_class()


class ObjectLookupMixin:
    """Provides a reusable object lookup flow for plain ViewSets."""

    lookup_field = 'pk'
    lookup_url_kwarg = None

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, **{self.lookup_field: lookup_value})
        self.check_object_permissions(self.request, obj)
        return obj


class PaginationMixin:
    """Adds pagination helpers for ViewSets without GenericAPIView."""

    pagination_class = None
    paginator = None

    def paginate_queryset(self, queryset):
        if self.pagination_class is None:
            return None
        if self.paginator is None:
            self.paginator = self.pagination_class()
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        if self.paginator is None:
            raise AssertionError('Paginator is not initialized.')
        return self.paginator.get_paginated_response(data)
