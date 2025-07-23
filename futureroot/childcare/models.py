from django.db import models


from django.contrib.auth import get_user_model


class Childcare(models.Model):
    name = models.CharField(max_length=128)
    type = models.CharField(
        max_length=64,
        choices=[
            ("daycare", "Daycare"),
            ("preschool", "Preschool"),
            ("after_school", "After School Program"),
            ("nanny", "Nanny Service"),
            ("other", "Other"),
        ],
    )
    # neighborhood = models.ForeignKey(
    #     Neighborhood, on_delete=models.SET_NULL, null=True, blank=True
    # )
    address = models.CharField(max_length=256)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    age_range = models.CharField(max_length=32, help_text="e.g. 6mo–5yrs")
    cost_per_month = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    capacity = models.IntegerField(null=True, blank=True)
    current_enrollment = models.IntegerField(default=0)
    quality_rating = models.FloatField(null=True, blank=True)  # e.g. from reviews
    owner = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True, blank=True
    )
    is_verified = models.BooleanField(default=False)
    added_on = models.DateTimeField(auto_now_add=True)
    town = models.CharField(max_length=100, blank=True, null=True)

    def extract_town(self):
        import re

        match = re.search(r",\s*(.+?),\s*[A-Z]{2}\s*\d{5}", self.address)
        return match.group(1).strip() if match else None

    def __str__(self):
        return self.name
