from django.shortcuts import render
from store.models import Product

# Create your views here.
def store(request):
    product = Product.objects.all().filter(is_available=True)
    product_count = product.count()
    context={
        'products':product,
        'product_count':product_count
    }
    return render(request,'stores/store.html',context)