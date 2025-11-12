# orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price_at_purchase', 'total_price']

    def get_total_price(self, obj):
        return obj.price_at_purchase * obj.quantity


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', 'updated_at',
                  'total_price', 'items', 'shipping_address', 'phone', 'comment']
        read_only_fields = ['status', 'created_at', 'updated_at', 'total_price']

