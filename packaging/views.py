from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BoxForm, OrderItemFormSet, ProductForm
from .models import Box, Order, Product
from .services import recommend_box


def home(request):
    return render(request, "packaging/home.html", {"product_count": Product.objects.count(), "box_count": Box.objects.count()})


def product_list(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product saved.")
        return redirect("product_list")
    return render(request, "packaging/product_list.html", {"form": form, "products": Product.objects.all()})


def box_list(request):
    form = BoxForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Shipping box saved.")
        return redirect("box_list")
    return render(request, "packaging/box_list.html", {"form": form, "boxes": Box.objects.all()})


def order_create(request):
    order = Order()
    formset = OrderItemFormSet(request.POST or None, instance=order, prefix="items")
    if request.method == "POST" and formset.is_valid():
        with transaction.atomic():
            saved_order = Order.objects.create()
            formset.instance = saved_order
            formset.save()
        return redirect("recommendation", order_id=saved_order.pk)
    return render(request, "packaging/order_create.html", {"formset": formset})


def recommendation(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), pk=order_id)
    result = recommend_box(order)
    return render(request, "packaging/recommendation.html", {"order": order, "result": result})
