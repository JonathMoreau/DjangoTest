from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class ApiDocsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api_docs"
    verbose_name = "API Docs"

    def ready(self):
        autodiscover_modules("api_docs")
