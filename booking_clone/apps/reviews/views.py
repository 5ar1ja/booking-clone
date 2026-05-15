import logging
from typing import Any

from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import BaseSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from apps.core.pagination import StandardResultsSetPagination
from apps.bookings.models import Booking
from .filters import ReviewFilter
from .models import Review
from .permissions import IsReviewAuthorOrReadOnly
from .serializers import ReviewReadSerializer, ReviewWriteSerializer

logger = logging.getLogger('apps.reviews')

ERR_OWN_APARTMENT = 'You cannot review your own apartment.'
ERR_NOT_STAYED = 'You can only review apartments you have stayed in.'


@extend_schema_view(
    list=extend_schema(
        summary="List all reviews",
        description="Retrieve a list of all reviews with optional filtering. Permissions: AllowAny (Read-only).",
        responses={200: ReviewReadSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create a new review",
        description="Add a new review for an apartment. Permissions: Authenticated users who stayed in the apartment.",
        request=ReviewWriteSerializer,
        responses={201: ReviewReadSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
    ),
    retrieve=extend_schema(
        summary="Retrieve review details",
        description="Get detailed information about a specific review by its ID. Permissions: AllowAny (Read-only).",
        responses={200: ReviewReadSerializer, 404: OpenApiTypes.OBJECT},
    ),
    update=extend_schema(
        summary="Update a review",
        description="Update all fields of an existing review. Permissions: Authenticated author of the review.",
        request=ReviewWriteSerializer,
        responses={200: ReviewReadSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    ),
    partial_update=extend_schema(
        summary="Partially update a review",
        description="Update specific fields of an existing review. Permissions: Authenticated author of the review.",
        request=ReviewWriteSerializer,
        responses={200: ReviewReadSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    ),
    destroy=extend_schema(
        summary="Delete a review",
        description="Remove a review from the platform. Permissions: Authenticated author of the review.",
        responses={204: None, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    ),
)
class ReviewViewSet(viewsets.ViewSet):
    '''
    ViewSet for reviews.
    Only renters with a completed stay can submit.
    '''
    
    permission_classes = [IsAuthenticatedOrReadOnly, IsReviewAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReviewFilter
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        '''Return the queryset of reviews, optimized with select_related for author and apartment.'''

        return Review.objects.select_related('author', 'apartment').all()

    def get_object(self, pk):
        '''Helper method to retrieve a review by primary key with proper permissions.'''

        obj = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request: DRFRequest) -> Response:
        '''List reviews with optional filtering and pagination. Permissions: AllowAny (Read-only).'''

        queryset = self.get_queryset()
        
        backend = DjangoFilterBackend()
        queryset = backend.filter_queryset(request, queryset, self)
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = ReviewReadSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ReviewReadSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request: DRFRequest) -> Response:
        '''Create a new review. Permissions: Authenticated users who stayed in the apartment.'''

        serializer = ReviewWriteSerializer(data=request.data)
        if serializer.is_valid():
            apartment = serializer.validated_data['apartment']
            user = request.user

            if apartment.owner == user:
                return Response({'detail': ERR_OWN_APARTMENT}, status=status.HTTP_403_FORBIDDEN)

            stayed = Booking.objects.filter(
                apartment=apartment,
                tenant=user,
                status=Booking.Status.COMPLETED,
            ).exists()

            if not stayed:
                return Response({'detail': ERR_NOT_STAYED}, status=status.HTTP_403_FORBIDDEN)

            review = serializer.save(author=user)
            logger.info(
                'Review created: author=%s, apartment_id=%s, rating=%s',
                user.email,
                apartment.id,
                serializer.validated_data.get('rating'),
            )
            
            return Response(ReviewReadSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Retrieve details of a specific review. Permissions: AllowAny (Read-only).'''

        review = self.get_object(pk)
        serializer = ReviewReadSerializer(review)
        return Response(serializer.data)

    def update(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Update an existing review. Permissions: Authenticated author of the review.'''

        review = self.get_object(pk)
        serializer = ReviewWriteSerializer(review, data=request.data)
        if serializer.is_valid():
            review = serializer.save()
            return Response(ReviewReadSerializer(review).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Partially update an existing review. Permissions: Authenticated author of the review.'''

        review = self.get_object(pk)
        serializer = ReviewWriteSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            review = serializer.save()
            return Response(ReviewReadSerializer(review).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request: DRFRequest, pk: Any = None) -> Response:
        '''Delete an existing review. Permissions: Authenticated author of the review.'''

        review = self.get_object(pk)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
