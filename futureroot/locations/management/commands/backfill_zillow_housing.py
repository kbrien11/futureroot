import os
import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from locations.models import Location

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZILLOW_PATH = os.path.join(BASE_DIR, "data", "zillow_zhvi.csv")


class Command(BaseCommand):
    help = "Backfills Location.housing_cost using Zillow ZHVI file"

    def handle(self, *args, **kwargs):
        if not os.path.exists(ZILLOW_PATH):
            self.stdout.write(
                self.style.ERROR(f"❌ Zillow file not found at {ZILLOW_PATH}")
            )
            return

        df = pd.read_csv(ZILLOW_PATH)

        updated, skipped = 0, 0

        for _, row in df.iterrows():
            zip_code = str(row.get("RegionName")).zfill(5)
            zhvi = row.get("2025-06-30")

            if pd.isna(zhvi) or not zip_code:
                skipped += 1
                continue

            loc = Location.objects.filter(zip_code=zip_code).first()
            if loc:
                loc.housing_cost = Decimal(zhvi)
                loc.save()
                updated += 1
                print(f"✅ {zip_code}: set housing_cost to ${zhvi}")
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"🏡 Backfill complete. Updated: {updated}, Skipped: {skipped}"
            )
        )
