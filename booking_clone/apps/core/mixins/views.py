from rest_framework import viewsets

class ActionSerializerMixin:
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
