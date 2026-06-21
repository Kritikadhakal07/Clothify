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


import requests
from django.conf import settings
from django.urls import reverse
from django.contrib import messages


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

def initiate_khalti_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    url = settings.KHALTI_BASE_URL + 'epayment/initiate/'
    headers = {
        'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    return_url = request.build_absolute_uri(reverse('khalti_verify')) + f'?order_id={order.id}'

    payload = {
        "return_url": return_url,
        "website_url": request.build_absolute_uri('/'),
        "amount": int(order.order_total * 100),
        "purchase_order_id": order.order_number,
        "purchase_order_name": f"Order-{order.order_number}",
        "customer_info": {
            "name": order.full_name(),
            "email": order.email,
            "phone": order.phone,
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    print("KHALTI STATUS CODE:", response.status_code)   # ← debug
    print("KHALTI RESPONSE:", data)                       # ← debug

    if response.status_code == 200 and 'payment_url' in data:
        order.khalti_pidx = data['pidx']
        order.save()
        return redirect(data['payment_url'])
    else:
        messages.error(request, 'Could not initiate Khalti payment. Please try again.')
        return redirect('place_order')
def khalti_verify(request):
    pidx = request.GET.get('pidx')
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)

    url = settings.KHALTI_BASE_URL + 'epayment/lookup/'
    headers = {
        'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {"pidx": pidx}

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if response.status_code == 200 and data.get('status') == 'Completed':
        # Create Payment record
        payment = Payment.objects.create(
            user=request.user,
            payment_id=pidx,
            payment_method='Khalti',
            amount_paid=str(order.order_total),
            status='Completed',
        )
        order.payment = payment
        order.is_ordered = True
        order.status = 'Accepted'
        order.save()

        # Now create OrderProduct rows + reduce stock + clear cart
        cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request), is_active=True)
        for cart_item in cart_items:
            order_product = OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=request.user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.price,
                ordered=True,
            )
            order_product.variations.set(cart_item.variations.all())
            order_product.save()

            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        cart_items.delete()

        messages.success(request, 'Payment successful! Your order has been placed.')
        return redirect('order_complete')
    else:
        messages.error(request, 'Payment verification failed or was not completed.')
        return redirect('place_order')