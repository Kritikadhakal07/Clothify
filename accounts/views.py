from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from .forms import RegistrationForm
from .models import Account

from django.contrib.auth.decorators import login_required
from orders.models import Order


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name  = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email      = form.cleaned_data['email']
            username   = form.cleaned_data['username']
            password   = form.cleaned_data['password']

            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password,
            )
            user.phone_number = phone_number
            user.is_active = True   # set False later if you add email verification
            user.save()

            messages.success(request, 'Registration successful!')
            return redirect('login')
    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)


from django.shortcuts import render, redirect
from django.contrib import messages, auth
from .forms import RegistrationForm
from .models import Account
from carts.models import Carts
from carts.views import _cart_id


def login(request):
    if request.method == 'POST':
        email    = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            old_cart_id = _cart_id(request)   # capture session key BEFORE login rotates it

            auth.login(request, user)
            messages.success(request, 'You are now logged in.')

            new_cart_id = _cart_id(request)   # session key AFTER login

            try:
                cart = Carts.objects.get(cart_id=old_cart_id)
                cart.cart_id = new_cart_id
                cart.save()
            except Carts.DoesNotExist:
                pass

            next_param = request.POST.get('next') or request.GET.get('next')
            if next_param:
                return redirect(next_param)
            return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    next_param = request.GET.get('next', '')
    return render(request, 'accounts/login.html', {'next': next_param})


def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    orders_count = orders.count()

    context = {
        'orders': orders,
        'orders_count': orders_count,
    }
    return render(request, 'accounts/dashboard.html', context)