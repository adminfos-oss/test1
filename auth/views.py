# auth\views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from .serializers import SignupSerializer, LoginSerializer


class SignupView(APIView):
    @swagger_auto_schema(
        request_body=LoginSerializer,  # Это ключевой параметр!
        tags=["1. Аутентификация"],
        operation_summary="Регистрация пользователя",
        responses={200: "Успех", 401: "Ошибка авторизации"},
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Пользователь успешно создан",
                    "user": {"id": user.pk, "username": user.username, "email": user.email},
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "token_type": "Bearer",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    @swagger_auto_schema(
        request_body=LoginSerializer,  # Это ключевой параметр!
        tags=["1. Аутентификация"],
        operation_summary="Вход в систему",
        responses={200: "Успех", 401: "Ошибка авторизации"},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Вход выполнен успешно",
                    "user": {"id": user.pk, "username": user.username, "email": user.email},
                    "access_token": "Bearer " + str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "token_type": "Bearer",
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    @swagger_auto_schema(
        request_body=LoginSerializer,
        tags=["1. Аутентификация"],
        operation_summary="Выход из аккаунта",
        responses={200: "Успех", 401: "Ошибка авторизации"},
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                raise TokenError("Refresh token required")

            # Черним токен (добавляем в blacklist)
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Выход выполнен успешно", "detail": "Токен заблокирован"},
                status=status.HTTP_205_RESET_CONTENT,
            )  # 205 для logout
        except TokenError as e:
            return Response(
                {"error": "Неверный или истекший refresh токен"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Ошибка при выходе"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
