# cart\serializers.py
from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    # product_id = serializers.IntegerField(write_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "product_name", "quantity"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "session", "user", "created_at", "items"]
        # fields = ['id', 'items']
        unique_together = ("session", "user")


# Новый сериализатор ТОЛЬКО для remove_item
class RemoveItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True, help_text="ID товара")
    quantity = serializers.IntegerField(
        required=False,  # ← НЕ обязательно!
        min_value=1,
        help_text="Количество для удаления (по умолчанию — всё)",
    )


class AddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1, help_text="ID продукта")
    quantity = serializers.IntegerField(
        min_value=1, max_value=100, default=1, help_text="Количество (по умолчанию 1)"
    )

    # Опционально: валидация
    # def validate_product_id(self, value):
    #     from products.models import Product  # Импорт
    #     if not Product.objects.filter(id=value).exists():
    #         raise serializers.ValidationError("Продукт не найден")
    #     return value


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(max_length=500)
    phone = serializers.CharField(max_length=20)
    comment = serializers.CharField(required=False, allow_blank=True)
