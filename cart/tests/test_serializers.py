# cart/tests/test_serializers.py
import pytest
from django.contrib.auth import get_user_model

from cart.models import Cart, CartItem
from cart.serializers import (
    CartSerializer,
    CartItemSerializer,
    AddItemSerializer,
    RemoveItemSerializer,
    CheckoutSerializer,
)
from products.models import Product


User = get_user_model()


@pytest.mark.django_db
class TestCartItemSerializer:
    """Тесты для CartItemSerializer — строка корзины в ответе"""

    def test_contains_expected_fields(self, cart_with_items):
        """Проверяем, что отдаются все нужные поля"""
        item = cart_with_items.items.first()
        serializer = CartItemSerializer(item)

        data = serializer.data
        expected_fields = {"id", "product_id", "product_name", "quantity"}
        assert set(data.keys()) == expected_fields

    def test_product_name_from_product_model(self, cart_with_items):
        """product_name берётся из product.name"""
        item = cart_with_items.items.first()
        serializer = CartItemSerializer(item)

        assert serializer.data["product_name"] == item.product.name

    def test_product_id_is_readable(self, cart_with_items):
        """product_id отдаётся (хотя write_only не указан, но по умолчанию readable)"""
        item = cart_with_items.items.first()
        serializer = CartItemSerializer(item)

        assert serializer.data["product_id"] == item.product.id


@pytest.mark.django_db
class TestCartSerializer:
    """Тесты для CartSerializer — полная корзина"""

    def test_items_nested_correctly(self, cart_with_items):
        """items — вложенный список с CartItemSerializer"""
        serializer = CartSerializer(cart_with_items)
        data = serializer.data

        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 2  # у нас 2 товара в фикстуре

    def test_user_and_session_included(self, user, anonymous_cart):
        """Для авторизованного — user, для анонима — session"""
        cart_auth = Cart.objects.create(user=user)
        serializer_auth = CartSerializer(cart_auth).data

        assert serializer_auth["user"] == user.id
        assert serializer_auth["session"] is None

        serializer_anon = CartSerializer(anonymous_cart).data
        assert serializer_anon["user"] is None
        assert serializer_anon["session"] is not None


@pytest.mark.django_db
class TestAddItemSerializer:
    """Тесты для AddItemSerializer — добавление товара"""

    def test_valid_data_passes(self):
        """Корректные данные проходят валидацию"""
        data = {"product_id": 1, "quantity": 5}
        serializer = AddItemSerializer(data=data)
        assert serializer.is_valid()

        assert serializer.validated_data["product_id"] == 1
        assert serializer.validated_data["quantity"] == 5

    def test_quantity_default_is_1(self):
        """Если quantity не передан — дефолт 1"""
        data = {"product_id": 999}
        serializer = AddItemSerializer(data=data)
        assert serializer.is_valid()

        assert serializer.validated_data["quantity"] == 1

    def test_quantity_min_value_1(self):
        """quantity не может быть 0 или отрицательным"""
        data = {"product_id": 1, "quantity": 0}
        serializer = AddItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors

        data = {"product_id": 1, "quantity": -5}
        serializer = AddItemSerializer(data=data)
        assert not serializer.is_valid()

    def test_quantity_max_value_100(self):
        """quantity не больше 100"""
        data = {"product_id": 1, "quantity": 101}
        serializer = AddItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors

    def test_product_id_required(self):
        """product_id обязателен"""
        data = {"quantity": 3}
        serializer = AddItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "product_id" in serializer.errors


@pytest.mark.django_db
class TestRemoveItemSerializer:
    """Тесты для RemoveItemSerializer — удаление/уменьшение товара"""

    def test_product_id_required(self):
        """product_id обязателен"""
        data = {"quantity": 2}
        serializer = RemoveItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "product_id" in serializer.errors

    def test_quantity_min_value_1_when_provided(self):
        """Если quantity передан — минимум 1"""
        data = {"product_id": 1, "quantity": 0}
        serializer = RemoveItemSerializer(data=data)
        assert not serializer.is_valid()

        data = {"product_id": 1, "quantity": 3}
        serializer = RemoveItemSerializer(data=data)
        assert serializer.is_valid()


@pytest.mark.django_db
class TestCheckoutSerializer:
    """Тесты для CheckoutSerializer — оформление заказа"""

    def test_required_fields(self):
        """shipping_address и phone обязательны"""
        data = {
            "shipping_address": "Москва, ул. Тестовая, д.1",
            "phone": "+79991234567",
        }
        serializer = CheckoutSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_shipping_address(self):
        data = {"phone": "+79991234567"}
        serializer = CheckoutSerializer(data=data)
        assert not serializer.is_valid()
        assert "shipping_address" in serializer.errors

    def test_comment_optional(self):
        data = {
            "shipping_address": "СПб",
            "phone": "89999999999",
            "comment": "Побыстрее пожалуйста!",
        }
        serializer = CheckoutSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["comment"] == "Побыстрее пожалуйста!"

        # Без comment — тоже ок
        del data["comment"]
        serializer = CheckoutSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data.get("comment", "") == ""


# === Фикстуры ===
@pytest.fixture
def user(db):
    return User.objects.create_user(username="cartuser", email="cart@test.com", password="123")


@pytest.fixture
def product(db, user):
    return Product.objects.create(name="Тестовый товар", price=999.00, created_by=user)


@pytest.fixture
def cart_with_items(user, product):
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=2)
    # Добавим ещё один товар
    product2 = Product.objects.create(name="Ещё товар", price=500, created_by=user)
    CartItem.objects.create(cart=cart, product=product2, quantity=1)
    return cart


@pytest.fixture
def anonymous_cart(db):
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    session = Session.objects.create(expire_date=timezone.now() + timezone.timedelta(days=30))
    return Cart.objects.create(session=session)
