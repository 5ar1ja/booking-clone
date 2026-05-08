import logging
from typing import Any

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.db.models import QuerySet

from .models import Booking
from .permissions import IsApartmentOwnerForBooking, IsBookingTenant, IsRenterOrReadOnly
from .serializers import BookingSerializer, BookingStatusSerializer

logger = logging.getLogger('apps.bookings')

DETAIL_FULL_UPDATE_NOT_ALLOWED = (
    'Full update not allowed. Use /cancel/ or /update-status/.'
)
DETAIL_PARTIAL_UPDATE_NOT_ALLOWED = (
    'Partial update not allowed. Use /cancel/ or /update-status/ instead.'
)
DETAIL_DELETE_NOT_ALLOWED = 'Deletion not allowed. Use the /cancel/ action instead.'
DETAIL_ALREADY_CANCELLED = 'Booking is already cancelled.'

ACTION_CANCEL = 'cancel'
ACTION_UPDATE_STATUS = 'update_status'


class BookingViewSet(viewsets.ModelViewSet):
    '''Manages booking lifecycle: creation, status updates, and cancellation.'''

    serializer_class = BookingSerializer
    permission_classes = [IsRenterOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self) -> list[BasePermission]:
        if self.action == ACTION_CANCEL:
            return [IsAuthenticated(), IsBookingTenant()]
        if self.action == ACTION_UPDATE_STATUS:
            return [IsAuthenticated(), IsApartmentOwnerForBooking()]
        return super().get_permissions()

    def get_queryset(self) -> QuerySet[Booking]:
        user = self.request.user
        if user.is_landlord:
            return Booking.objects.filter(
                apartment__owner=user
            ).select_related('tenant', 'apartment')
        return Booking.objects.filter(
            tenant=user
        ).select_related('tenant', 'apartment')

    def perform_create(self, serializer: BaseSerializer) -> None:
        serializer.save(tenant=self.request.user)
        logger.info(
            'Booking created: tenant=%s, apartment_id=%s',
            self.request.user.email,
            serializer.instance.apartment_id,
        )

    def update(self, request: DRFRequest, *args: Any, **kwargs: Any) -> Response:
        return Response(
            {'detail': DETAIL_FULL_UPDATE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request: DRFRequest, *args: Any, **kwargs: Any) -> Response:
        return Response(
            {'detail': DETAIL_PARTIAL_UPDATE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request: DRFRequest, *args: Any, **kwargs: Any) -> Response:
        return Response(
            {'detail': DETAIL_DELETE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(methods=['patch'], detail=True, url_path='cancel')
    def cancel(self, request: DRFRequest, pk: int | None = None) -> Response:
        '''Renter cancels their own booking.'''
        booking = self.get_object()
        if booking.status == Booking.Status.CANCELLED:
            return Response(
                {'detail': DETAIL_ALREADY_CANCELLED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=['status'])
        logger.info('Booking %s cancelled by %s', booking.id, request.user.email)
        return Response(BookingSerializer(booking).data)

    @action(methods=['patch'], detail=True, url_path='update-status')
    def update_status(self, request: DRFRequest, pk: int | None = None) -> Response:
        '''Landlord accepts or rejects the booking.'''
        booking = self.get_object()
        serializer = BookingStatusSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(
            'Booking #%s status → %s by landlord=%s',
            booking.id,
            serializer.validated_data.get('status'),
            request.user.email,
        )
        return Response(BookingSerializer(booking).data)
