from django.db import models

# class Item(models.Model):
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=9, decimal_places=2)
    amount = models.PositiveIntegerField(null=False)
    created_by = models.ForeignKey('main.ShopUser', related_name='items_created', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return self.name

