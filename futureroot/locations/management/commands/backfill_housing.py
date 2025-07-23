import requests
from decimal import Decimal
from django.core.management.base import BaseCommand
from locations.models import Location
from locations.utils import get_rentcast_data

RENTCAST_API_KEY = "your_api_key_here"


class Command(BaseCommand):
    help = "Backfills housing_cost for each Location using RentCast API"

    def handle(self, *args, **kwargs):
        updated, skipped = 0, 0

        for loc in Location.objects.all():
            if loc.housing_cost is not None:
                skipped += 1
                continue

            result = get_rentcast_data(loc.zip_code)
            rent = result.get("median_rent")

            if rent:
                loc.housing_cost = Decimal(rent)
                loc.save()
                updated += 1
                print(f"✅ Updated ZIP {loc.zip_code} with rent ${rent}")
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"🏡 Housing cost backfill complete. Updated: {updated}, Skipped: {skipped}"
            )
        )
