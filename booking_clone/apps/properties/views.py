from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
# from django.core.cache import cache 
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import Apartment
from .serializers import ApartmentSerializer
from .filters import ApartmentFilter
from .permissions import IsLandlordOrReadOnly, IsApartmentOwner

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer



class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.select_related("city", "city__country", "owner").all()
    serializer_class = ApartmentSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = ApartmentFilter

    permission_classes = [IsLandlordOrReadOnly, IsApartmentOwner]


    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @method_decorator(cache_page(60, key_prefix="apartment_review"))
    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):

        apartment = self.get_object()

        reviews = Review.objects.filter(apartment=apartment).select_related("author")

        serializer = ReviewSerializer(reviews, many=True)

        return Response(serializer.data)