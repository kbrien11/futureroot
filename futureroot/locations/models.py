from django.db import models


class Location(models.Model):
    zip_code = models.CharField(max_length=5, blank=True, null=True)
    cost_center_infant = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    housing_cost = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    niche_school_url = models.URLField(blank=True, null=True)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )

    def __str__(self):
        return f"{self.name}, {self.city}, {self.state}"
