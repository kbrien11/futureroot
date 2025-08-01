from django.shortcuts import render
from rest_framework.decorators import action, api_view
from collections import defaultdict
from django.db.models import Q
from .utils import scrape_aarp_scores, enrich_location_with_aarp_scores

# Create your views here.
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status


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
