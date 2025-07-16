from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path("register", views.createUser, name="create_user"),
    path("login", views.login, name="login"),
]
