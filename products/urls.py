# products/urls.py)

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Импорт вашего ViewSet
from .views import ProductViewSet

# Создаём роутер (автоматически генерирует все CRUD-эндпоинты)
router = DefaultRouter()
router.register(
    r"products", ProductViewSet, basename="product"
)  # basename обязателен, если в модели нет queryset

urlpatterns = [
    # Подключаем все маршруты от роутера
    # GET    /products/          → list
    # POST   /products/          → create
    # GET    /products/<pk>/     → retrieve
    # PUT    /products/<pk>/     → update
    # PATCH  /products/<pk>/     → partial_update
    # DELETE /products/<pk>/     → destroy
    path("", include(router.urls)),
]
