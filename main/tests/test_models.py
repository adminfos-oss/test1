# main/tests/test_models.py
import pytest
from django.contrib.auth import get_user_model, authenticate
from django.db import IntegrityError

ShopUser = get_user_model()


@pytest.mark.django_db
class TestShopUserModel:
    """Тесты для ShopUser — адаптированы под текущую реализацию (без правок models.py)"""

    def test_create_user_success(self):
        """Можно создать пользователя с email и паролем"""
        user = ShopUser.objects.create_user(
            username="testuser", email="test@example.com", password="supersecret123"
        )
        assert user.pk is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.check_password("supersecret123")

    def test_create_superuser(self):
        """create_superuser работает"""
        admin = ShopUser.objects.create_superuser(
            username="admin", email="admin@shop.com", password="adminpass"
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_login_by_email_works_via_username_param(self):
        """Логин по email"""
        ShopUser.objects.create_user(
            username="john_doe", email="john@example.com", password="pass123"
        )

        assert authenticate(email="john@example.com", password="pass123") is not None

    def test_email_is_unique(self):
        """Email уникален — дубликат вызывает ошибку"""
        ShopUser.objects.create_user(username="u1", email="dup@example.com", password="pass")

        with pytest.raises(IntegrityError):
            ShopUser.objects.create_user(username="u2", email="dup@example.com", password="pass")

    def test_str_returns_email(self):
        """__str__ возвращает email"""
        user = ShopUser.objects.create_user(
            username="strtest", email="str@test.com", password="pass"
        )
        assert str(user) == "str@test.com"

    def test_auto_timestamps(self):
        """created_at и updated_at заполняются"""
        user = ShopUser.objects.create_user(username="time", email="time@test.com", password="pass")
        assert user.created_at is not None
        assert user.updated_at is not None


@pytest.mark.django_db
def test_authenticate_works():
    """authenticate работает с email"""
    ShopUser.objects.create_user(username="auth", email="auth@test.com", password="correct")

    user = authenticate(username="auth@test.com", password="correct")  # у тебя работает так
    assert user is not None
    assert user.email == "auth@test.com"

    # Неверный пароль
    assert authenticate(username="auth@test.com", password="wrong") is None
