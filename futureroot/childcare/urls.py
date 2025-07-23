from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path("getchChildCareData", views.getChildCareData, name="getchChildCareData"),
    path("compare/", views.compare_childcare_view),
    path("fetchSingleTown/", views.childcare_by_town_view),
]
