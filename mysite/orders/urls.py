from django.urls import path

from . import api, views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("new/", views.order_create, name="create"),
    path("<int:order_id>/", views.order_detail, name="detail"),
    path("api/orders/openapi.yaml", api.openapi_spec, name="api-openapi"),
    path("api/orders/", api.orders_collection, name="api-orders"),
    path("api/orders/<int:order_id>/", api.order_detail, name="api-order-detail"),
]
