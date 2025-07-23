from rest_framework import serializers
from childcare.models import Childcare


class childCareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Childcare
        fields = [
            "name",
            "address",
            "type",
            "lat",
            "lon",
            "age_range",
            "capacity",
            "quality_rating",
            "owner",
            "is_verified",
            "added_on",
            "current_enrollment",
            "cost_per_month",
        ]
