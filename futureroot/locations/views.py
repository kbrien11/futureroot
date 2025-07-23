from django.shortcuts import render
from rest_framework.decorators import action, api_view
from collections import defaultdict
from django.db.models import Q

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

    return Response(
        {
            "zip_code": loc.zip_code,
            "housing_cost": "${:,.0f}".format(float(loc.housing_cost))
            if loc.housing_cost
            else None,
            "school_rating": round(float(loc.school_rating), 2)
            if loc.school_rating
            else None,
            "tax_rate": f"{float(loc.tax_rate):.2f}%" if loc.tax_rate else None,
            # Add any other fields you’ve populated
        }
    )
