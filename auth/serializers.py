# auth\serializers.py

from main.models import ShopUser
from rest_framework import serializers
from django.contrib.auth import authenticate


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = ShopUser
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        if ShopUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        user = ShopUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['email'],  # Поскольку USERNAME_FIELD = 'email'
            password=attrs['password']
        )
        if not user or not user.is_active:
            raise serializers.ValidationError("Неверные учетные данные")
        attrs['user'] = user
        return attrs