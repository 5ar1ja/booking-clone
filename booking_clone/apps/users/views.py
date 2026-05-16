import logging

# Third-party modules
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

# Project modules
from apps.users.serializers import (
    LoginResponseSerializer,
    UserLoginSerializer,
    UserReadSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
)

logger = logging.getLogger('apps.users')


@extend_schema_view(
    register=extend_schema(
        summary="Register a new user",
        description=(
            "Create a new user account as either a Landlord or a Renter. "
            "Permissions: AllowAny."
        ),
        request=UserRegistrationSerializer,
        responses={201: UserReadSerializer},
    ),
    login=extend_schema(
        summary="User login",
        description=(
            "Authenticate user with email and password and return JWT tokens. "
            "Permissions: AllowAny."
        ),
        request=UserLoginSerializer,
        responses={200: LoginResponseSerializer},
    ),
    fetch_personal_info=extend_schema(
        summary="Get personal info",
        description=(
            "Retrieve current authenticated user's profile details. "
            "Permissions: Authenticated only."
        ),
        responses={200: UserReadSerializer},
    ),
    update_profile=extend_schema(
        summary="Update profile",
        description=(
            "Partially update current authenticated user's profile. "
            "Permissions: Authenticated only."
        ),
        request=UserUpdateSerializer,
        responses={200: UserReadSerializer},
    ),
)
class CustomUserViewSet(ViewSet):
    '''Handles user registration, login, and profile management using ViewSet.'''

    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)

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
        read_serializer = UserReadSerializer(user, context={'request': request})
        return DRFResponse(data=read_serializer.data, status=HTTP_201_CREATED)

    @action(
        methods=('post',),
        detail=False,
        url_path='login',
        permission_classes=(AllowAny,),
    )
    def login(self, request: DRFRequest) -> DRFResponse:
        '''Authenticate user and return JWT tokens along with user info.'''

        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        logger.info('User logged in: %s', user.email)
        refresh = RefreshToken.for_user(user)

        response_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_landlord': user.is_landlord,
            'is_renter': user.is_renter,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
        return DRFResponse(data=response_data, status=HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='personal-info',
        permission_classes=(IsAuthenticated,),
    )
    def fetch_personal_info(self, request: DRFRequest) -> DRFResponse:
        '''Fetch the authenticated user's personal information.'''

        user = request.user
        serializer = UserReadSerializer(user, context={'request': request})
        return DRFResponse(data=serializer.data, status=HTTP_200_OK)

    @action(
        methods=['patch'],
        detail=False,
        url_path='update-profile',
        permission_classes=(IsAuthenticated,),
    )
    def update_profile(self, request: DRFRequest) -> DRFResponse:
        '''Update the authenticated user's profile information.'''

        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info('Profile updated: %s', request.user.email)

        read_serializer = UserReadSerializer(user, context={'request': request})
        return DRFResponse(read_serializer.data, status=HTTP_200_OK)
