# yourapp/management/commands/backfill_commute_scores.py
import os
import pandas as pd
from django.core.management.base import BaseCommand
from locations.models import Location
import math

# Assume this is precomputed from your dataset or anchor ZIPs
MAX_COMMUTERS = 12000


def to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def normalize_commute_score(commute_score, min_score=0.0, max_score=10.0):
    return assign_commute_grade(
        round((commute_score - min_score) / (max_score - min_score) * 100, 1)
    )


def assign_commute_grade(score):
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "A−"
    elif score >= 75:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 65:
        return "B−"
    elif score >= 60:
        return "C+"
    elif score >= 55:
        return "C"
    elif score >= 50:
        return "C−"
    elif score >= 40:
        return "D"
    else:
        return "F"


def get_commuter_score(row):
    total_commuters = to_int(row.get("B08303_001E"))

    burden_sum = (
        to_int(row.get("B08303_009E")) * 0.8
        + to_int(row.get("B08303_010E")) * 1.0  # 25–29 mins
        + to_int(row.get("B08303_011E")) * 1.2  # 30–34
        + to_int(row.get("B08303_012E")) * 1.4  # 35–39
        + to_int(row.get("B08303_013E")) * 1.6  # 40–44
        + to_int(row.get("B08303_014E")) * 1.8  # 45–59
        + to_int(row.get("B08303_015E")) * 2.0  # 60–89  # 90+ mins
    )

    burden_index = burden_sum / max(1, total_commuters)
    commute_score = round(
        (2.5 - burden_index) * 4.0, 2
    )  # Normalized: lower burden → higher score
    return normalize_commute_score(commute_score)


def normalize_zip(raw_zip):
    import re

    if pd.isna(raw_zip):
        return None
    if isinstance(raw_zip, (int, float)):
        return str(int(raw_zip)).zfill(5)
    if isinstance(raw_zip, str):
        match = re.search(r"(\d{5})", raw_zip)
        return match.group(0) if match else None
    return None


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMMUTER_PATH = os.path.join(BASE_DIR, "data", "commuteData.csv")


class Command(BaseCommand):
    help = "Backfill commuter scores using ACS data from CSV"

    def handle(self, *args, **kwargs):
        if not os.path.exists(COMMUTER_PATH):
            self.stdout.write(
                self.style.ERROR(f"❌ Zillow file not found at {COMMUTER_PATH}")
            )
            return

        df = pd.read_csv(COMMUTER_PATH)

        # Compute scores
        df["commuter_score"] = df.apply(get_commuter_score, axis=1)

        # Fetch locations by GEO_ID and bulk update scores
        updates = []
        zip_val = ""
        for _, row in df.iterrows():
            raw_zip = row.get("NAME")
            zip_val = normalize_zip(raw_zip)
            print(zip_val)
            if zip_val is not None:
                location = Location.objects.filter(zip_code=zip_val).first()
                if location:
                    location.commuter_score = row["commuter_score"]
                    updates.append(location)
                else:
                    print(f"⚠️ No Location found for ZIP: {zip_val}")
            else:
                print(f"⚠️ Invalid ZIP value in row: {raw_zip}")
        if updates:
            Location.objects.bulk_update(updates, ["commuter_score"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Updated {len(updates)} locations with commuter scores"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("⚠️ No matching locations found"))
