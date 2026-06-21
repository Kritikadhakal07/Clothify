from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart, name="cart"),
    path('add_cart/<int:product_id>/', views.add_cart, name="add_cart"),
    path('increase_quantity/<int:cart_item_id>/', views.increase_quantity, name="increase_quantity"),
    path('decrease_quantity/<int:cart_item_id>/', views.decrease_quantity, name="decrease_quantity"),
    path('remove/<int:cart_item_id>/', views.remove, name="remove"),
]