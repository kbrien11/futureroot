from django.shortcuts import render
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer
from .models import CustomUser
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.views import Response
from rest_framework.decorators import action, api_view
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import authenticate


# Create your views here.


@api_view(["POST"])
def createUser(request):
    try:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)

            return Response(
                {
                    "data": serializer.data,
                    "token": token.key,
                    "status": status.HTTP_200_OK,
                }
            )
    except Exception as e:
        return Response(
            {"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
        )


# @api_view(["POST"])
# def login(request):
#     email = request.data.get("email")
#     password = request.data.get("password")
#     user_obj = CustomUser.objects.filter(email__iexact=email).first()
#     ser = UserSerializer(user_obj, many=False)
#     if user_obj:
#         validate_password = check_password(password, ser.data["password"])
#         print(validate_password, password)
#         if validate_password:
#             token = Token.objects.get(user=user_obj)
#             return Response(
#                 {
#                     "username": ser.data["username"],
#                     "id": ser.data["id"],
#                     "token": token.key,
#                     "status": status.HTTP_200_OK,
#                 }
#             )
#         else:
#             print("error logging in")
#             return Response(
#                 {
#                     "passwordError": "invalid password",
#                     "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 }
#             )
#     else:
#         print("email is wrong")
#         return Response(
#             {
#                 "EmailError": "invalid email",
#                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
#             }
#         )


@api_view(["POST"])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = CustomUser.objects.filter(email__iexact=email).first()

    if not user:
        return Response(
            {"emailError": "Invalid email"}, status=status.HTTP_404_NOT_FOUND
        )

    if not check_password(password, user.password):
        return Response(
            {"passwordError": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)
    ser = UserSerializer(user)

    return Response(
        {
            "username": ser.data["username"],
            "id": ser.data["id"],
            "token": token.key,
            "status": status.HTTP_200_OK,
        }
    )
