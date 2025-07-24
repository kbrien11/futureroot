from rest_framework import serializers
from locations.models import Location


class locationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "zip_code",
            "cost_center_infant",
            "housing_cost",
            "great_schools_url ",
            "tax_rate",
        ]
