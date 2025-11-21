# products/tests/test_models.py

import pytest
from decimal import Decimal

from django.utils import timezone
from django.db import IntegrityError

from main.models import ShopUser
from products.models import Product


@pytest.fixture
def shop_user(db):
    return ShopUser.objects.create(username="owner", email="o@example.com")


@pytest.mark.django_db
def test_product_creation(shop_user):
    product = Product.objects.create(
        name="iPhone 15",
        description="Крутой телефон",
        price=Decimal("999.99"),
        amount=10,
        created_by=shop_user,
    )
    assert product.name == "iPhone 15"
    assert product.price == Decimal("999.99")
    assert product.amount == 10
    assert product.created_by == shop_user
    assert product.created is not None


@pytest.mark.django_db
def test_product_str_method(shop_user):
    product = Product.objects.create(name="MacBook", price=1000, amount=5, created_by=shop_user)
    assert str(product) == "MacBook"


@pytest.mark.django_db
def test_ordering_by_created_desc(shop_user):
    """Тест сортировки: новые сверху (по убыванию created)"""
    p1 = Product.objects.create(name="Старый", price=100, amount=1, created_by=shop_user)
    p2 = Product.objects.create(name="Новый", price=200, amount=2, created_by=shop_user)

    # Меняем дату у старого товара (auto_now_add не даёт менять при создании)
    p1.created = timezone.make_aware(timezone.datetime(2020, 1, 1))  # ← ИСПРАВЛЕНО
    p1.save(update_fields=["created"])

    products = list(Product.objects.all())
    assert [p.name for p in products] == ["Новый", "Старый"]


@pytest.mark.django_db
def test_price_precision(shop_user):
    product = Product.objects.create(
        name="Дорогой товар",
        price=Decimal("1234567.89"),  # ровно 9 знаков
        amount=1,
        created_by=shop_user,
    )
    product.refresh_from_db()
    assert product.price == Decimal("1234567.89")


@pytest.mark.django_db
def test_amount_cannot_be_negative(shop_user):
    """PositiveIntegerField + null=False → должно кидать IntegrityError при отрицательном значении"""
    with pytest.raises(IntegrityError):  # ← ИСПРАВЛЕНО: IntegrityError, а не ValueError
        Product.objects.create(
            name="Минус",
            price=100,
            amount=-5,  # ← запрещено
            created_by=shop_user,
        )


@pytest.mark.django_db
def test_created_auto_now_add(shop_user):
    product = Product.objects.create(name="Тест", price=100, amount=1, created_by=shop_user)
    old_created = product.created
    product.name = "Обновлён"
    product.save()
    product.refresh_from_db()
    assert product.created == old_created  # дата не изменилась


@pytest.mark.django_db
def test_related_name_items_created(shop_user):
    Product.objects.create(name="Товар 1", price=100, amount=5, created_by=shop_user)
    Product.objects.create(name="Товар 2", price=200, amount=3, created_by=shop_user)
    assert shop_user.items_created.count() == 2
