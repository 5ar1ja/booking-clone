from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

ERR_EMAIL_REQUIRED = 'Users must have an email address'
ERR_STAFF_REQUIRED = 'Superuser must have is_staff=True'
ERR_SUPERUSER_REQUIRED = 'Superuser must have is_superuser=True'

ROLE_LANDLORD = 'Landlord'
ROLE_RENTER = 'Renter'


class CustomUserManager(BaseUserManager):
    '''Manager for CustomUser using email as the unique identifier.'''

    def create_user(
        self, email: str, password: str | None = None, **extra_fields
    ) -> CustomUser:
        if not email:
            raise ValueError(ERR_EMAIL_REQUIRED)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str, **extra_fields
    ) -> CustomUser:
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(ERR_STAFF_REQUIRED)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError(ERR_SUPERUSER_REQUIRED)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    '''Custom user model using email instead of username as the login field.'''

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    # avatar = models.ImageField(upload_to='avatar/', null=True, blank=True)

    is_landlord = models.BooleanField(default=False)
    is_renter = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self) -> str:
        return f'{self.email} ({ROLE_LANDLORD if self.is_landlord else ROLE_RENTER})'
