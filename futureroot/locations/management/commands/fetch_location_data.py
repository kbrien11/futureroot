import re
import requests
from django.core.management.base import BaseCommand
from childcare.models import Childcare
from locations.models import Location
from decouple import config

META_DATA_API = config("META_DATA_API")  # <- Add your actual key here
BASE_URL = "https://global.metadapi.com/zipc/v1/zipcodes"
SOI_URL = "https://global.metadapi.com/zipc/v1/zipcodes/{zip}/soi"
headers = {"Ocp-Apim-Subscription-Key": META_DATA_API}
NATIONAL_MEDIAN_INCOME = 70000.0


def extract_zip(address: str) -> str | None:
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


def get_unique_zip_codes():
    zip_set = set()
    for entry in Childcare.objects.all():
        zip_code = extract_zip(entry.address)
        if zip_code:
            zip_set.add(zip_code)
    return list(zip_set)


class Command(BaseCommand):
    help = "Fetch location data from MetaDapi for all ZIPs used in Childcare records"

    def handle(self, *args, **kwargs):
        zip_codes = get_unique_zip_codes()
        self.stdout.write(
            self.style.NOTICE(f"Fetching data for {len(zip_codes)} ZIP codes...")
        )

        for zip_code in zip_codes:
            try:
                # Basic location data
                loc_url = f"{BASE_URL}/{zip_code}"
                loc_resp = requests.get(loc_url, headers=headers, timeout=10)
                if loc_resp.status_code != 200:
                    self.stdout.write(
                        self.style.WARNING(
                            f"MetaDapi 401 response for {zip_code}: {loc_resp.text}"
                        )
                    )
                    continue
                loc_data = loc_resp.json()

                # Income data
                soi_url = SOI_URL.format(zip=zip_code)
                soi_resp = requests.get(soi_url, headers=HEADERS, timeout=10)
                if soi_resp.status_code != 200:
                    self.stdout.write(
                        self.style.WARNING(
                            f"SOI failed for {zip_code}: {soi_resp.status_code}"
                        )
                    )
                    continue
                soi_data = soi_resp.json()
                income = soi_data.get("adjustedGrossIncomeAmount")

                if income is None:
                    self.stdout.write(
                        self.style.WARNING(f"No income data for {zip_code}, skipping")
                    )
                    continue

                # Insert into Location model
                Location.objects.update_or_create(
                    zip_code=zip_code,
                    defaults={
                        "name": f"{loc_data.get('cityName')} ({zip_code})",
                        "city": loc_data.get("cityName"),
                        "state": loc_data.get("stateCode"),
                        "median_income": income,
                        "childcare_cost_index": round(
                            income / NATIONAL_MEDIAN_INCOME, 2
                        ),
                    },
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{zip_code} → ${income:.0f} income | Index saved"
                    )
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error for {zip_code}: {str(e)}"))
