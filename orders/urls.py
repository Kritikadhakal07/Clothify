from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
        path('place_order/', views.place_order, name='place_order'),
    path('confirm_order/<int:order_id>/', views.confirm_order, name='confirm_order'),
    path('order_complete/', views.order_complete, name='order_complete'),
    
   
   
    path('my_orders/', views.my_orders, name='my_orders'),
    path('order_detail/<str:order_number>/', views.order_detail, name='order_detail'),

]