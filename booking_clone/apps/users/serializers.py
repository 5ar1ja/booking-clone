from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from apps.users.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    first_name = serializers.CharField()
    last_name = serializers.CharField()

    is_landlord = serializers.BooleanField()
    is_renter = serializers.BooleanField()

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "avatar",
            "is_landlord",
            "is_renter",
        ]

        read_only_fields = ["is_staff", "is_superuser"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    first_name = serializers.CharField()
    last_name = serializers.CharField()

    is_landlord = serializers.BooleanField()
    is_renter = serializers.BooleanField()

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "avatar",
            "is_landlord",
            "is_renter",
        )

    def validate(self, data):
        # We get the values out of the 'data' dictionary
        landlord = data.get("is_landlord")
        renter = data.get("is_renter")

        if landlord == renter:
            raise ValidationError(
                "You must choose exactly one role: Landlord or Renter."
            )

        return data

    def create(self, validated_data):
        # This calls the CustomUserManager method you wrote earlier
        return CustomUser.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ("email", "password")

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email and password:
            # Стандартная функция Django: ищет юзера и проверяет пароль
            user = authenticate(email=email, password=password)

            if not user:
                raise ValidationError("Invalid email or password.")

            if not user.is_active:
                raise ValidationError("User account is disabled.")
        else:
            raise ValidationError("Must include 'email' and 'password'.")

        # Мы добавляем найденного юзера в проверенные данные,
        # чтобы View мог его легко достать и выдать ему токен
        data["user"] = user
        return data
