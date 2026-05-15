import json
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.properties.models import Country, City, Apartment

User = get_user_model()

class Command(BaseCommand):
    help = 'Load apartment data from seed.json'

    def handle(self, *args, **kwargs):
        try:
            with open('seed.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('seed.json file not found'))
            return

        # Create or get a default user
        user, _ = User.objects.get_or_create(
            email='admin@example.com', 
            defaults={'is_superuser': True, 'is_staff': True}
        )
        if not user.password:
            user.set_password('admin')
            user.save()

        # Create or get a default country and city
        country, _ = Country.objects.get_or_create(name='Kazakhstan')
        city, _ = City.objects.get_or_create(name='Almaty', country=country)

        apartments_created = 0

        for item in data:
            title = item.get('Title', '')
            price_str = item.get('Price', '')
            address = item.get('Subtitle', '')
            description = item.get('Text Preview', '')

            # Extract rooms from title (e.g. "1-комнатная квартира")
            rooms = 1
            room_match = re.search(r'(\d+)-комнатная', title)
            if room_match:
                rooms = int(room_match.group(1))

            # Extract price (e.g. "15 000 〒\nза сутки")
            price_per_night = Decimal('0.00')
            price_part = price_str.split('〒')[0] if '〒' in price_str else price_str
            price_digits = re.sub(r'[^\d]', '', price_part)
            if price_digits:
                price_per_night = Decimal(price_digits)

            # Skip if price is 0 or invalid to avoid bad data
            if price_per_night <= 0:
                continue

            # Create apartment
            Apartment.objects.create(
                title=title,
                description=description,
                address=address,
                city=city,
                price_per_night=price_per_night,
                rooms=rooms,
                owner=user
            )
            apartments_created += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {apartments_created} apartments!'))
