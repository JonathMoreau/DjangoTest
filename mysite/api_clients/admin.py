from django.contrib import admin

from .models import ApiClient


@admin.register(ApiClient)
class ApiClientAdmin(admin.ModelAdmin):
    list_display = ("name", "client_id", "scope_list", "is_active", "last_used_at")
    list_filter = ("is_active",)
    search_fields = ("name", "client_id", "description")
    readonly_fields = (
        "client_id",
        "secret_prefix",
        "last_used_at",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Identification",
            {
                "fields": ("name", "description", "is_active"),
            },
        ),
        (
            "Scopes",
            {
                "fields": ("scopes",),
                "description": "Exemples : orders:read, orders:write, products:read",
            },
        ),
        (
            "Secret",
            {
                "fields": ("client_id", "secret_prefix"),
                "description": (
                    "Le secret complet n'est jamais re-affiche. "
                    "Utilisez les commandes de gestion pour creer ou renouveler un secret."
                ),
            },
        ),
        (
            "Suivi",
            {
                "fields": ("last_used_at", "created_at", "updated_at"),
            },
        ),
    )

    def scope_list(self, obj):
        return ", ".join(obj.scopes) if obj.scopes else "-"

    scope_list.short_description = "Scopes"
