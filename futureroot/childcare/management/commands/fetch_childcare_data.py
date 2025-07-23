import requests
from django.core.management.base import BaseCommand
from childcare.models import Childcare
from decouple import config

YELP_API_KEY = config("YELP_API_KEY")
YELP_URL = "https://api.yelp.com/v3/businesses/search"

HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}


class Command(BaseCommand):
    help = "Fetch childcare listings from Yelp API"

    def handle(self, *args, **kwargs):
        params = {
            "term": "childcare",
            "location": "Rosyln, NY",
            "categories": "childcare,daycare,preschool",
            "limit": 50,
        }

        response = requests.get(YELP_URL, headers=HEADERS, params=params)
        print(response)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR("API request failed"))
            return

        for biz in response.json().get("businesses", []):
            print(biz)
            name = biz.get("name")
            lat = biz["coordinates"]["latitude"]
            lon = biz["coordinates"]["longitude"]
            address = ", ".join(biz["location"]["display_address"])
            rating = biz.get("rating", 0.0)

            Childcare.objects.update_or_create(
                name=name,
                defaults={
                    "type": "daycare",
                    "address": address,
                    "lat": lat,
                    "lon": lon,
                    "quality_rating": rating,
                    "cost_per_month": None,  # can be enriched later
                },
            )

        self.stdout.write(self.style.SUCCESS("Childcare data successfully imported"))
