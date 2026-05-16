from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

ERR_EMAIL_REQUIRED = _('Users must have an email address')
ERR_STAFF_REQUIRED = _('Superuser must have is_staff=True')
ERR_SUPERUSER_REQUIRED = _('Superuser must have is_superuser=True')

ROLE_LANDLORD = _('Landlord')
ROLE_RENTER = _('Renter')


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
    '''
    Custom user model using email instead of username as the login field.
    Supports two roles: Landlord and Renter.
    '''

    email = models.EmailField(
        unique=True,
        verbose_name=_('Email address'),
        help_text=_('Unique identifier for the user.')
    )
    first_name = models.CharField(
        max_length=255,
        verbose_name=_('First name'),
        help_text=_('User\'s given name.')
    )
    last_name = models.CharField(
        max_length=255,
        verbose_name=_('Last name'),
        help_text=_('User\'s family name.')
    )

    is_landlord = models.BooleanField(
        default=False,
        verbose_name=_('Is landlord'),
        help_text=_('Designates whether the user can list apartments.')
    )
    is_renter = models.BooleanField(
        default=False,
        verbose_name=_('Is renter'),
        help_text=_('Designates whether the user can book apartments.')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Designates whether this user should be treated as active.')
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('Is staff'),
        help_text=_('Designates whether the user can log into this admin site.')
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_landlord']),
            models.Index(fields=['is_renter']),
        ]

    def __str__(self) -> str:
        role = 'Superuser' if self.is_superuser else (ROLE_LANDLORD if self.is_landlord else ROLE_RENTER)
        return f'{self.email} ({role})'
