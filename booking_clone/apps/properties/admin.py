from django.contrib import admin

from .models import Apartment, City, Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    '''Admin interface for the Country model.
    Displays country names and allows searching by name.'''

    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    '''Admin interface for the City model.
    Displays city names and their associated countries,
    allows filtering by country and searching by city name.'''

    list_display = ('id', 'name')
    list_filter = ('country',)
    search_fields = ('name',)


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    '''Admin interface for the Apartment model.'''

    list_display = ('id', 'title', 'city', 'price_per_night', 'rooms', 'owner', 'created_at')
    list_filter = ('city', 'rooms', 'created_at')
    search_fields = ('title', 'address')
