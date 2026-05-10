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

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer
from .filters import ApartmentFilter
from .models import Apartment
from .permissions import IsApartmentOwner, IsLandlordOrReadOnly
from .serializers import ApartmentReadSerializer, ApartmentWriteSerializer

logger = logging.getLogger('apps.properties')


class ApartmentViewSet(viewsets.ViewSet):
    '''
    ViewSet for apartments.
    Uses ApartmentReadSerializer for GET
    Uses ApartmentWriteSerializer for POST/PUT/PATCH
    '''
    
    permission_classes = [IsAuthenticatedOrReadOnly, IsLandlordOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ApartmentFilter

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
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)