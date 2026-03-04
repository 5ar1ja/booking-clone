from typing import Any
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.viewsets import ViewSet
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action

from apps.users.serializers import UserLoginSerializer, UserRegistrationSerializer, CustomUserSerializer
# CustomUser импортируем только если используем его для типизации


class CustomUserViewSet(ViewSet):
    # По умолчанию — только для залогиненных
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
            
            # 1. Сохраняем юзера (вызывает метод create в сериализаторе)
            user = serializer.save() 
            
            # 2. Вместо ручного перечисления полей, берем данные из CustomUserSerializer
            # Это делает код вьюхи коротким, сколько бы полей ни было в модели.
            response_data = CustomUserSerializer(user).data
            
            return DRFResponse(data=response_data, status=201)

    @action(
        methods=("post",),
        detail=False,
        url_path="login",
        permission_classes=(AllowAny,),  # Разрешаем всем
    )
    def login(self, request: DRFRequest, *args: Any, **kwargs: Any) -> DRFResponse:
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return DRFResponse(
            data={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_landlord": user.is_landlord,
                "is_renter": user.is_renter,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=HTTP_200_OK,
        )

    @action(
        methods=["get"],
        detail=False,
        url_path="personal-info",  # В URL лучше использовать дефис
        # Здесь мы просто проверяем, что юзер залогинен.
        # Его роль проверится внутри данных.
        permission_classes=(IsAuthenticated,),
    )
    def fetch_personal_info(self, request: DRFRequest) -> DRFResponse:
        user = request.user
        return DRFResponse(
            data={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "avatar": user.avatar,
                "is_landlord": user.is_landlord,
                "is_renter": user.is_renter,
            },
            status=HTTP_200_OK,
        )
