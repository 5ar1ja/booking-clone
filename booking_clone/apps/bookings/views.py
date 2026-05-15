import logging
from typing import Any

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from django.db.models import QuerySet
from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from apps.core.pagination import StandardResultsSetPagination
from apps.notifications.models import Notification
from apps.notifications.utils import notify_after_commit
from .filters import BookingFilter
from .models import Booking
from .permissions import IsApartmentOwnerForBooking, IsBookingTenant, IsRenterOrReadOnly
from .serializers import BookingReadSerializer, BookingWriteSerializer, BookingStatusSerializer

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


def build_booking_notification_metadata(
    booking: Booking,
    *,
    actor_email: str,
    previous_status: str | None = None,
) -> dict[str, Any]:
    return {
        'booking_id': booking.id,
        'apartment_id': booking.apartment_id,
        'apartment_title': booking.apartment.title,
        'tenant_email': booking.tenant.email,
        'landlord_email': booking.apartment.owner.email,
        'status': booking.status,
        'previous_status': previous_status,
        'check_in': booking.check_in.isoformat(),
        'check_out': booking.check_out.isoformat(),
        'actor_email': actor_email,
    }


@extend_schema_view(
    list=extend_schema(
        summary="List bookings",
        description="Retrieve a list of bookings. Landlords see bookings for their apartments, tenants see their own bookings",
        responses={200: BookingReadSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create a new booking",
        description="Create a new booking for an apartment. Permissions: Authenticated Renters",
        request=BookingWriteSerializer,
        responses={201: BookingReadSerializer, 400: OpenApiTypes.OBJECT},
    ),
    retrieve=extend_schema(
        summary="Retrieve booking details",
        description="Get detailed information about a specific booking",
        responses={200: BookingReadSerializer, 404: OpenApiTypes.OBJECT},
    ),
    update=extend_schema(
        summary="Update a booking (Disabled)",
        description="Full updates are not allowed. Use /cancel/ or /update-status/",
        responses={405: OpenApiTypes.OBJECT},
    ),
    partial_update=extend_schema(
        summary="Partially update a booking (Disabled)",
        description="Partial updates are not allowed. Use /cancel/ or /update-status/",
        responses={405: OpenApiTypes.OBJECT},
    ),
    destroy=extend_schema(
        summary="Delete a booking (Disabled)",
        description="Deletions are not allowed. Use the /cancel/ action instead",
        responses={405: OpenApiTypes.OBJECT},
    ),
    cancel=extend_schema(
        summary="Cancel a booking",
        description="Allows a tenant to cancel their own booking",
        request=None,
        responses={200: BookingReadSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
    ),
    update_status=extend_schema(
        summary="Update booking status",
        description="Allows an apartment owner to accept or reject a booking",
        request=BookingStatusSerializer,
        responses={200: BookingReadSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
    ),
)
class BookingViewSet(viewsets.ViewSet):
    '''
    ViewSet for bookings.
    Uses BookingReadSerializer for GET
    Uses BookingWriteSerializer for POST
    '''
    permission_classes = [IsAuthenticated, IsRenterOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingFilter
    pagination_class = StandardResultsSetPagination

    def get_permissions(self) -> list[BasePermission]:
        if self.action == ACTION_CANCEL:
            return [IsAuthenticated(), IsBookingTenant()]
        if self.action == ACTION_UPDATE_STATUS:
            return [IsAuthenticated(), IsApartmentOwnerForBooking()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self) -> QuerySet[Booking]:
        user = self.request.user
        if user.is_landlord:
            return Booking.objects.filter(
                apartment__owner=user
            ).select_related('tenant', 'apartment')
        return Booking.objects.filter(
            tenant=user
        ).select_related('tenant', 'apartment')

    def get_object(self, pk: Any = None) -> Booking:
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request: DRFRequest) -> Response:
        queryset = self.get_queryset()
        backend = DjangoFilterBackend()
        queryset = backend.filter_queryset(request, queryset, self)
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = BookingReadSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = BookingReadSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request: DRFRequest) -> Response:
        serializer = BookingWriteSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                booking = serializer.save(tenant=request.user)
                logger.info(
                    'Booking created: tenant=%s, apartment_id=%s',
                    request.user.email,
                    booking.apartment_id,
                )

                notify_after_commit(
                    user=booking.apartment.owner,
                    event_type=Notification.EventType.BOOKING_CREATED,
                    message=(
                        f'New booking request from {request.user.email} '
                        f'for "{booking.apartment.title}".'
                    ),
                    booking=booking,
                    metadata=build_booking_notification_metadata(
                        booking,
                        actor_email=request.user.email,
                    ),
                )

            read_serializer = BookingReadSerializer(booking)
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request: DRFRequest, pk: Any = None) -> Response:
        booking = self.get_object(pk)
        serializer = BookingReadSerializer(booking)
        return Response(serializer.data)

    def update(self, request: DRFRequest, pk: Any = None) -> Response:
        return Response(
            {'detail': DETAIL_FULL_UPDATE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request: DRFRequest, pk: Any = None) -> Response:
        return Response(
            {'detail': DETAIL_PARTIAL_UPDATE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request: DRFRequest, pk: Any = None) -> Response:
        return Response(
            {'detail': DETAIL_DELETE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(methods=['patch'], detail=True, url_path='cancel')
    def cancel(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Renter cancels their own booking.'''
        booking = self.get_object(pk)
        if booking.status == Booking.Status.CANCELLED:
            return Response(
                {'detail': DETAIL_ALREADY_CANCELLED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        previous_status = booking.status
        with transaction.atomic():
            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=['status'])
            logger.info('Booking %s cancelled by %s', booking.id, request.user.email)

            notify_after_commit(
                user=booking.apartment.owner,
                event_type=Notification.EventType.BOOKING_CANCELLED,
                message=f'Booking for "{booking.apartment.title}" has been cancelled by the tenant.',
                booking=booking,
                metadata=build_booking_notification_metadata(
                    booking,
                    actor_email=request.user.email,
                    previous_status=previous_status,
                ),
            )

        return Response(BookingReadSerializer(booking).data)

    @action(methods=['patch'], detail=True, url_path='update-status')
    def update_status(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Landlord accepts or rejects the booking.'''
        booking = self.get_object(pk)
        serializer = BookingStatusSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        previous_status = booking.status
        new_status = serializer.validated_data.get('status')
        with transaction.atomic():
            serializer.save()

            notify_after_commit(
                user=booking.tenant,
                event_type=Notification.EventType.BOOKING_STATUS_CHANGED,
                message=f'Your booking for "{booking.apartment.title}" is now {new_status.upper()}.',
                booking=booking,
                metadata=build_booking_notification_metadata(
                    booking,
                    actor_email=request.user.email,
                    previous_status=previous_status,
                ),
            )

        # trigger delayed email task if status is confirmed
        if new_status == Booking.Status.CONFIRMED:
            from .tasks import send_booking_confirmation_email
            transaction.on_commit(lambda: send_booking_confirmation_email.delay(booking.id))
            logger.info('Booking #%s confirmed, email task queued.', booking.id)

        logger.info(
            'Booking #%s status → %s by landlord=%s',
            booking.id,
            new_status,
            request.user.email,
        )
        return Response(BookingReadSerializer(booking).data)
