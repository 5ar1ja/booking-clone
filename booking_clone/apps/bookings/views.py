# Python modules
import logging
from typing import Any

# Django modules
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

# Third-party modules
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

# Project modules
from apps.core.mixins.views import ActionSerializerMixin, ObjectLookupMixin, PaginationMixin
from apps.core.pagination import StandardResultsSetPagination
from apps.notifications.models import Notification
from apps.notifications.utils import notify_after_commit
from .models import Booking
from .permissions import IsApartmentOwnerForBooking, IsBookingTenant, IsRenterOrReadOnly
from .serializers import BookingReadSerializer, BookingWriteSerializer, BookingStatusSerializer


logger = logging.getLogger('apps.bookings')

DETAIL_FULL_UPDATE_NOT_ALLOWED = (
    _('Full update not allowed. Use /cancel/ or /update-status/.')
)
DETAIL_PARTIAL_UPDATE_NOT_ALLOWED = (
    _('Partial update not allowed. Use /cancel/ or /update-status/ instead.')
)
DETAIL_DELETE_NOT_ALLOWED = _('Deletion not allowed. Use the /cancel/ action instead.')
DETAIL_ALREADY_CANCELLED = _('Booking is already cancelled.')

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
        description="Retrieve a list of bookings. Landlords see bookings for their apartments, tenants see their own bookings.",
        responses={200: BookingReadSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create a new booking",
        description="Create a new booking for an apartment. Permissions: Authenticated Renters.",
        request=BookingWriteSerializer,
        responses={201: BookingReadSerializer, 400: OpenApiTypes.OBJECT},
    ),
    retrieve=extend_schema(
        summary="Retrieve booking details",
        description="Get detailed information about a specific booking.",
        responses={200: BookingReadSerializer, 404: OpenApiTypes.OBJECT},
    ),
    update=extend_schema(
        summary="Update a booking (Disabled)",
        description="Full updates are not allowed. Use /cancel/ or /update-status/.",
        responses={405: OpenApiTypes.OBJECT},
    ),
    partial_update=extend_schema(
        summary="Partially update a booking (Disabled)",
        description="Partial updates are not allowed. Use /cancel/ or /update-status/.",
        responses={405: OpenApiTypes.OBJECT},
    ),
    destroy=extend_schema(
        summary="Delete a booking (Disabled)",
        description="Deletions are not allowed. Use the /cancel/ action instead.",
        responses={405: OpenApiTypes.OBJECT},
    ),
    cancel=extend_schema(
        summary="Cancel a booking",
        description="Allows a tenant to cancel their own booking.",
        request=None,
        responses={200: BookingReadSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
    ),
    update_status=extend_schema(
        summary="Update booking status",
        description="Allows an apartment owner to accept or reject a booking.",
        request=BookingStatusSerializer,
        responses={200: BookingReadSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
    ),
)
class BookingViewSet(
    ActionSerializerMixin,
    ObjectLookupMixin,
    PaginationMixin,
    viewsets.ViewSet,
):
    '''
    ViewSet for bookings.
    Uses BookingReadSerializer for GET
    Uses BookingWriteSerializer for POST
    '''
    permission_classes = [IsAuthenticated, IsRenterOrReadOnly]
    pagination_class = StandardResultsSetPagination
    serializer_class = BookingReadSerializer
    serializer_action_classes = {
        'create': BookingWriteSerializer,
        'update_status': BookingStatusSerializer,
    }

    def get_permissions(self) -> list[BasePermission]:
        '''Return the list of permissions based on the action.'''

        if self.action == ACTION_CANCEL:
            return [IsAuthenticated(), IsBookingTenant()]
        if self.action == ACTION_UPDATE_STATUS:
            return [IsAuthenticated(), IsApartmentOwnerForBooking()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self) -> QuerySet[Booking]:
        '''Return the queryset of bookings based on the user's role.'''

        user = self.request.user
        if user.is_landlord:
            return Booking.objects.filter(
                apartment__owner=user
            ).select_related('tenant', 'apartment')
        return Booking.objects.filter(
            tenant=user
        ).select_related('tenant', 'apartment')

    def get_object(self, pk: Any = None) -> Booking:
        '''Return the booking object for the given primary key.'''

        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request: DRFRequest) -> Response:
        '''List bookings for the authenticated user.'''

        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request: DRFRequest) -> Response:
        '''Create a new booking. Only renters can create bookings.'''

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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
                message=_(
                    'New booking request from %(email)s for "%(title)s".'
                ) % {
                    'email': request.user.email,
                    'title': booking.apartment.title,
                },
                booking=booking,
                metadata=build_booking_notification_metadata(
                    booking,
                    actor_email=request.user.email,
                ),
            )

        read_serializer = BookingReadSerializer(booking, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Retrieve a specific booking.'''

        booking = self.get_object(pk)
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    def update(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Full updates are not allowed. Use /cancel/ or /update-status/.'''

        return Response(
            {'detail': DETAIL_FULL_UPDATE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Partial updates are not allowed. Use /cancel/ or /update-status/ instead.'''

        return Response(
            {'detail': DETAIL_PARTIAL_UPDATE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Deletions are not allowed. Use the /cancel/ action instead.'''

        return Response(
            {'detail': DETAIL_DELETE_NOT_ALLOWED},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(methods=['patch'], detail=True, url_path='cancel')
    def cancel(self, request: DRFRequest, pk=None) -> Response:
        '''Renter cancels their own booking.'''

        booking = self.get_object(pk)
        if booking.status == Booking.Status.CANCELLED:
            logger.warning('Booking %s already cancelled, user=%s', booking.id, request.user.email)
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
                message=_('Booking for "%(title)s" has been cancelled by the tenant.') % {
                    'title': booking.apartment.title,
                },
                booking=booking,
                metadata=build_booking_notification_metadata(
                    booking,
                    actor_email=request.user.email,
                    previous_status=previous_status,
                ),
            )

        return Response(BookingReadSerializer(booking).data)

    @action(methods=['patch'], detail=True, url_path='update-status')
    def update_status(self, request: DRFRequest, pk=None) -> Response:
        '''Landlord accepts or rejects the booking.'''

        booking = self.get_object(pk)
        serializer = self.get_serializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        previous_status = booking.status
        new_status = serializer.validated_data.get('status')
        with transaction.atomic():
            serializer.save()

            notify_after_commit(
                user=booking.tenant,
                event_type=Notification.EventType.BOOKING_STATUS_CHANGED,
                message=_('Your booking for "%(title)s" is now %(status)s.') % {
                    'title': booking.apartment.title,
                    'status': new_status.upper(),
                },
                booking=booking,
                metadata=build_booking_notification_metadata(
                    booking,
                    actor_email=request.user.email,
                    previous_status=previous_status,
                ),
            )

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
        return Response(BookingReadSerializer(booking, context=self.get_serializer_context()).data)
