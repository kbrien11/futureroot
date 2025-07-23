# locations/management/commands/enrich_childcare_costs.py

import re
from django.core.management.base import BaseCommand
from childcare.models import Childcare
from locations.models import Location
from locations.utils import enrich_locations_with_ndcp

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "NDCP2022.csv")
ZIP_DATA_PATH = os.path.join(BASE_DIR, "data", "ZIP_COUNTY_032025.csv")
MONTHLY_MULTIPLIER = 4.63


def extract_zip(address: str) -> str | None:
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


class Command(BaseCommand):
    help = "Update childcare cost_per_month using NDCP county-level pricing"

    def handle(self, *args, **kwargs):
        cost_map = enrich_locations_with_ndcp(DATA_PATH, ZIP_DATA_PATH)
        updated = 0

        for provider in Childcare.objects.filter(cost_per_month__isnull=True):
            zip_code = extract_zip(provider.address)

            if not zip_code:
                continue

            location = Location.objects.filter(zip_code=zip_code).first()
            if not location or not location.zip_code:
                continue

            weekly_cost = cost_map.get(location.zip_code)
            if weekly_cost is None:
                continue

            monthly_cost = round(weekly_cost * MONTHLY_MULTIPLIER, 2)
            provider.cost_per_month = monthly_cost
            provider.save()
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Updated {updated} childcare entries with NDCP pricing")
        )
