from django.contrib import admin
from .models import Carts, CartItem


# Register your models here.
admin.site.register(Carts)
admin.site.register(CartItem)