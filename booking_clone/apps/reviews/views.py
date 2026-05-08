import logging

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import BaseSerializer

from apps.bookings.models import Booking
from .filters import ReviewFilter
from .models import Review
from .permissions import IsReviewAuthorOrReadOnly
from .serializers import ReviewSerializer

logger = logging.getLogger('apps.reviews')

ERR_OWN_APARTMENT = 'You cannot review your own apartment.'
ERR_NOT_STAYED = 'You can only review apartments you have stayed in.'


class ReviewViewSet(viewsets.ModelViewSet):
    '''Manages apartment reviews; only renters with a completed stay can submit.'''

    queryset = Review.objects.select_related('author', 'apartment')
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReviewFilter

    def perform_create(self, serializer: BaseSerializer) -> None:
        apartment = serializer.validated_data['apartment']
        user = self.request.user

        if apartment.owner == user:
            raise PermissionDenied(ERR_OWN_APARTMENT)

        # Trust the COMPLETED status (landlord already confirmed the stay)
        stayed = Booking.objects.filter(
            apartment=apartment,
            tenant=user,
            status=Booking.Status.COMPLETED,
        ).exists()

        if not stayed:
            raise PermissionDenied(ERR_NOT_STAYED)

        serializer.save(author=user)
        logger.info(
            'Review created: author=%s, apartment_id=%s, rating=%s',
            user.email,
            apartment.id,
            serializer.validated_data.get('rating'),
        )
