import logging
from celery import shared_task
from .models import Location
from django.db.models import Q
from uszipcode import SearchEngine
from .utils import enrich_location_with_aarp_scores
from django.contrib.auth import get_user_model
from profiles.models import UserPreferenceResult
from .utils import (
    scrape_aarp_scores,
    enrich_location_with_aarp_scores,
    haversine,
    get_coords,
)
from .serializers import locationSerializer


logger = logging.getLogger(__name__)


@shared_task
def refresh_missing_zip_scores():
    missing = Location.objects.filter(livability_score__isnull=True)
    logger.info(f"Starting enrichment for {missing.count()} ZIPs")

    for loc in missing:
        try:
            enrich_location_with_aarp_scores(loc, loc.zip_code)
            logger.info(f"Updated ZIP {loc.zip_code}")
        except Exception as e:
            logger.error(f"Error enriching ZIP {loc.zip_code}: {e}")


# tasks.py


User = get_user_model()

GRADE_MAP = {
    "A": 7,
    "A-": 6,
    "B": 5,
    "B-": 4,
    "C": 3,
    "C-": 2,
    "D": 1,
    "F": 0,
    None: -1,  # Treat missing grades as lowest
}


def grade_to_score(grade):
    return GRADE_MAP.get(grade, -1)


@shared_task
def run_zip_recommendation(user_id, preferences, target_zip, name=""):

    origin_lat, origin_lng = get_coords(target_zip)
    if origin_lat is None or origin_lng is None:
        return {"error": f"Could not find coordinates for ZIP {target_zip}."}

    valid_filter = Q()
    for field in preferences:
        valid_filter &= Q(**{f"{field}__isnull": False})

    locations = Location.objects.filter(valid_filter)

    def sort_key(loc):
        return tuple(-grade_to_score(getattr(loc, field)) for field in preferences)

    sorted_locations = sorted(locations, key=sort_key)
    location_ser = locationSerializer(sorted_locations, many=True)

    final_output = []
    for loc_data in location_ser.data:
        zip_code = loc_data.get("zip_code")
        if not zip_code:
            continue

        lat, lng = get_coords(zip_code)
        if lat is None or lng is None:
            continue

        distance = haversine(origin_lat, origin_lng, lat, lng)
        if not (12 <= distance <= 25):
            continue

        search = SearchEngine()
        zipcode_info = search.by_zipcode(zip_code)

        score = 0
        details = {}
        for field in preferences:
            grade = loc_data.get(field)
            numeric = grade_to_score(grade)
            score += numeric
            details[field] = grade

        final_output.append(
            {
                "zip_code": zip_code,
                "score": score,
                "details": details,
                "distance": round(distance, 2),
                "town": zipcode_info.major_city,
            }
        )

        if len(final_output) == 10:
            break

    # Save to DB
    try:
        user = User.objects.get(id=user_id)
        print(user)
        print(final_output)
        UserPreferenceResult.objects.create(
            user=user,
            name=name,
            filters={"preferences": preferences, "target_zip": target_zip},
            zip_codes=[entry["zip_code"] for entry in final_output],
        )
    except Exception as e:
        return {"error": str(e)}

    return {
        "status": "success",
        "zip_codes": [entry["zip_code"] for entry in final_output],
    }
