from django.urls import path

from . import views

app_name = "api_docs"

urlpatterns = [
    path("api/docs", views.index, name="index"),
    path("api/docs/", views.index),
    path("api/docs/<slug:domain_slug>", views.domain_docs, name="domain-docs"),
    path("api/docs/<slug:domain_slug>/", views.domain_docs),
]
