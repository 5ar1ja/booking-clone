# Python modules
from typing import Any

# Django modules
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

# Third-party modules
from rest_framework import serializers
from rest_framework.serializers import ValidationError

# Project modules
from apps.users.constants import ERR_ROLE_CONFLICT
from apps.users.models import CustomUser

ERR_INVALID_CREDENTIALS = _('Invalid email or password.')
ERR_ACCOUNT_DISABLED = _('User account is disabled.')
ERR_MISSING_CREDENTIALS = _('Must include \'email\' and \'password\'.')


class UserReadSerializer(serializers.ModelSerializer):
    '''Serializer for reading user data (GET requests).'''
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_landlord', 'is_renter']
        read_only_fields = fields


class UserRegistrationSerializer(serializers.ModelSerializer):
    '''Serializer for user registration (POST /register).'''
    
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'first_name', 'last_name', 'is_landlord', 'is_renter')

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if data.get('is_landlord') == data.get('is_renter'):
            raise ValidationError(ERR_ROLE_CONFLICT)
        return data

    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        password = validated_data.pop('password')
        return CustomUser.objects.create_user(password=password, **validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    '''Serializer for updating user profile (PATCH /update-profile).'''
    
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'password']

    def update(self, instance: CustomUser, validated_data: dict[str, Any]) -> CustomUser:
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=['password'])
        return instance


class UserLoginSerializer(serializers.Serializer):
    '''Serializer for user login (POST /login).'''
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
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


class LoginResponseSerializer(serializers.Serializer):
    '''Serializer for login response (includes JWT tokens).'''
    
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_landlord = serializers.BooleanField()
    is_renter = serializers.BooleanField()
    access = serializers.CharField()
    refresh = serializers.CharField()
