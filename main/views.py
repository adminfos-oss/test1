"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from main.authenticate import token_validation_required
from main.serializers import LoginSerializer, SignupSerializer


@swagger_auto_schema(method='POST',
                     request_body=LoginSerializer,
                     responses={200: 'OK'}, tags=['Авторизация/Регистрация'])
@api_view(http_method_names=['POST'])
def login(request):
    serializer = LoginSerializer(data = request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        if not user:
            return Response({"Login error": request.data}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "action": "login",
            "username": user.username,
            "JWT": user.token
        }, status=status.HTTP_200_OK)
    return Response({"Bad request": request.data}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='POST',
    manual_parameters=[openapi.Parameter('JWT', openapi.IN_HEADER, description="your token", required=True, type=openapi.TYPE_STRING)],
    responses={200: 'OK'}, tags=['Авторизация/Регистрация'])
@api_view(http_method_names=['POST'])
@token_validation_required
def logout(request, *args, **kwargs):
    user = kwargs['user']
    user.save()
    return Response({"action": "logout", "username": user.username, }, status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST', request_body=SignupSerializer, responses={200: 'OK'}, tags=['Авторизация/Регистрация'])
@api_view(http_method_names=['POST'])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
        except:
            return Response({"Signup error": request.data}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "action": "signup",
            "username": user.username,
            "JWT": user.token
        }, status=status.HTTP_200_OK)
    return Response({"Bad request": request.data}, status=status.HTTP_400_BAD_REQUEST)

"""