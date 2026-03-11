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
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        user = self.request.user

        if user.is_landlord:
            return Booking.objects.filter(
                apartment__owner=user
            ).select_related("tenant", "apartment")

        return Booking.objects.filter(
            tenant=user
        ).select_related("tenant", "apartment")

    def get_permissions(self):
        if self.action == "create":
            return [IsRenterOrReadOnly()]
        if self.action in ["cancel"]:
            return [IsAuthenticated(), IsBookingTenant()]
        if self.action == "update_status":
            return [IsAuthenticated(), IsApartmentOwnerForBooking()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)

    @action(methods=["patch"], detail=True, url_path="cancel")
    def cancel(self, request: DRFRequest, pk=None) -> Response:
        """Арендатор отменяет своё бронирование."""
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
        """Владелец квартиры подтверждает или отменяет бронирование."""
        booking = self.get_object()
        self.check_object_permissions(request, booking)

        serializer = BookingStatusSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(BookingSerializer(booking).data)