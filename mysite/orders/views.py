from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OrderCreateForm, OrderLineFormSet
from .models import Order, OrderStatus


@login_required
def order_list(request):
    orders = (
        Order.objects.filter(customer=request.user)
        .prefetch_related("lines__product")
        .order_by("-created_at")
    )
    status_cards = [
        {
            "value": value,
            "label": label,
            "count": orders.filter(status=value).count(),
        }
        for value, label in OrderStatus.choices
    ]
    context = {
        "orders": orders,
        "status_cards": status_cards,
    }
    return render(request, "orders/order_list.html", context)


@login_required
def order_create(request):
    order = Order(customer=request.user)

    if request.method == "POST":
        form = OrderCreateForm(request.POST, instance=order)
        formset = OrderLineFormSet(request.POST, instance=order, prefix="lines")
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            order.save()
            formset.instance = order
            formset.save()
            return redirect("orders:detail", order_id=order.id)
    else:
        form = OrderCreateForm(instance=order)
        formset = OrderLineFormSet(instance=order, prefix="lines")

    return render(
        request,
        "orders/order_create.html",
        {
            "form": form,
            "formset": formset,
        },
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.filter(customer=request.user).prefetch_related("lines__product"),
        pk=order_id,
    )
    return render(request, "orders/order_detail.html", {"order": order})
