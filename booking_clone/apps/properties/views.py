# Python modules
import logging
from typing import Any

# Django modules
from django.core.cache import cache
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.views.decorators.cache import cache_page

# Third-party modules
from django_redis.exceptions import ConnectionInterrupted
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from redis.exceptions import ConnectionError as RedisConnectionError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, BasePermission
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

# Project modules
from apps.core.mixins.views import ActionSerializerMixin
from apps.bookings.models import Booking
from apps.core.pagination import StandardResultsSetPagination
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewReadSerializer
from .filters import ApartmentFilter
from .models import Apartment
from .permissions import IsApartmentOwner, IsLandlordOrReadOnly
from .serializers import ApartmentReadSerializer, ApartmentWriteSerializer


logger = logging.getLogger('apps.properties')


@extend_schema_view(
    list=extend_schema(
        summary="List all apartments",
        description="Retrieve a list of all apartments with optional filtering by city, rooms, price, and availability dates. Permissions: AllowAny (Read-only).",
        parameters=[
            OpenApiParameter(name='check_in', description='Format: YYYY-MM-DD. Filter by availability start date.', required=False, type=OpenApiTypes.DATE),
            OpenApiParameter(name='check_out', description='Format: YYYY-MM-DD. Filter by availability end date.', required=False, type=OpenApiTypes.DATE),
        ],
        responses={200: ApartmentReadSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create a new apartment",
        description="Add a new apartment listing to the platform. Permissions: Authenticated Landlords only.",
        request=ApartmentWriteSerializer,
        responses={201: ApartmentWriteSerializer, 400: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                'Apartment Creation Example',
                value={
                    'title': 'Luxury Penthouse',
                    'description': 'A beautiful penthouse in the city center.',
                    'address': '123 Main St',
                    'city_id': 1,
                    'price_per_night': '250.00',
                    'rooms': 3
                }
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Retrieve apartment details",
        description="Get detailed information about a specific apartment by its ID. Permissions: AllowAny (Read-only).",
        responses={200: ApartmentReadSerializer, 404: OpenApiTypes.OBJECT},
    ),
    update=extend_schema(
        summary="Update an apartment",
        description="Update all fields of an existing apartment. Permissions: Authenticated Landlord who owns the apartment.",
        request=ApartmentWriteSerializer,
        responses={200: ApartmentWriteSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    ),
    partial_update=extend_schema(
        summary="Partially update an apartment",
        description="Update specific fields of an existing apartment. Permissions: Authenticated Landlord who owns the apartment.",
        request=ApartmentWriteSerializer,
        responses={200: ApartmentWriteSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    ),
    destroy=extend_schema(
        summary="Delete an apartment",
        description="Remove an apartment listing from the platform. Permissions: Authenticated Landlord who owns the apartment.",
        responses={204: None, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    ),
    reviews=extend_schema(
        summary="List reviews for an apartment",
        description="Retrieve all reviews associated with a specific apartment. This endpoint is cached for 60 seconds. Permissions: AllowAny (Read-only).",
        responses={200: ReviewReadSerializer(many=True), 404: OpenApiTypes.OBJECT},
    ),
    availability=extend_schema(
        summary="List busy dates for an apartment",
        description="Returns apartment details along with a list of date ranges that are already booked or pending.",
        responses={200: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                'Availability Example',
                value={
                    'apartment': {
                        'id': 1,
                        'title': 'Luxury Penthouse',
                        'price_per_night': '250.00'
                    },
                    'busy_dates': [
                        {'check_in': '2024-06-01', 'check_out': '2024-06-10'},
                        {'check_in': '2024-07-15', 'check_out': '2024-07-20'}
                    ]
                }
            )
        ]
    ),
)
class ApartmentViewSet(ActionSerializerMixin, viewsets.ModelViewSet):
    '''
    ViewSet for apartments.
    Uses ApartmentReadSerializer for GET
    Uses ApartmentWriteSerializer for POST/PUT/PATCH
    '''
    
    permission_classes = [IsAuthenticatedOrReadOnly, IsLandlordOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ApartmentFilter
    pagination_class = StandardResultsSetPagination
    
    serializer_class = ApartmentReadSerializer
    serializer_action_classes = {
        'create': ApartmentWriteSerializer,
        'update': ApartmentWriteSerializer,
        'partial_update': ApartmentWriteSerializer,
    }

    def get_queryset(self) -> QuerySet[Apartment]:
        return Apartment.objects.select_related('city', 'city__country', 'owner').all()

    def get_object(self, pk: Any = None) -> Apartment:
        pk = pk if pk is not None else self.kwargs.get('pk')
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissions(self) -> list[BasePermission]:
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticatedOrReadOnly(), IsLandlordOrReadOnly(), IsApartmentOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        logger.info('Apartment created: owner=%s', self.request.user.email)

    @action(detail=True, methods=['get'])
    def reviews(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Returns all reviews for the given apartment with best-effort caching.'''
        apartment = self.get_object()

        paginator = self.pagination_class()
        cache_key = f'apartment_review:{apartment.pk}:page:{request.query_params.get("page", "1")}'

        try:
            cached_payload = cache.get(cache_key)
        except (ConnectionInterrupted, RedisConnectionError):
            cached_payload = None

        if cached_payload is not None:
            return Response(cached_payload)

        reviews = Review.objects.filter(apartment=apartment).select_related('author')
        page = paginator.paginate_queryset(reviews, request, view=self)
        if page is not None:
            serializer = ReviewReadSerializer(page, many=True)
            response = paginator.get_paginated_response(serializer.data)
            payload = response.data
        else:
            serializer = ReviewReadSerializer(reviews, many=True)
            payload = serializer.data

        try:
            cache.set(cache_key, payload, timeout=60)
        except (ConnectionInterrupted, RedisConnectionError):
            pass

        return Response(payload)

    @action(detail=True, methods=['get'])
    def availability(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Returns apartment info along with occupied date ranges.'''
        apartment = self.get_object()
        
        # We only care about bookings that actually block the calendar
        busy_bookings = Booking.objects.filter(
            apartment=apartment,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
        ).values('check_in', 'check_out').order_by('check_in')

        busy_dates = [
            {
                'check_in': parse_date(item['check_in'].isoformat()) or item['check_in'],
                'check_out': parse_date(item['check_out'].isoformat()) or item['check_out'],
            }
            for item in busy_bookings
        ]
        serializer = ApartmentReadSerializer(apartment)

        return Response({
            'apartment': serializer.data,
            'busy_dates': busy_dates
        })
