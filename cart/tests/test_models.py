# cart/tests/test_models.py
import pytest
from django.contrib.sessions.models import Session
from django.utils import timezone

from cart.models import Cart, CartItem
from products.models import Product


@pytest.mark.django_db
class TestCartModel:
    """Тесты для модели Cart — корзина пользователя"""

    def test_cart_created_for_authenticated_user(self, user):
        """При создании корзины с пользователем — user заполняется, session=None"""
        cart = Cart.objects.create(user=user)

        assert cart.user == user
        assert cart.session is None
        assert cart.created_at is not None
        assert f"User: {user.email}" in str(cart)

    def test_cart_created_for_anonymous_via_session(self, rf):
        """Для анонима корзина привязывается к сессии"""
        request = rf.get("/")
        session = Session.objects.create(expire_date=timezone.now() + timezone.timedelta(days=1))

        cart = Cart.objects.create(session=session)

        assert cart.session == session
        assert cart.user is None
        assert "Anonymous" in str(cart)

    def test_one_cart_per_user(self, user):
        """OneToOneField — нельзя создать вторую корзину для одного пользователя"""
        Cart.objects.create(user=user)

        with pytest.raises(Exception):  # IntegrityError из-за OneToOne
            Cart.objects.create(user=user)

    def test_str_method_works_correctly(self, user):
        """__str__ отображает владельца"""
        cart1 = Cart.objects.create(user=user)
        cart2 = Cart.objects.create()  # анонимная

        assert str(cart1) == f"Cart {cart1.id} - User: {user.email}"
        assert "Anonymous" in str(cart2)


@pytest.mark.django_db
class TestCartItemModel:
    """Тесты для CartItem — товары в корзине"""

    def test_add_item_to_cart(self, user, product):
        """Можно добавить товар в корзину"""
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, product=product, quantity=3)

        assert item.cart == cart
        assert item.product == product
        assert item.quantity == 3

    def test_unique_together_cart_and_product(self, user, product):
        """Нельзя добавить один и тот же товар в корзину дважды — unique_together"""
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        with pytest.raises(Exception):  # IntegrityError
            CartItem.objects.create(cart=cart, product=product, quantity=5)

    def test_update_quantity_instead_of_duplicate(self, user, product):
        """Обычная логика: при добавлении товара — увеличиваем quantity"""
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, product=product, quantity=2)

        # Имитируем добавление ещё 3 шт
        item.quantity += 3
        item.save()

        assert CartItem.objects.filter(cart=cart).count() == 1
        assert CartItem.objects.get(cart=cart, product=product).quantity == 5

    def test_cart_items_related_name_works(self, user, product):
        """related_name="items" позволяет легко получить товары корзины"""
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        assert cart.items.count() == 1
        assert cart.items.first().product == product

    def test_delete_product_cascade_to_cartitem(self, user, product):
        """При удалении товара — удаляется и строка в корзине (on_delete=CASCADE)"""
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        assert CartItem.objects.count() == 1
        product.delete()
        assert CartItem.objects.count() == 0

    def test_cart_total_items_and_quantity(self, user, product_factory):
        """Удобная проверка: сколько товаров и общее количество"""
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product_factory(), quantity=2)
        CartItem.objects.create(cart=cart, product=product_factory(), quantity=3)
        CartItem.objects.create(cart=cart, product=product_factory(), quantity=1)

        assert cart.items.count() == 3
        total_qty = sum(item.quantity for item in cart.items.all())
        assert total_qty == 6


# Фикстуры
@pytest.fixture
def user(db):
    from main.models import ShopUser

    return ShopUser.objects.create_user(username="cartuser", email="cart@test.com", password="123")


@pytest.fixture
def product(db, user):
    return Product.objects.create(name="Test Product", price=999.00, created_by=user)


@pytest.fixture
def product_factory(db, user):
    """Фабрика для создания множества товаров"""

    def create_product(name="Product"):
        return Product.objects.create(name=name, price=100.00, created_by=user)

    return create_product
