from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request as DRFRequest

from .models import Booking
from .serializers import BookingSerializer, BookingStatusSerializer
from .permissions import IsRenterOrReadOnly, IsApartmentOwnerForBooking, IsBookingTenant


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsRenterOrReadOnly]          # ← now the default (cleaner)
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "cancel":
            return [IsAuthenticated(), IsBookingTenant()]
        if self.action == "update_status":
            return [IsAuthenticated(), IsApartmentOwnerForBooking()]
        # list, create, retrieve → handled by IsRenterOrReadOnly
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_landlord:
            return Booking.objects.filter(
                apartment__owner=user
            ).select_related("tenant", "apartment")
        return Booking.objects.filter(
            tenant=user
        ).select_related("tenant", "apartment")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)

    # ───── Block unsafe default actions ─────
    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Full update not allowed. Use /cancel/ or /update-status/."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Partial update not allowed. Use /cancel/ or /update-status/ instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Deletion not allowed. Use the /cancel/ action instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    # ───── Custom actions ─────
    @action(methods=["patch"], detail=True, url_path="cancel")
    def cancel(self, request: DRFRequest, pk=None) -> Response:
        """Renter cancels their own booking."""
        booking = self.get_object()
        if booking.status == Booking.Status.CANCELLED:
            return Response(
                {"detail": "Booking is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
        return Response(BookingSerializer(booking).data)

    @action(methods=["patch"], detail=True, url_path="update-status")
    def update_status(self, request: DRFRequest, pk=None) -> Response:
        """Landlord accepts or rejects the booking."""
        booking = self.get_object()
        serializer = BookingStatusSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(BookingSerializer(booking).data)