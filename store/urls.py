from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    
    path('',views.store,name='store'),
    path('<slug:category_slug>/',views.store,name='product_by_category'),
]
