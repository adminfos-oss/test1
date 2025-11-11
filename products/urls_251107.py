# products/urls.py)

from django.urls import path
from .views import ProductViewSet

list_create = ProductViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

patch_delete = ProductViewSet.as_view({
    'patch': 'partial_update',
    'delete': 'destroy',
})


urlpatterns = [
    path('list_create/', list_create, ),
    path('patch_delete/<int:pk>/', patch_delete, ),
]
