from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from apps.users.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    # avatar = serializers.SerializerMethodField()

    first_name = serializers.CharField()
    last_name = serializers.CharField()

    is_landlord = serializers.BooleanField()
    is_renter = serializers.BooleanField()

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
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
        password = validated_data.pop("password")
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


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
            # Search the User email and check password
            user = authenticate(email=email, password=password)

            if not user:
                raise ValidationError("Invalid email or password.")

            if not user.is_active:
                raise ValidationError("User account is disabled.")
        else:
            raise ValidationError("Must include 'email' and 'password'.")

        # We show user data if we found
        data["user"] = user
        return data
