from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import RiderCreateForm, SellerRegisterForm

ROLE_HOME = {"seller": "seller_home", "rider": "rider_home", "admin": "admin_home"}


def register(request):
    form = SellerRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("login")
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect(ROLE_HOME.get(user.role, "login"))
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


@role_required("seller")
def seller_home(request):
    return render(request, "accounts/home.html", {"role": "Seller"})


@role_required("rider")
def rider_home(request):
    return render(request, "accounts/home.html", {"role": "Rider"})


@role_required("admin")
def admin_home(request):
    return render(request, "accounts/home.html", {"role": "Admin"})


@role_required("admin")
def create_rider(request):
    form = RiderCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("admin_home")
    return render(request, "accounts/create_rider.html", {"form": form})
