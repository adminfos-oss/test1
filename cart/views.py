#  cart/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.sessions.models import Session
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi  # Для схем
from django.db import transaction
from .models import Cart, CartItem
from orders.models import Order, OrderItem
from .serializers import CartSerializer, AddItemSerializer, CheckoutSerializer
from orders.serializers import OrderSerializer, OrderItemSerializer
from products.models import Product

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # Динамические разрешения — ключевой момент
    def get_permissions(self):
        """
        Только list, add_item — публичные (AllowAny)
        Все остальные действия только для авторизованных
        """
        if self.action in ['list', 'add_item']:
            return [AllowAny()]
        return [IsAuthenticated()]  # Всё остальное — только авторизованные

    def get_queryset(self):
        """
        Возвращает только корзину текущего пользователя или сессии
        """
        if not self.request.session.session_key:
            self.request.session.create()
        session_key = self.request.session.session_key

        user = self.request.user if self.request.user.is_authenticated else None
        if user:  # Авторизован: только по user (с merge сессии в _attach)
            queryset = Cart.objects.filter(user=user)
        else:  # Аноним: ТОЛЬКО по сессии!
            queryset = Cart.objects.filter(session__session_key=session_key)

        # Привязка/объединение (если авторизован)
        if user:
            self._attach_cart_to_user(session_key, user)

        return queryset.distinct()

    def _attach_cart_to_user(self, session_key, user):
        """
        Привязывает анонимную корзину к пользователю и объединяет дубли
        """
        session_cart = Cart.objects.filter(session__session_key=session_key).first()
        # session_cart = Cart.objects.filter(session_key=session_key).first()
        user_cart = Cart.objects.filter(user=user, session__session_key__isnull=True).first()
        # user_cart = Cart.objects.filter(user=user, session_key__isnull=True).first()

        if session_cart and not session_cart.user:
            if user_cart and user_cart != session_cart:
                # Объединяем
                self._merge_carts(session_cart, user_cart)
                session_cart.delete()
            else:
                session_cart.user = user
                session_cart.save()

    def _merge_carts(self, from_cart, to_cart):
        """Переносит товары из одной корзины в другую"""
        for item in from_cart.items.all():
            existing, _ = to_cart.items.update_or_create(
                product=item.product,
                defaults={'quantity': item.quantity}
            )
            if not _:
                existing.quantity += item.quantity
                existing.save()

    def get_cart(self):
        """
        Возвращает текущую корзину (по сессии или пользователю)
        """
        queryset = self.get_queryset()
        cart = queryset.first()
        if not cart:
            # Создаём новую
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key

            session = Session.objects.get(session_key=session_key)

            cart = Cart.objects.create(
                session=session,
                user=self.request.user if self.request.user.is_authenticated else None
            )
        return cart


    # === Действия ===
    @swagger_auto_schema(
        operation_summary="Получить корзину",
        operation_description="Возвращает корзину текущего пользователя",
        tags=['3. Корзина'],  # Опционально: тег для группировки
    )
    def list(self, request, *args, **kwargs):
        cart = self.get_cart()
        serializer = self.get_serializer(cart)
        print(f"serializer.data: {serializer.data}")
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Добавить товар в корзину",
        operation_description="Добавляет или обновляет товар в корзине по product_id и quantity",
        request_body=AddItemSerializer,  # ← Body-параметры!
        responses={
            201: CartSerializer,  # Успех: данные корзины
            400: openapi.Response('Ошибка валидации', AddItemSerializer), # Ошибка
        },
        tags=['3. Корзина'],  # Опционально: тег для группировки
    )
    @action(detail=False, methods=['post'])
    def add_item(self, request, *args, **kwargs):
        cart = self.get_cart()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if not product_id:
            return Response({"error": "product_id is required"}, status=400)

        if quantity <= 0:
            return Response({"error": "quantity must be positive"}, status=400)

        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.update_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        return Response(self.get_serializer(cart).data, status=201 if created else 200)


    @swagger_auto_schema(
        operation_summary="Удалить товар из корзины",
        operation_description="Удаляет товар из корзины",
        request_body=AddItemSerializer,  # ← Body-параметры!
        responses={
            201: CartSerializer,  # Успех: данные корзины
            400: openapi.Response('Ошибка валидации', AddItemSerializer),  # Ошибка
        },
        tags=['3. Корзина'],
    )
    @action(detail=False, methods=['delete'])
    def remove_item(self, request, *args, **kwargs):
        cart = self.get_cart()
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "product_id is required"}, status=400)

        product = get_object_or_404(Product, id=product_id)
        deleted, _ = cart.items.filter(product=product).delete()
        if not deleted:
            return Response({"error": "Item not in cart"}, status=404)

        return Response(self.get_serializer(cart).data)

    @swagger_auto_schema(
        operation_summary="Очистить корзину",
        operation_description="Удаление всех товаров из корзины. ",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={},  # пустые свойства = пустое тело
            # description="Этот эндпоинт не принимает тело запроса"
        ),
        responses={
            200: CartSerializer,  # Успех: обновлённая корзина
            401: 'Не авторизован',
            404: 'Корзина не найдена',
        },
        tags=['3. Корзина'],
    )
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        cart = self.get_cart()
        cart.items.all().delete()
        return Response(self.get_serializer(cart).data)


    @swagger_auto_schema(
        operation_summary="Оформить заказ",
        operation_description="Оформление заказа на товары из корзины",
        request_body=CheckoutSerializer,  # ← Body-параметры!
        responses={
            201: CheckoutSerializer,
            400: openapi.Response('Ошибка валидации', CheckoutSerializer),  # Ошибка
        },
        tags=['3. Корзина'],
    )
    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        cart = request.user.cart

        if not cart.items.exists():
            return Response({"error": "Корзина пуста"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                shipping_address=serializer.validated_data['shipping_address'],
                phone=serializer.validated_data['phone'],
                comment=serializer.validated_data.get('comment', ''),
            )

            total = 0
            for item in cart.items.select_related('product'):
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_purchase=item.product.price,
                )
                total += item.product.price * item.quantity

            order.total_price = total
            order.save(update_fields=['total_price'])

            # Очищаем корзину
            cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)



   # --- Скрываем от Сваггера ----
    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(auto_schema=None)
    def update(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(auto_schema=None)
    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PATCH')

    @swagger_auto_schema(auto_schema=None)
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')

    @swagger_auto_schema(auto_schema=None)  # ← спрячет
    def retrieve(self, request, pk=None):
        pass