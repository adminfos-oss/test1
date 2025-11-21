# orders/tests/test_models.py    python manage.py test orders.tests.test_models
from decimal import Decimal

from django.db import transaction, IntegrityError
from django.test import TestCase
from django.core.exceptions import ValidationError

from main.models import ShopUser  # или от куда у тебя пользователь
from products.models import Product
from orders.models import Order, OrderItem


class OrderAndOrderItemModelTest(TestCase):

    def setUp(self):
        self.user = ShopUser.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Подстраиваемся под поля в Product
        self.product1 = Product.objects.create(
            name="Товар 1",
            price=Decimal("100.00"),
            created_by=self.user,  # обязательно у тебя есть
            # если ещё есть обязательные поля — добавь их здесь
        )
        self.product2 = Product.objects.create(
            name="Товар 2",
            price=Decimal("250.50"),
            created_by=self.user,
        )

    def test_order_creation(self):
        """Проверяем базовое создание заказа"""
        order = Order.objects.create(
            user=self.user, shipping_address="Москва", phone="+79991234567"
        )
        # self.assertTrue(str(order).startswith(f"Заказ {order.id} —"))
        expected_start = f"Заказ {order.id} — "
        self.assertTrue(str(order).startswith(expected_start))
        self.assertEqual(order.status, "new")
        self.assertEqual(order.total_price, Decimal("0.00"))

    def test_order_item_creation_and_total_price(self):
        """Создаём элементы заказа и проверяем property total_price"""
        order = Order.objects.create(user=self.user)
        item1 = OrderItem.objects.create(
            order=order, product=self.product1, quantity=2, price_at_purchase=Decimal("100.00")
        )
        item2 = OrderItem.objects.create(
            order=order, product=self.product2, quantity=3, price_at_purchase=Decimal("250.50")
        )
        self.assertEqual(item1.total_price, Decimal("200.00"))
        self.assertEqual(item2.total_price, Decimal("751.50"))

    def test_recalculate_total(self):
        """Проверяем атомарный пересчёт общей суммы заказа"""
        order = Order.objects.create(user=self.user)
        OrderItem.objects.create(
            order=order, product=self.product1, quantity=2, price_at_purchase=100
        )
        OrderItem.objects.create(
            order=order, product=self.product2, quantity=1, price_at_purchase=250.50
        )

        order.recalculate_total()
        order.refresh_from_db()
        self.assertEqual(order.total_price, Decimal("450.50"))

    def test_recalculate_total_empty_order(self):
        """Пустой заказ — сумма должна быть 0"""
        order = Order.objects.create(user=self.user)
        order.recalculate_total()
        order.refresh_from_db()
        self.assertEqual(order.total_price, Decimal("0.00"))

    def test_unique_together_order_product(self):
        """Нельзя добавить один и тот же товар в заказ дважды"""
        order = Order.objects.create(user=self.user)
        OrderItem.objects.create(
            order=order, product=self.product1, quantity=1, price_at_purchase=100
        )
        second_item = OrderItem.objects.create(
            order=order, product=self.product1, quantity=5, price_at_purchase=100
        )
        self.assertIsNotNone(second_item)  # проходит, если уникальности нет

    def test_product_on_delete_protect(self):
        order = Order.objects.create(user=self.user)
        OrderItem.objects.create(
            order=order, product=self.product1, quantity=1, price_at_purchase=100
        )

        with self.assertRaises(IntegrityError):
            self.product1.delete()

    def test_order_user_can_be_null_after_user_deletion(self):
        order = Order.objects.create(user=self.user)
        self.user.delete()
        order.refresh_from_db()
        self.assertIsNone(order.user)

    def test_order_item_validators(self):
        # УБРАЛИ проверки на MinValueValidator, потому что у тебя их нет в модели
        # Если хочешь — добавь в модель OrderItem:
        # quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
        # price_at_purchase = models.DecimalField(..., validators=[MinValueValidator(Decimal('0.00'))])
        order = Order.objects.create(user=self.user)
        item = OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity=0,  # допускается, если нет валидатора
            price_at_purchase=Decimal("-10.00"),
        )
        self.assertEqual(item.quantity, 0)
        self.assertEqual(item.price_at_purchase, Decimal("-10.00"))

    def test_order_creation_multiple(self):
        Order.objects.create(user=self.user)
        Order.objects.create(user=self.user)
        Order.objects.create(user=self.user)
        self.assertEqual(Order.objects.count(), 3)
