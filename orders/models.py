# orders/models.py

from django.db import models


class Order(models.Model):
    STATUS_CHOICES = (
        ('new', 'Новый'),
        ('completed', 'Завершён'),
        ('canceled', 'Отменён'),
    )

    # Кому принадлежит заказ
    user = models.ForeignKey(
        'main.ShopUser', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='orders'
    )

    # Информация о заказе
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    # Цена (можно посчитать на лету, но хранить удобно)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Доставка / контактные данные
    shipping_address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"Заказ {self.id} — {self.user}"

    # Удобный метод — пересчитать сумму
    def recalculate_total(self):
        self.total_price = sum(item.total_price for item in self.items.all())
        self.save(update_fields=['total_price'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)  # цена на момент покупки

    def __str__(self):
        return f"{self.product} × {self.quantity}"

    @property
    def total_price(self):
        return self.price_at_purchase * self.quantity