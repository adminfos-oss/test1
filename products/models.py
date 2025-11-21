# products/models.py
from __future__ import annotations

from django.db import models


class Product(models.Model):
    """Модель товара в магазине.

    Представляет отдельный товар, который может быть добавлен продавцом
    и куплен покупателем.

    Attributes:
        name: Название товара (максимум 200 символов).
        description: Полное описание товара. Может содержать HTML-разметку.
        price: Цена товара в валюте магазина (до 999 999.99).
        amount: Количество единиц товара на складе.
        created_by: Продавец (пользователь типа ShopUser), который добавил товар.
        created: Дата и время создания записи (автоматически).

    Examples:
        >>> product = Product.objects.create(
        ...     name="iPhone 15 Pro",
        ...     description="Новый телефон от Apple",
        ...     price=1299.99,
        ...     amount=10,
        ...     created_by=user
        ... )
    """

    name = models.CharField(
        max_length=200,
        verbose_name="название товара",
        help_text="Короткое название, отображается в каталоге и на карточке товара",
    )
    description = models.TextField(
        verbose_name="описание",
        help_text="Полное описание товара, можно использовать Markdown или HTML",
        blank=True,
    )
    price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        verbose_name="цена",
        help_text="Цена за одну единицу товара",
    )
    amount = models.PositiveIntegerField(
        verbose_name="количество на складе",
        default=0,
        help_text="Сколько единиц товара сейчас в наличии",
    )
    created_by = models.ForeignKey(
        "main.ShopUser",
        related_name="items_created",
        on_delete=models.CASCADE,
        verbose_name="продавец",
        help_text="Пользователь, который добавил этот товар",
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="дата добавления",
    )

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["-created"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self) -> str:
        """Возвращает человекочитаемое название товара."""
        return self.name

    def clean(self) -> None:
        """Валидация модели перед сохранением."""
        if self.price < 0:
            raise ValueError("Цена не может быть отрицательной")
        if self.amount < 0:
            raise ValueError("Количество не может быть отрицательным")

    def is_available(self) -> bool:
        """Проверяет, есть ли товар в наличии.

        Returns:
            True, если количество больше нуля.
        """
        return self.amount > 0

    # Если хочешь, чтобы эти методы тоже попали в документацию Sphinx:
    is_available.boolean = True  # для красивой иконки в админке и docs
