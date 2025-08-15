from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class UserPreferenceResult(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="preference_results"
    )
    filters = models.JSONField()
    zip_codes = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(
        max_length=100, blank=True
    )  # Optional label for easy lookup
