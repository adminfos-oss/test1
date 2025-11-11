# cart\models.py

from django.db import models
from django.contrib.sessions.models import Session


# Один пользователь — одна корзина. Для анонимных — привязываем к сессии.
class Cart(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, null=True, blank=True)
    user = models.OneToOneField('main.ShopUser', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} - User: {self.user or 'Anonymous'}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)  # твой продукт
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')