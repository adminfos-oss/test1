# cart/tests/test_views.py
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from cart.models import Cart, CartItem
from orders.models import Order
from products.models import Product


@pytest.mark.django_db
class TestCartViewSet:
    """Тесты для CartViewSet"""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        self.client = api_client
        self.product1 = Product.objects.create(
            name="Товар 1", price=Decimal("100.00"), created_by=admin_user
        )
        self.product2 = Product.objects.create(
            name="Товар 2", price=Decimal("250.00"), created_by=admin_user
        )

    # === Вспомогательные методы ===
    def auth_client(self, user):
        """Авторизует клиента по JWT"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    # === Тесты ===
    def test_anonymous_can_add_to_cart(self, user_factory, rf):
        """Аноним добавляет товар → создаётся корзина по сессии"""
        request = rf.post("/")
        request.session = self.client.session
        request.session.save()

        self.client.post(reverse("cart-add-item"), {"product_id": self.product1.id, "quantity": 2})

        assert Cart.objects.filter(session__session_key=request.session.session_key).exists()
        cart = Cart.objects.get(session__session_key=request.session.session_key)
        assert cart.items.count() == 1
        assert cart.items.first().quantity == 2

    def test_authenticated_user_gets_own_cart(self, user):
        """Авторизованный пользователь видит свою корзину"""
        self.auth_client(user)
        Cart.objects.create(user=user)  # пустая корзина

        response = self.client.get(reverse("cart-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"] == user.id

    def test_merge_anonymous_cart_on_login(self, user, rf):
        """Аноним добавил товары → залогинился → товары перенеслись в его корзину"""
        # 1. Аноним добавляет товары
        request = rf.post("/")
        request.session = self.client.session
        request.session.save()
        session_key = request.session.session_key

        self.client.post(reverse("cart-add-item"), {"product_id": self.product1.id, "quantity": 3})
        anon_cart = Cart.objects.get(session__session_key=session_key)
        assert anon_cart.items.count() == 1

        # Создаём "старую" корзину у пользователя (чтобы сработал merge и delete)
        Cart.objects.create(user=user)  # пустая корзина у пользователя

        # 2. Логинимся
        self.auth_client(user)

        # 3. Запрашиваем корзину — должен сработать merge
        response = self.client.get(reverse("cart-list"))
        assert response.status_code == 200

        # Корзина теперь у пользователя
        user_cart = Cart.objects.get(user=user)
        assert user_cart.items.count() == 1
        assert user_cart.items.first().quantity == 3

        # Анонимная корзина удалена
        assert not Cart.objects.filter(session__session_key=session_key).exists()

    def test_add_item_creates_or_updates(self, user):
        """Добавление товара: первый раз — создаёт, второй — обновляет количество"""
        self.auth_client(user)
        cart = Cart.objects.create(user=user)

        # Первый раз
        resp1 = self.client.post(
            reverse("cart-add-item"), {"product_id": self.product1.id, "quantity": 2}
        )
        assert resp1.status_code == 201
        assert CartItem.objects.get(cart=cart, product=self.product1).quantity == 2

        # Второй раз — обновляем
        resp2 = self.client.post(
            reverse("cart-add-item"), {"product_id": self.product1.id, "quantity": 5}
        )
        assert resp2.status_code == 200
        assert CartItem.objects.get(cart=cart, product=self.product1).quantity == 5

    def test_remove_item_deletes_or_reduces(self, user):
        self.auth_client(user)
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=10)

        # Удаляем частично (если будет RemoveItemSerializer с quantity)
        # Пока у тебя удаление полное — проверяем полное удаление
        response = self.client.delete(reverse("cart-remove-item"), {"product_id": self.product1.id})
        assert response.status_code == 200
        assert not cart.items.exists()

    def test_clear_cart_empties_all_items(self, user):
        self.auth_client(user)
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)

        response = self.client.delete(reverse("cart-clear"))
        assert response.status_code == 200
        assert cart.items.count() == 0

    def test_checkout_creates_order_and_clears_cart(self, user):
        self.auth_client(user)
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)

        checkout_data = {
            "shipping_address": "Москва, Тестовая 1",
            "phone": "+79991234567",
            "comment": "Быстрее!",
        }

        response = self.client.post(reverse("cart-checkout"), checkout_data)
        assert response.status_code == 201

        # Заказ создан
        order = Order.objects.get(user=user)
        assert order.shipping_address == checkout_data["shipping_address"]
        assert order.items.count() == 2
        assert Decimal(order.total_price) == Decimal("450.00")  # 2*100 + 1*250

        # Корзина очищена
        assert cart.items.count() == 0

    def test_checkout_empty_cart_returns_400(self, user):
        self.auth_client(user)
        Cart.objects.create(user=user)  # пустая

        response = self.client.post(
            reverse("cart-checkout"), {"shipping_address": "Адрес", "phone": "+79991234567"}
        )
        assert response.status_code == 400
        assert "Корзина пуста" in str(response.data)


# === Фикстуры ===
@pytest.fixture
def admin_user(db):
    from main.models import ShopUser

    return ShopUser.objects.create_user(
        username="adminshop", email="admin@shop.com", password="admin123"
    )


@pytest.fixture
def product1(admin_user):
    return Product.objects.create(name="Товар 1", price=Decimal("100.00"), created_by=admin_user)


@pytest.fixture
def product2(admin_user):
    return Product.objects.create(name="Товар 2", price=Decimal("250.00"), created_by=admin_user)


@pytest.fixture
def user_factory(db):
    from main.models import ShopUser

    def create(**kwargs):
        return ShopUser.objects.create_user(
            username=kwargs.get("username", "testuser"),
            email=kwargs.get("email", "test@test.com"),
            password="pass123",
        )

    return create


@pytest.fixture
def user(user_factory):
    return user_factory()


@pytest.fixture
def api_client():
    """Возвращает DRF APIClient с методами .credentials() и .force_authenticate()"""
    return APIClient()
