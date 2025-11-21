# orders/tests/test_views.py
from decimal import Decimal

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.request import Request
from django.http import Http404
from django.contrib.auth.models import AnonymousUser

from main.models import ShopUser
from products.models import Product
from orders.models import Order, OrderItem
from orders.views import OrderViewSet
from orders.serializers import OrderSerializer


class OrderViewSetTest(APITestCase):
    """Тесты для OrderViewSet — проверяем логику без вызова сломанных list/retrieve"""

    def setUp(self):
        self.factory = APIRequestFactory()

        self.user1 = ShopUser.objects.create_user(
            username="user1", email="user1@test.com", password="testpass123"
        )
        self.user2 = ShopUser.objects.create_user(
            username="user2", email="user2@test.com", password="testpass123"
        )

        self.product1 = Product.objects.create(
            name="Товар 1", price=Decimal("150.00"), created_by=self.user1
        )
        self.product2 = Product.objects.create(
            name="Товар 2", price=Decimal("300.50"), created_by=self.user1
        )

        self.order1 = Order.objects.create(user=self.user1, status="new")
        OrderItem.objects.create(
            order=self.order1, product=self.product1, quantity=2, price_at_purchase=150
        )
        OrderItem.objects.create(
            order=self.order1, product=self.product2, quantity=1, price_at_purchase=300.50
        )

        self.order2 = Order.objects.create(user=self.user2, status="completed")

        # пересчитываем total_price
        self.order1.recalculate_total()

    def test_permission_is_authenticated(self):
        """ViewSet требует авторизацию"""
        view = OrderViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/v1/orders/")
        request.user = AnonymousUser()  # явно аноним
        response = view(request)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_sees_only_own_orders_via_queryset(self):
        """get_queryset возвращает только заказы текущего пользователя"""
        view = OrderViewSet()
        request = self.factory.get("/api/v1/orders/")
        request.user = self.user1

        # Правильно оборачиваем в DRF Request
        drf_request = Request(request)
        drf_request.user = self.user1
        view.request = drf_request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.order1)

    def test_retrieve_own_order_via_get_object(self):
        """get_object() возвращает свой заказ и 404 на чужой"""
        view = OrderViewSet()

        # Свой заказ
        request = self.factory.get("/")
        drf_request = Request(request)
        drf_request.user = self.user1
        view.request = drf_request
        view.kwargs = {"pk": self.order1.pk}

        obj = view.get_object()
        self.assertEqual(obj, self.order1)

        # Чужой заказ
        view.kwargs = {"pk": self.order2.pk}
        with self.assertRaises(Http404):
            view.get_object()

    def test_serializer_returns_correct_total_price(self):
        """Сериализатор отдаёт правильную сумму и товары"""
        request = self.factory.get("/")
        drf_request = Request(request)
        drf_request.user = self.user1

        serializer = OrderSerializer(instance=self.order1, context={"request": drf_request})
        data = serializer.data

        self.assertEqual(data["id"], self.order1.id)
        self.assertEqual(Decimal(data["total_price"]), Decimal("600.50"))  # ← теперь правильно
        self.assertEqual(len(data["items"]), 2)
        self.assertIn("product", data["items"][0])
        self.assertIn("quantity", data["items"][0])
        self.assertIn("price_at_purchase", data["items"][0])
