# products/tests/test_views.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from model_bakery import baker
from main.models import ShopUser

from products.models import Product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    u = baker.make(ShopUser)
    u.set_password("12345")
    u.save()
    return u


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestProductViewSet:

    # Публичные методы — работают без авторизации
    def test_list_public(self, api_client):
        baker.make(Product, _quantity=5)
        resp = api_client.get("/api/v1/products/")  # ←←← подправь роут, если у тебя другой
        assert resp.status_code == 200
        # Поддержка и с пагинацией, и без
        data = (
            resp.data["results"]
            if isinstance(resp.data, dict) and "results" in resp.data
            else resp.data
        )
        assert len(data) == 5

    def test_retrieve_public(self, api_client):
        p = baker.make(Product, name="iPhone 17")
        resp = api_client.get(f"/api/v1/products/{p.id}/")
        assert resp.status_code == 200
        assert resp.data["name"] == "iPhone 17"

    # Создание — только авторизованный + created_by = текущий пользователь
    def test_create_ok(self, auth_client, user):
        payload = {
            "name": "Товар от юзера",
            "description": "тест",
            "price": "1234.56",
            "amount": 10,
        }
        resp = auth_client.post("/api/v1/products/", payload, format="json")
        assert resp.status_code == 201
        assert Product.objects.get(pk=resp.data["id"]).created_by == user

    def test_create_unauthorized(self, api_client):
        resp = api_client.post("/api/v1/products/", {"name": "Хак"}, format="json")
        assert resp.status_code == 401

    # Обновление — только своего товара
    def test_update_own_product(self, auth_client, user):
        p = baker.make(Product, created_by=user)
        payload = {
            "name": "Обновлённое имя",
            "price": "999.99",
            "amount": 5,
            "description": "новое описание",
        }
        resp = auth_client.put(f"/api/v1/products/{p.id}/", payload, format="json")
        assert resp.status_code == 200
        p.refresh_from_db()
        assert p.name == "Обновлённое имя"

    # Удаление — только своего товара
    def test_delete_own_product(self, auth_client, user):
        p = baker.make(Product, created_by=user)
        resp = auth_client.delete(f"/api/v1/products/{p.id}/")
        assert resp.status_code == 204
        assert not Product.objects.filter(pk=p.id).exists()

    def test_update_foreign_product_404(self, auth_client, user):
        foreign = baker.make(Product, created_by=baker.make(ShopUser), description="чужой")
        payload = {
            "name": "Пытаюсь изменить чужой",
            "description": "desc",
            "price": "1.00",
            "amount": 1,
        }
        r = auth_client.put(f"/api/v1/products/{foreign.id}/", payload, format="json")
        assert r.status_code == 404

    def test_delete_foreign_product_404(self, auth_client, user):
        foreign = baker.make(Product, created_by=baker.make(ShopUser))
        r = auth_client.delete(f"/api/v1/products/{foreign.id}/")
        assert r.status_code == 404
        assert Product.objects.filter(pk=foreign.id).exists()  # товар остался!
