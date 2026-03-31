from django.db.models import Count, Prefetch, Q
from django.shortcuts import render

from .models import Category, Product


def api_docs(request):
    return render(request, "products/api_docs.html")


def catalog(request):
    active_products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .order_by("category__name", "name")
    )

    category_preview_products = Product.objects.filter(is_active=True).only(
        "id",
        "name",
        "category_id",
    ).order_by("name")

    categories = list(
        Category.objects.annotate(
            active_product_count=Count(
                "products",
                filter=Q(products__is_active=True),
            )
        )
        .prefetch_related(
            Prefetch(
                "products",
                queryset=category_preview_products,
                to_attr="active_products",
            )
        )
        .order_by("name")
    )

    selected_category = None
    selected_category_id = request.GET.get("category")

    if selected_category_id and selected_category_id.isdigit():
        selected_category = next(
            (category for category in categories if category.id == int(selected_category_id)),
            None,
        )
        if selected_category is not None:
            active_products = active_products.filter(category_id=selected_category.id)

    all_active_products = Product.objects.filter(is_active=True)
    products = list(active_products)

    context = {
        "categories": categories,
        "products": products,
        "selected_category": selected_category,
        "selected_category_id": int(selected_category_id)
        if selected_category is not None
        else None,
        "category_count": len(categories),
        "product_count": len(products),
        "all_product_count": all_active_products.count(),
        "in_stock_count": all_active_products.filter(stock__gt=0).count(),
    }
    return render(request, "products/catalog.html", context)
