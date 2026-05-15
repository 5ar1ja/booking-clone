import logging
from typing import Any

from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import (
    CustomUserSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)

logger = logging.getLogger('apps.users')


class CustomUserViewSet(ViewSet):
    '''Handles user registration, login, and profile management.'''

    permission_classes = (IsAuthenticated,)

    @action(
        methods=['post'],
        detail=False,
        url_path='register',
        permission_classes=(AllowAny,),
    )
    def register(self, request: DRFRequest) -> DRFResponse:
        '''Register a new user with email, password, and role (landlord or renter).'''

        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info(
            'New user registered: %s (landlord=%s, renter=%s)',
            user.email,
            user.is_landlord,
            user.is_renter,
        )
        return DRFResponse(data=CustomUserSerializer(user).data, status=HTTP_201_CREATED)

    @action(
        methods=('post',),
        detail=False,
        url_path='login',
        permission_classes=(AllowAny,),
    )
    def login(self, request: DRFRequest, *args: Any, **kwargs: Any) -> DRFResponse:
        '''Authenticate user and return JWT tokens along with user info.'''

        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        logger.info('User logged in: %s', user.email)
        refresh = RefreshToken.for_user(user)

        return DRFResponse(
            data={
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_landlord': user.is_landlord,
                'is_renter': user.is_renter,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=HTTP_200_OK,
        )

    @action(
        methods=['get'],
        detail=False,
        url_path='personal-info',
        permission_classes=(IsAuthenticated,),
    )
    def fetch_personal_info(self, request: DRFRequest) -> DRFResponse:
        '''Fetch the authenticated user's personal information. Permissions: Authenticated users only.'''

        user = request.user
        return DRFResponse(
            data={
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_landlord': user.is_landlord,
                'is_renter': user.is_renter,
            },
            status=HTTP_200_OK,
        )

    @action(
        methods=['patch'],
        detail=False,
        url_path='update-profile',
        permission_classes=(IsAuthenticated,),
    )
    def update_profile(self, request: DRFRequest) -> DRFResponse:
        '''Update the authenticated user's profile information. Permissions: Authenticated users only.'''

        user = request.user
        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info('Profile updated: %s', request.user.email)
        return DRFResponse(serializer.data, status=HTTP_200_OK)
