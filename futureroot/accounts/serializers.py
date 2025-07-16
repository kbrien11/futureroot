from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "password",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            email=validated_data["email"],
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
            is_active=False,
        )
        print(user)
        Token.objects.create(user=user)
        return user
