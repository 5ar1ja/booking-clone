# Python modules
import logging
from typing import Any

# Django modules
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

# Third-party modules
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response

# Project modules
from apps.core.mixins.views import ActionSerializerMixin, ObjectLookupMixin, PaginationMixin
from apps.core.pagination import StandardResultsSetPagination
from apps.bookings.models import Booking
from apps.core.pagination import StandardResultsSetPagination
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
class ReviewViewSet(
    ActionSerializerMixin,
    ObjectLookupMixin,
    PaginationMixin,
    viewsets.ViewSet,
):
    '''
    ViewSet for reviews.
    Only renters with a completed stay can submit.
    '''
    
    permission_classes = [IsAuthenticatedOrReadOnly, IsReviewAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReviewFilter
    pagination_class = StandardResultsSetPagination
    serializer_class = ReviewReadSerializer
    serializer_action_classes = {
        'create': ReviewWriteSerializer,
        'update': ReviewWriteSerializer,
        'partial_update': ReviewWriteSerializer,
    }

    def get_queryset(self) -> QuerySet[Review]:
        return Review.objects.select_related('author', 'apartment').all()

    def get_object(self, pk: Any = None) -> Review:
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request: DRFRequest) -> Response:
        queryset = self.get_queryset()

        backend = DjangoFilterBackend()
        queryset = backend.filter_queryset(request, queryset, self)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request: DRFRequest) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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

        read_serializer = ReviewReadSerializer(review, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: DRFRequest, pk=None) -> Response:
        review = self.get_object()
        serializer = self.get_serializer(review)
        return Response(serializer.data)

    def update(self, request: DRFRequest, pk=None) -> Response:
        review = self.get_object()
        serializer = self.get_serializer(review, data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(ReviewReadSerializer(review, context=self.get_serializer_context()).data)

    def partial_update(self, request: DRFRequest, pk=None) -> Response:
        review = self.get_object()
        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(ReviewReadSerializer(review, context=self.get_serializer_context()).data)

    def destroy(self, request: DRFRequest, pk=None) -> Response:
        review = self.get_object()
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
