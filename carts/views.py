from django.shortcuts import render,get_object_or_404,redirect  
from store.models import Product,Variation
from carts.models import Carts,CartItem
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist


from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Variation
from carts.models import Carts, CartItem

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Variation
from carts.models import Carts, CartItem


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        request.session.create()
    return request.session.session_key


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    # ── 1. Collect selected variations from the form ──────────────────────────
    product_variation = []
    if request.method == 'POST':
        for item in request.POST:
            key   = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,    # 'color' or 'size'
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    # ── 2. Get or create the Cart ─────────────────────────────────────────────
    try:
        cart = Carts.objects.get(cart_id=_cart_id(request))
    except Carts.DoesNotExist:
        cart = Carts.objects.create(cart_id=_cart_id(request))

    # ── 3. Get existing cart items for this product ───────────────────────────
    cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

    if cart_item_exists:
        cart_items = CartItem.objects.filter(product=product, cart=cart)

        existing_variations_list = []   # variations already in cart
        item_id_list             = []   # their ids

        for item in cart_items:
            existing_variations_list.append(list(item.variations.all()))
            item_id_list.append(item.id)

        # ── 4. If same variation combo exists → just increment qty ────────────
        if product_variation in existing_variations_list:
            index     = existing_variations_list.index(product_variation)
            item_id   = item_id_list[index]
            cart_item = CartItem.objects.get(id=item_id)
            cart_item.quantity += 1
            cart_item.save()

        # ── 5. New variation combo → create a new cart item ───────────────────
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart
            )
            if product_variation:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

    else:
        # ── 6. No cart item for this product at all → create fresh ────────────
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart
        )
        if product_variation:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variation)
        cart_item.save()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax         = 0
        grand_total = 0
        cart        = Carts.objects.get(cart_id=_cart_id(request))
        cart_items  = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total    += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax         = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total':       total,
        'quantity':    quantity,
        'cart_items':  cart_items,
        'tax':         tax,
        'grand_total': grand_total,
    }
    return render(request, 'stores/cart.html', context)


def remove_cart(request, product_id):
    cart      = Carts.objects.get(cart_id=_cart_id(request))
    product   = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


def remove(request, product_id):
    cart      = Carts.objects.get(cart_id=_cart_id(request))
    product   = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart')
    cart=Carts.objects.get(cart_id=_cart_id(request))
    product=get_object_or_404(Product,id=product_id)
    cart_item=CartItem.objects.get(product=product,cart=cart)
    cart_item.delete()
    return redirect('cart')