from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path("fetchZipCode", views.location_by_zip_view, name="location_by_zip_view"),
]
