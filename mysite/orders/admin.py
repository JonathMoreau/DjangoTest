from django.contrib import admin

from .models import Order, OrderLine


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 1
    raw_id_fields = ("product",)
    readonly_fields = ("product_name", "sku_snapshot", "unit_price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "status", "total_display", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("number", "customer__username", "customer__email")
    raw_id_fields = ("customer",)
    readonly_fields = ("number", "created_at", "updated_at", "total_display")
    inlines = [OrderLineInline]

    def total_display(self, obj):
        return f"{obj.total_amount:.2f} EUR"

    total_display.short_description = "Total"
