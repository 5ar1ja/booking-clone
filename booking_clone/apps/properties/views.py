import logging

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer
from .filters import ApartmentFilter
from .models import Apartment
from .permissions import IsApartmentOwner, IsLandlordOrReadOnly
from .serializers import ApartmentSerializer

logger = logging.getLogger('apps.properties')


class ApartmentViewSet(viewsets.ModelViewSet):
    '''CRUD for apartments with filtering by city, country, price, and rooms.'''

    queryset = Apartment.objects.select_related('city', 'city__country', 'owner').all()
    serializer_class = ApartmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ApartmentFilter
    permission_classes = [IsLandlordOrReadOnly, IsApartmentOwner]

    def perform_create(self, serializer: BaseSerializer) -> None:
        serializer.save(owner=self.request.user)
        logger.info('Apartment created: owner=%s', self.request.user.email)

    @method_decorator(cache_page(60, key_prefix='apartment_review'))
    @action(detail=True, methods=['get'])
    def reviews(self, request: DRFRequest, pk: int | None = None) -> Response:
        '''Returns all reviews for the given apartment (cached 60 s).'''
        apartment = self.get_object()
        reviews = Review.objects.filter(apartment=apartment).select_related('author')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
