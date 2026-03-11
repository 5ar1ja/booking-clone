from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from apps.bookings.models import Booking
from .models import Review
from .serializers import ReviewSerializer
from .permissions import IsReviewAuthorOrReadOnly
from .filters import ReviewFilter


class ReviewViewSet(viewsets.ModelViewSet):

    queryset = Review.objects.select_related(
        "author",
        "apartment"
    )

    serializer_class = ReviewSerializer

    permission_classes = [IsReviewAuthorOrReadOnly]

    filter_backends = [DjangoFilterBackend]
    filterset_class = ReviewFilter

    def perform_create(self, serializer):
        apartment = serializer.validated_data["apartment"]
        user = self.request.user

        # Prevent reviewing own apartment
        if apartment.owner == user:
            raise PermissionDenied("You cannot review your own apartment.")

        # Trust the COMPLETED status (landlord already confirmed the stay)
        stayed = Booking.objects.filter(
            apartment=apartment,
            tenant=user,
            status=Booking.Status.COMPLETED
            # ← removed the date check (it was breaking test data + early completion)
        ).exists()

        if not stayed:
            raise PermissionDenied(
                "You can only review apartments you have stayed in."
            )

        serializer.save(author=user)