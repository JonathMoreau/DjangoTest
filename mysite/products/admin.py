from django.contrib import admin
from .models import Product, Category
from django.utils.html import format_html
from django import forms

admin.site.site_header = "Administration catalogue"
admin.site.site_title = "Back-office Django"
admin.site.index_title = "Gestion des produits"

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def clean_sku(self):
        sku = self.cleaned_data["sku"]
        if "test" in sku:
            raise forms.ValidationError("Le SKU ne doit pas être \"test\".")
        return sku

@admin.action(description="Désactiver les produits sélectionnés")
def deactivate_products(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "price", "stock", "stock_status", "stock_badge", "is_active")
    search_fields = ("name", "sku")
    list_filter = ("is_active",)

    fieldsets = (
        ("Informations générales", {
            "fields": ("name", "sku", "category")
        }),
        ("Détails commerciaux", {
            "fields": ("price", "stock", "is_active")
        }),
        ("Description", {
            "fields": ("description",)
        }),
        ("Dates", {
            "fields": ("created_at", "updated_at")
        }),
    )

    readonly_fields = ("created_at", "updated_at")

    actions = [deactivate_products]

    form = ProductAdminForm

    def stock_status(self, obj):
        return "Rupture" if obj.stock == 0 else "Disponible"

    stock_status.short_description = "Statut stock"

    def stock_badge(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color:red;">Rupture</span>')
        return format_html('<span style="color:green;">Disponible</span>')
    stock_badge.short_description = "Statut stock"
    

admin.site.register(Category)