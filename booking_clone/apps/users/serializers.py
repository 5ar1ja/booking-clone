from rest_framework import serializers
from rest_framework.serializers import ValidationError

from django.contrib.auth import authenticate

from apps.users.models import CustomUser

ERR_ROLE_CONFLICT = 'You must choose exactly one role: Landlord or Renter.'
ERR_INVALID_CREDENTIALS = 'Invalid email or password.'
ERR_ACCOUNT_DISABLED = 'User account is disabled.'
ERR_MISSING_CREDENTIALS = 'Must include \'email\' and \'password\'.'


class CustomUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        required=False,
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_landlord = serializers.BooleanField()
    is_renter = serializers.BooleanField()

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'first_name', 'last_name', 'is_landlord', 'is_renter']
        read_only_fields = ['is_staff', 'is_superuser']

    def update(self, instance: CustomUser, validated_data: dict) -> CustomUser:
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=['password'])
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_landlord = serializers.BooleanField()
    is_renter = serializers.BooleanField()

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'first_name', 'last_name', 'is_landlord', 'is_renter')

    def validate(self, data: dict) -> dict:
        if data.get('is_landlord') == data.get('is_renter'):
            raise ValidationError(ERR_ROLE_CONFLICT)
        return data

    def create(self, validated_data: dict) -> CustomUser:
        password = validated_data.pop('password')
        return CustomUser.objects.create_user(password=password, **validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data: dict) -> dict:
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise ValidationError(ERR_INVALID_CREDENTIALS)
            if not user.is_active:
                raise ValidationError(ERR_ACCOUNT_DISABLED)
        else:
            raise ValidationError(ERR_MISSING_CREDENTIALS)

        data['user'] = user
        return data
