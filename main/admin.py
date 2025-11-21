from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from products.models import Product
from .models import ShopUser
from cart.models import Cart, CartItem


@admin.register(ShopUser)
class AdminShopUser(UserAdmin):
    model = ShopUser

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    class Meta:
        model = ShopUser
        fields = "__all__"

    def save_form(self, request, form, change):
        if not change:
            form.instance = self.model.objects.create_user(
                form.cleaned_data["username"],
                form.cleaned_data["email"],
                form.cleaned_data["password1"],
            )
        return super().save_form(request, form, change)


@admin.register(Product)
class AdminItem(admin.ModelAdmin):
    list_display = ["created_by", "created", "name", "price", "amount"]


admin.site.register([Cart, CartItem])
