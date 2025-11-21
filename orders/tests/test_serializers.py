# orders/tests/test_serializers.py
import pytest
from decimal import Decimal

from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer, OrderItemSerializer
from products.models import Product


@pytest.mark.django_db
class TestOrderItemSerializer:
    """Тесты для OrderItemSerializer — строки заказа"""

    def test_total_price_calculated_correctly(self, user, product):
        """get_total_price правильно умножает цену на количество"""
        item = OrderItem.objects.create(
            order=Order.objects.create(user=user),
            product=product,
            quantity=3,
            price_at_purchase=Decimal("199.90"),
        )

        serializer = OrderItemSerializer(item)
        assert serializer.data["total_price"] == Decimal("599.70")
        assert serializer.data["quantity"] == 3
        assert serializer.data["price_at_purchase"] == "199.90"  # DRF возвращает str для Decimal

    def test_product_nested_serializer_works(self, user, product):
        """Поле product использует ProductSerializer и отдаёт полные данные товара"""
        item = OrderItem.objects.create(
            order=Order.objects.create(user=user),
            product=product,
            quantity=1,
            price_at_purchase=100,
        )

        serializer = OrderItemSerializer(item)
        product_data = serializer.data["product"]

        assert product_data["id"] == product.id
        assert product_data["name"] == product.name
        assert "price" in product_data
        assert "created_by" not in product_data  # если в ProductSerializer нет — ок

    def test_fields_are_correct(self, user, product):
        """Проверяем, что все нужные поля есть и лишних нет"""
        item = OrderItem.objects.create(
            order=Order.objects.create(user=user),
            product=product,
            quantity=2,
            price_at_purchase=150,
        )

        serializer = OrderItemSerializer(item)
        data = serializer.data

        expected_fields = {"product", "quantity", "price_at_purchase", "total_price"}
        assert set(data.keys()) == expected_fields


@pytest.mark.django_db
class TestOrderSerializer:
    """Тесты для OrderSerializer — основной сериализатор заказа"""

    def test_items_are_nested_and_serialized_correctly(self, user, product):
        """Поле items отдаёт список OrderItem с полным содержимым"""
        order = Order.objects.create(user=user, shipping_address="Москва")
        OrderItem.objects.create(order=order, product=product, quantity=2, price_at_purchase=100)
        OrderItem.objects.create(order=order, product=product, quantity=1, price_at_purchase=200)

        # Важно: пересчитываем сумму!
        order.recalculate_total()

        serializer = OrderSerializer(order)
        data = serializer.data

        assert len(data["items"]) == 2
        assert data["items"][0]["total_price"] == Decimal("200.00")  # 2 × 100
        assert data["items"][1]["total_price"] == Decimal("200.00")  # 1 × 200

    def test_total_price_comes_from_model_field(self, user, product):
        """total_price берётся из поля модели, а не считается заново"""
        order = Order.objects.create(user=user)
        OrderItem.objects.create(order=order, product=product, quantity=5, price_at_purchase=100)

        # Имитируем, что пересчёт произошёл
        order.total_price = Decimal("500.00")
        order.save(update_fields=["total_price"])

        serializer = OrderSerializer(order)
        assert Decimal(serializer.data["total_price"]) == Decimal("500.00")
        # assert serializer.data["total_price"] == "500.00"  # DRF → str

    def test_read_only_fields_cannot_be_set_on_create(self, user, product):
        """Поля read_only_fields не принимаются при создании/обновлении"""
        order = Order.objects.create(user=user)
        OrderItem.objects.create(order=order, product=product, quantity=1, price_at_purchase=100)
        order.recalculate_total()

        # Пытаемся "взломать" read_only поля
        malicious_data = {
            "status": "completed",
            "total_price": "99999.99",
            "created_at": "2020-01-01T00:00:00Z",
            "items": [],  # пытаемся очистить товары
        }

        serializer = OrderSerializer(order, data=malicious_data, partial=True)
        assert serializer.is_valid(), serializer.errors  # должно пройти валидацию
        updated_order = serializer.save()

        # Ничего из read_only не изменилось!
        assert updated_order.status == "new"  # осталось как было
        assert updated_order.total_price == Decimal("100.00")  # не 99999
        assert updated_order.created_at is not None
        assert updated_order.items.count() == 1  # items не очистились

    def test_all_expected_fields_present(self, user, product):
        """Проверяем полный список полей в ответе"""
        order = Order.objects.create(
            user=user,
            shipping_address="СПб, Невский пр.",
            phone="+79991234567",
            comment="Побыстрее пожалуйста",
        )
        OrderItem.objects.create(order=order, product=product, quantity=1, price_at_purchase=500)
        order.recalculate_total()

        serializer = OrderSerializer(order)
        data = serializer.data

        expected_fields = {
            "id",
            "status",
            "created_at",
            "updated_at",
            "total_price",
            "items",
            "shipping_address",
            "phone",
            "comment",
        }
        assert set(data.keys()) == expected_fields
        assert data["shipping_address"] == "СПб, Невский пр."
        assert data["comment"] == "Побыстрее пожалуйста"


# Фикстуры (можно вынести в conftest.py позже)
@pytest.fixture
def user(db):
    from main.models import ShopUser

    return ShopUser.objects.create_user(username="testuser", email="test@test.com", password="123")


@pytest.fixture
def product(db, user):
    return Product.objects.create(
        name="Смартфон Galaxy", price=Decimal("49990.00"), created_by=user
    )
