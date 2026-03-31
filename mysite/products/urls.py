from django.urls import path

from . import api, views

app_name = "products"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("catalogue/", views.catalog, name="catalogue"),
    path("api/docs", views.api_docs, name="api-docs"),
    path("api/docs/", views.api_docs),
    path("api/openapi.yaml", api.openapi_spec, name="api-openapi"),
    path("api/categories/", api.categories_collection, name="api-categories"),
    path(
        "api/categories/<int:category_id>/",
        api.category_detail,
        name="api-category-detail",
    ),
    path("api/products/", api.products_collection, name="api-products"),
    path(
        "api/products/<int:product_id>/",
        api.product_detail,
        name="api-product-detail",
    ),
]
