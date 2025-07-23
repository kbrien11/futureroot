import re
from django.core.management.base import BaseCommand
from childcare.models import Childcare
from locations.models import Location
from .utils import estimate_cost_per_month


def extract_zip(address: str) -> str | None:
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


class Command(BaseCommand):
    help = "Estimate cost_per_month for Childcare entries missing pricing"

    def handle(self, *args, **kwargs):
        updated = 0

        for provider in Childcare.objects.filter(cost_per_month__isnull=True):
            zip_code = extract_zip(provider.address)
            if not zip_code:
                continue

            location = Location.objects.filter(zip_code=zip_code).first()
            if not location:
                continue

            income = location.median_income
            cost = estimate_cost_per_month(income)

            provider.cost_per_month = cost
            provider.save()
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {updated} childcare entries with estimated costs"
            )
        )
