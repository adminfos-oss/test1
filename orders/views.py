# orders/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Посмотреть заказ",
        operation_description="Возвращает список заказанных товаров пользователя",
        tags=['4. Заказы'],
    )
    def list(self, request, pk=None):
        pass

    def get_queryset(self):
        # Swagger спотыкается, если анонимный юзер
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')

    @swagger_auto_schema(auto_schema=None)
    def retrieve(self, request, pk=None):
        pass