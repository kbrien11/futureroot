from django.db import models


class Location(models.Model):
    zip_code = models.CharField(max_length=5, blank=True, null=True)
    cost_center_infant = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    housing_cost = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    great_schools_url = models.URLField(blank=True, null=True)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    commuter_score = models.CharField(null=True, blank=True)

    livability_score = models.CharField(null=True, blank=True)

    housing_score = models.CharField(null=True, blank=True)
    neighborhood_score = models.CharField(null=True, blank=True)
    transportation_score = models.CharField(null=True, blank=True)
    environment_score = models.CharField(null=True, blank=True)
    health_score = models.CharField(null=True, blank=True)
    engagement_score = models.CharField(null=True, blank=True)
    opportunity_score = models.CharField(null=True, blank=True)
    median_household_income = models.CharField(null=True, blank=True)
