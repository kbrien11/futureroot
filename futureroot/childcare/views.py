from django.shortcuts import render
from rest_framework.decorators import action, api_view
from collections import defaultdict
from django.db.models import Q

# Create your views here.
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

from locations.serializers import locationSerializer
from .models import Childcare
from .serializer import childCareSerializer
from .utils import get_zip_from_address, formatted_cost
from locations.models import Location
from locations.utils import enrich_location_with_aarp_scores


@api_view(["GET"])
def getChildCareData(request):
    querySet = Childcare.objects.all()
    ser = childCareSerializer(querySet, many=True)
    if ser.data:
        return Response({"data": ser.data, "status": status.HTTP_200_OK})
    else:
        return Response(
            {
                "data": ser.data,
                "count": len(ser.data),
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        )


@api_view(["GET"])
def compare_childcare_view(request):
    town_filter = request.GET.get("towns")
    queryset = Childcare.objects.all()

    towns = []
    if town_filter:
        towns = [t.strip() for t in town_filter.split(",")]
        town_queries = Q()
        for town in towns:
            town_queries |= Q(town__iexact=town)
        queryset = queryset.filter(town_queries)

    cost_map = defaultdict(list)
    zip_map = defaultdict(set)

    # Group costs and ZIPs by town
    for provider in queryset:
        town = provider.town.strip() if provider.town else None
        zip_code = get_zip_from_address(provider.address) if provider.address else None

        if town and provider.cost_per_month:
            try:
                cost = float(provider.cost_per_month)
                cost_map[town].append(cost)
                if zip_code:
                    zip_map[town].add(zip_code)
            except (TypeError, ValueError):
                continue

    # Build final response
    response_data = {}
    for town, costs in cost_map.items():
        avg_childcare = round(sum(costs) / len(costs), 2)
        zip_codes = zip_map.get(town, [])
        housing_costs = []

        for z in zip_codes:
            loc = Location.objects.filter(zip_code=z).first()
            loc_ser = locationSerializer(loc, many=False)
            loc_data = loc_ser.data  # .data gives you the actual dictionary

            if loc_data.get("livability_score") is None:
                enrich_location_with_aarp_scores(loc, z)
            if loc and loc.housing_cost:
                housing_costs.append(float(loc.housing_cost))

        avg_housing = (
            round(sum(housing_costs) / len(housing_costs), 2) if housing_costs else None
        )

        response_data[town] = {
            "avg_monthly_childcare": avg_childcare,
            "avg_housing_cost": formatted_cost(avg_housing),
            "locationData": loc_ser.data,
        }

    return Response(response_data)


@api_view(["GET"])
def childcare_by_town_view(request):
    town_param = request.GET.get("town")
    queryset = Childcare.objects.all()

    if town_param:
        queryset = queryset.filter(town__iexact=town_param.strip())

    serializer = childCareSerializer(queryset, many=True)
    return Response({"data": serializer.data, "count": len(serializer.data)})
