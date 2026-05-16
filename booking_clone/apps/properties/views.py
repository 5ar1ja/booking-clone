import logging
from typing import Any

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from apps.core.pagination import StandardResultsSetPagination
from apps.core.mixins.views import ActionSerializerMixin
from apps.bookings.models import Booking
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

    def get_queryset(self):
        return Apartment.objects.select_related('city', 'city__country', 'owner').all()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticatedOrReadOnly(), IsLandlordOrReadOnly(), IsApartmentOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        logger.info('Apartment created: owner=%s', self.request.user.email)

    @method_decorator(cache_page(60, key_prefix='apartment_review'))
    @action(detail=True, methods=['get'])
    def reviews(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Returns all reviews for the given apartment (cached 60 s).'''
        apartment = self.get_object()
        reviews = Review.objects.filter(apartment=apartment).select_related('author')
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(reviews, request, view=self)
        if page is not None:
            serializer = ReviewReadSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ReviewReadSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def availability(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Returns apartment info along with occupied date ranges.'''
        apartment = self.get_object()
        
        # We only care about bookings that actually block the calendar
        busy_bookings = Booking.objects.filter(
            apartment=apartment,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
        ).values('check_in', 'check_out').order_by('check_in')
        
        serializer = ApartmentReadSerializer(apartment)
        
        return Response({
            'apartment': serializer.data,
            'busy_dates': list(busy_bookings)
        })
