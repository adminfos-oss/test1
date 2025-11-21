# products/tests/test_serializers.py
import pytest
from decimal import Decimal
from model_bakery import baker
from products.serializers import ProductSerializer


@pytest.mark.django_db
def test_serialize_with_baker():
    product = baker.make(
        "products.Product", name="Хурма", description="Синяя", price=Decimal("299.99"), amount=30
    )

    serializer = ProductSerializer(product)
    assert serializer.data["name"] == "Хурма"
    assert serializer.data["description"] == "Синяя"
    assert serializer.data["price"] == "299.99"
