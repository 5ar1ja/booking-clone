from typing import Any
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.viewsets import ViewSet
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action

from apps.users.serializers import (
    UserLoginSerializer,
    UserRegistrationSerializer,
    CustomUserSerializer,
    PersonalInfoSerializer,
    UpdateProfileSerializer,
)


class CustomUserViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(
        methods=["post"],
        detail=False,
        url_path="register",
        permission_classes=(AllowAny,),
    )
    def register(self, request: DRFRequest):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        response_data = CustomUserSerializer(user).data

        return DRFResponse(data=response_data, status=HTTP_201_CREATED)

    @action(
        methods=("post",),
        detail=False,
        url_path="login",
        permission_classes=(AllowAny,),
    )
    def login(self, request: DRFRequest, *args: Any, **kwargs: Any) -> DRFResponse:
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        response_data = UserLoginSerializer(user).data

        return DRFResponse(
            data={
                **response_data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=HTTP_200_OK,
        )

    @action(
        methods=["get"],
        detail=False,
        url_path="personal-info",
        permission_classes=(IsAuthenticated,),
    )
    def fetch_personal_info(self, request: DRFRequest) -> DRFResponse:
        user = request.user

        response_data = PersonalInfoSerializer(user).data
        return DRFResponse(data=response_data, status=HTTP_200_OK)

    @action(
        methods=["patch"],
        detail=False,
        url_path="update-profile",
        permission_classes=(IsAuthenticated,),
    )
    def update_profile(self, request: DRFRequest) -> DRFResponse:
        user = request.user

        serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_user = serializer.save()

        return DRFResponse(data=serializer.data, status=HTTP_200_OK)
