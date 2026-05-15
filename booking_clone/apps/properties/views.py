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
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from apps.core.pagination import StandardResultsSetPagination
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
        description="Returns a list of date ranges that are already booked or pending for this apartment.",
        responses={200: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                'Availability Example',
                value=[
                    {'check_in': '2024-06-01', 'check_out': '2024-06-10'},
                    {'check_in': '2024-07-15', 'check_out': '2024-07-20'}
                ]
            )
        ]
    )
)
class ApartmentViewSet(viewsets.ViewSet):
    '''
    ViewSet for apartments.
    Uses ApartmentReadSerializer for GET
    Uses ApartmentWriteSerializer for POST/PUT/PATCH
    '''
    
    permission_classes = [IsAuthenticatedOrReadOnly, IsLandlordOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ApartmentFilter
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Apartment.objects.select_related('city', 'city__country', 'owner').all()

    def get_object(self, pk):
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticatedOrReadOnly(), IsLandlordOrReadOnly(), IsApartmentOwner()]
        return super().get_permissions()

    def list(self, request: DRFRequest) -> Response:
        queryset = self.get_queryset()
        
        backend = DjangoFilterBackend()
        queryset = backend.filter_queryset(request, queryset, self)
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = ApartmentReadSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ApartmentReadSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request: DRFRequest) -> Response:
        serializer = ApartmentWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            logger.info('Apartment created: owner=%s', request.user.email)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request: DRFRequest, pk: Any = None) -> Response:
        apartment = self.get_object(pk)
        serializer = ApartmentReadSerializer(apartment)
        return Response(serializer.data)

    def update(self, request: DRFRequest, pk: Any = None) -> Response:
        apartment = self.get_object(pk)
        serializer = ApartmentWriteSerializer(apartment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request: DRFRequest, pk: Any = None) -> Response:
        apartment = self.get_object(pk)
        serializer = ApartmentWriteSerializer(apartment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request: DRFRequest, pk: Any = None) -> Response:
        apartment = self.get_object(pk)
        apartment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @method_decorator(cache_page(60, key_prefix='apartment_review'))
    @action(detail=True, methods=['get'])
    def reviews(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Returns all reviews for the given apartment (cached 60 s).'''
        apartment = self.get_object(pk)
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
        '''Returns a list of occupied date ranges for the apartment.'''
        apartment = self.get_object(pk)
        # We only care about bookings that actually block the calendar
        busy_bookings = Booking.objects.filter(
            apartment=apartment,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
        ).values('check_in', 'check_out').order_by('check_in')
        
        return Response(list(busy_bookings))
