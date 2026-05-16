import argparse
import random
from datetime import date, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users.models import CustomUser
from apps.properties.models import Country, City, Apartment
from apps.bookings.models import Booking
from apps.reviews.models import Review


class Command(BaseCommand):
    help = 'Seeds the database with sample data'

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Review.objects.all().delete()
            Booking.objects.all().delete()
            Apartment.objects.all().delete()
            City.objects.all().delete()
            Country.objects.all().delete()
            CustomUser.objects.exclude(is_superuser=True).delete()

        self.stdout.write('Seeding data...')

        # 1. Create Users
        landlords = []
        for i in range(5):
            email = f'landlord{i}@example.com'
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={'is_landlord': True}
            )
            if created:
                user.set_password('password123')
                user.save()
            landlords.append(user)

        renters = []
        for i in range(10):
            email = f'renter{i}@example.com'
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={'is_renter': True}
            )
            if created:
                user.set_password('password123')
                user.save()
            renters.append(user)

        # 2. Create Countries and Cities
        countries_data = {
            'Kazakhstan': ['Almaty', 'Astana', 'Shymkent'],
            'France': ['Paris', 'Lyon', 'Marseille'],
            'USA': ['New York', 'Los Angeles', 'Chicago'],
        }

        cities = []
        for country_name, city_names in countries_data.items():
            country, _ = Country.objects.get_or_create(name=country_name)
            for city_name in city_names:
                city, _ = City.objects.get_or_create(name=city_name, country=country)
                cities.append(city)

        # 3. Create Apartments
        apartments = []
        titles = ['Cozy Studio', 'Luxury Penthouse', 'Modern Loft', 'Quiet Garden Apartment', 'Central Suite']
        for i in range(20):
            title = f'{random.choice(titles)} {i}'
            apt, created = Apartment.objects.get_or_create(
                title=title,
                defaults={
                    'description': 'A wonderful place to stay with all amenities.',
                    'address': f'{random.randint(1, 999)} Sample St',
                    'city': random.choice(cities),
                    'price_per_night': random.randint(50, 500),
                    'rooms': random.randint(1, 5),
                    'owner': random.choice(landlords)
                }
            )
            apartments.append(apt)

        # 4. Create Bookings and Reviews
        for renter in renters:
            # Each renter makes 2-4 bookings
            num_bookings = random.randint(2, 4)
            chosen_apts = random.sample(apartments, num_bookings)
            
            for apt in chosen_apts:
                # Past booking (Completed)
                start_date = date.today() - timedelta(days=random.randint(10, 100))
                end_date = start_date + timedelta(days=random.randint(1, 7))
                
                # Check if this renter already has a completed stay here
                if not Booking.objects.filter(tenant=renter, apartment=apt, status=Booking.Status.COMPLETED).exists():
                    try:
                        Booking.objects.create(
                            tenant=renter,
                            apartment=apt,
                            check_in=start_date,
                            check_out=end_date,
                            status=Booking.Status.COMPLETED
                        )

                        # Create a review (get_or_create to avoid duplicate review errors)
                        Review.objects.get_or_create(
                            apartment=apt,
                            author=renter,
                            defaults={
                                'rating': random.randint(3, 5),
                                'comment': random.choice([
                                    "Excellent stay!",
                                    "Clean and comfortable.",
                                    "Great location, would stay again.",
                                    "Average experience.",
                                    "The host was very helpful."
                                ])
                            }
                        )
                    except Exception:
                        continue

                # Future booking
                future_start = date.today() + timedelta(days=random.randint(1, 30))
                future_end = future_start + timedelta(days=random.randint(1, 5))
                
                try:
                    if not Booking.objects.filter(
                        apartment=apt,
                        check_in__lt=future_end,
                        check_out__gt=future_start
                    ).exists():
                        Booking.objects.create(
                            tenant=renter,
                            apartment=apt,
                            check_in=future_start,
                            check_out=future_end,
                            status=random.choice([Booking.Status.PENDING, Booking.Status.CONFIRMED])
                        )
                except Exception:
                    continue

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database!'))
