from django.shortcuts import render
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from collections import defaultdict
from django.db.models import Q
from uszipcode import SearchEngine

from .tasks import run_zip_recommendation
from .serializers import locationSerializer
from .utils import (
    scrape_aarp_scores,
    enrich_location_with_aarp_scores,
    haversine,
    get_coords,
)

# Create your views here.
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

from profiles.models import UserPreferenceResult
from locations.models import Location

# Create your views here.
@api_view(["GET"])
def location_by_zip_view(request):
    zip_code = request.GET.get("zip")
    if not zip_code:
        return Response({"error": "Missing ZIP code parameter."}, status=400)

    loc = Location.objects.filter(zip_code=zip_code.strip()).first()

    if not loc:
        return Response({"error": f"No Location found for ZIP {zip_code}."}, status=404)

    # Enrich if livability_score is missing
    if loc.livability_score is None:
        score = scrape_aarp_scores(zip_code)
        print(score)
        if score is not None:
            enrich_location_with_aarp_scores(loc, zip_code)

    # Always construct response_data after enrichment attempt
    response_data = {
        "zip_code": loc.zip_code,
        "commuter_score": loc.commuter_score,
        "housing_cost": "${:,.0f}".format(float(loc.housing_cost))
        if loc.housing_cost
        else None,
        "school_rating": loc.great_schools_url if loc.great_schools_url else None,
        "tax_rate": f"{float(loc.tax_rate):.2f}%" if loc.tax_rate else None,
        "livability_score": loc.livability_score,
        "housing_score": loc.housing_score,
        "neighborhood_score": loc.neighborhood_score,
        "transportation_score": loc.transportation_score,
        "environment_score": loc.environment_score,
        "health_score": loc.health_score,
        "engagement_score": loc.engagement_score,
        "opportunity_score": loc.opportunity_score,
        "median_household_income": loc.median_household_income,
    }

    return Response(response_data)


@api_view(["GET"])
def get_zips_with_livability(request):
    zip_codes = (
        Location.objects.filter(livability_score__isnull=False)
        .values_list("zip_code", flat=True)
        .distinct()
    )
    return JsonResponse({"zips": list(zip_codes)})


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


@api_view(["POST"])
def recommend_zip_codes(request):
    preferences = request.data.get("preferences")
    target_zip = request.data.get("target_zip")
    token_key = request.data.get("token")
    name = request.data.get("name")
    if not isinstance(preferences, list) or len(preferences) != 3:
        return Response(
            {"error": "Please provide exactly three preference fields."}, status=400
        )

    if not target_zip:
        return Response({"error": "Please provide a target ZIP code."}, status=400)

    try:
        token = Token.objects.get(key=token_key)
        user = token.user
    except Token.DoesNotExist:
        return Response({"error": "Invalid token."}, status=403)

    # Trigger background task
    task = run_zip_recommendation.delay(user.id, preferences, target_zip, name)

    return Response(
        {
            "task_id": task.id,
            "status": "processing reccomendation, will provide shortly :)",
        }
    )
    # if not isinstance(preferences, list) or len(preferences) != 3:
    #     return Response(
    #         {"error": "Please provide exactly three preference fields."},
    #         status=status.HTTP_400_BAD_REQUEST,
    #     )

    # if not target_zip:
    #     return Response(
    #         {"error": "Please provide a target ZIP code."},
    #         status=status.HTTP_400_BAD_REQUEST,
    #     )

    # origin_lat, origin_lng = get_coords(target_zip)
    # if origin_lat is None or origin_lng is None:
    #     return Response(
    #         {"error": f"Could not find coordinates for ZIP {target_zip}."},
    #         status=status.HTTP_400_BAD_REQUEST,
    #     )

    # # Filter out locations missing any of the preference fields
    # valid_filter = Q()
    # for field in preferences:
    #     valid_filter &= Q(**{f"{field}__isnull": False})

    # locations = Location.objects.filter(valid_filter)

    # def sort_key(loc):
    #     return tuple(-grade_to_score(getattr(loc, field)) for field in preferences)

    # sorted_locations = sorted(locations, key=sort_key)
    # location_ser = locationSerializer(sorted_locations, many=True)

    # final_output = []
    # for loc_data in location_ser.data:
    #     zip_code = loc_data.get("zip_code")
    #     print(zip_code)
    #     if not zip_code:
    #         continue

    #     lat, lng = get_coords(zip_code)
    #     if lat is None or lng is None:
    #         continue

    #     distance = haversine(origin_lat, origin_lng, lat, lng)
    #     if not (12 <= distance <= 25):
    #         continue

    #     search = SearchEngine()
    #     zipcode_info = search.by_zipcode(zip_code)

    #     score = 0
    #     details = {}
    #     for field in preferences:
    #         grade = loc_data.get(field)
    #         numeric = grade_to_score(grade)
    #         score += numeric
    #         details[field] = grade

    #     final_output.append(
    #         {
    #             "zip_code": zip_code,
    #             "score": score,
    #             "details": details,
    #             "distance": round(distance, 2),
    #             "town": zipcode_info.major_city,
    #         }
    #     )

    #     if len(final_output) == 10:
    #         break

    #     # 🧠 Save preferences and results to the database
    # if token_key:
    #     try:
    #         token = Token.objects.get(key=token_key)
    #         user = token.user
    #         print(token)
    #         print(user)

    #         UserPreferenceResult.objects.create(
    #             user=user,
    #             name=name,
    #             filters={"preferences": preferences, "target_zip": target_zip},
    #             zip_codes=[entry["zip_code"] for entry in final_output],
    #         )
    #     except Token.DoesNotExist:
    #         print("Invalid token: no matching user found.")
    #     except Exception as e:
    #         print(f"Error saving preferences: {e}")

    # return Response({"results": final_output})
