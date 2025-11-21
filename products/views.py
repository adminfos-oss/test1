# products/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Product
from .serializers import ProductSerializer
import logging


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # Динамические разрешения — ключевой момент
    def get_permissions(self):
        """
        Только list — публичный (AllowAny)
        Все остальные действия (create, retrieve, update, destroy) — только для авторизованных
        """
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]  # Всё остальное — только авторизованные

    @swagger_auto_schema(
        operation_summary="Получить каталог товаров",
        operation_description="Список товаров в интернет-магазине",
        tags=["2. Товары"],
    )
    def list(self, request, *args, **kwargs):
        self.queryset = Product.objects.all()

        total_count = self.queryset.count()
        user = self.request.user if hasattr(self.request, "user") else None
        username = user.username if user and user.is_authenticated else "Anonymous"
        user_id = user.id if user and user.is_authenticated else None
        ip = (
            self.request.META.get("REMOTE_ADDR", "unknown")
            if hasattr(self.request, "META")
            else "unknown"
        )

        # Основная запись в лог — всегда полезно знать, кто и сколько видит
        api_logger = logging.getLogger("api_requests")
        api_logger.info(
            "LIST request | view=%s | user=%s (id=%s) | ip=%s | total_products=%d | ",
            self.__class__.__name__,
            username,
            user_id,
            ip,
            total_count,
            extra={"request": request},  # опционально, если потом захочешь фильтры по request
        )

        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Получить отдельный товар",
        operation_description="Доступно для всех пользователей",
        tags=["2. Товары"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return Product.objects.filter(created_by=self.request.user)
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()
        return Product.objects.all()

    @swagger_auto_schema(
        operation_summary="Добавить товар в каталог",
        operation_description="Добавление товара в каталог только авторизованным пользователем",
        tags=["2. Товары"],  # Опционально: тег для группировки
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)  # Передаём полный объект user, не PK

    @swagger_auto_schema(
        operation_summary="Удалить отдельный товар",
        operation_description="Доступно для авторизованных пользователей",
        tags=["2. Товары"],
    )
    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        self.queryset = self.filter_queryset(Product.objects.filter(created_by=user))
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="Обновить отдельный товар",
        operation_description="Доступно для авторизованных пользователей. Обновить можно только свой товар.",
        tags=["2. Товары"],
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user = self.request.user
        request.data["created_by"] = user.pk
        self.queryset = self.filter_queryset(Product.objects.filter(created_by=user))
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data, status=status.HTTP_200_OK)

    # --- Скрываем от Сваггера ----
    @swagger_auto_schema(auto_schema=None)
    def partial_update(self, request, *args, **kwargs):
        pass
