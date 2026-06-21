import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from carts.models import CartItem
from carts.views import _cart_id
from .forms import OrderForm
from .models import Order

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from carts.models import CartItem
from carts.views import _cart_id
from .forms import OrderForm
from .models import Order, OrderProduct


@login_required(login_url='login')
def place_order(request):
    current_user = request.user
    cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request), is_active=True)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    total = 0
    quantity = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = current_user
            order.order_total = grand_total
            order.tax = tax
            order.ip = request.META.get('REMOTE_ADDR')
            order.save()

            order_number = datetime.datetime.now().strftime('%Y%m%d') + str(order.id)
            order.order_number = order_number
            order.save()

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
    else:
        # pre-fill name/email from logged-in user
        form = OrderForm(initial={
            'first_name': current_user.first_name,
            'last_name':  current_user.last_name,
            'email':      current_user.email,
            'phone':      current_user.phone_number,
        })

    return render(request, 'orders/place_order.html', {'form': form})



@login_required(login_url='login')
def confirm_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request), is_active=True)

    if request.method == 'POST':
        # 1. Create OrderProduct rows from cart items
        for cart_item in cart_items:
            order_product = OrderProduct.objects.create(
                order=order,
                user=request.user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.price,
                ordered=True,
            )
            order_product.variations.set(cart_item.variations.all())
            order_product.save()

            # 2. Reduce stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        # 3. Mark order as completed
        order.is_ordered = True
        order.status = 'Accepted'
        order.save()

        # 4. Clear the cart
        cart_items.delete()

        return redirect('order_complete')

    return redirect('place_order')


def order_complete(request):
    return render(request, 'orders/order_complete.html')


def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'orders/my_orders.html', context)


def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_products = OrderProduct.objects.filter(order=order)

    sub_total = 0
    for item in order_products:
        sub_total += item.product_price * item.quantity

    context = {
        'order': order,
        'order_products': order_products,
        'sub_total': sub_total,
    }
    return render(request, 'orders/order_detail.html', context)