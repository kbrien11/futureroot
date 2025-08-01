from rest_framework import serializers
from locations.models import Location


class locationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "zip_code",
            "housing_cost",
            "great_schools_url",
            "tax_rate",
            "livability_score",
            "housing_score",
            "neighborhood_score",
            "transportation_score",
            "environment_score",
            "health_score",
            "engagement_score",
            "opportunity_score",
            "median_household_income",
        ]
