import secrets
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class OrderStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    SUBMITTED = "submitted", "Soumise"
    PREPARING = "preparing", "Preparation"
    SHIPPED = "shipped", "Expediee"
    COMPLETED = "completed", "Terminee"
    CANCELLED = "cancelled", "Annulee"


class Order(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    number = models.CharField(max_length=24, unique=True, editable=False)
    status = models.CharField(
        max_length=16,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)

    def generate_number(self):
        return f"ORD-{secrets.token_hex(4).upper()}"

    @property
    def total_amount(self):
        total = sum((line.total_amount for line in self.lines.all()), Decimal("0.00"))
        return total.quantize(Decimal("0.01"))

    @property
    def total_quantity(self):
        return sum(line.quantity for line in self.lines.all())


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200, editable=False)
    sku_snapshot = models.CharField(max_length=50, editable=False)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if self.product_id:
            if not self.product_name:
                self.product_name = self.product.name
            if not self.sku_snapshot:
                self.sku_snapshot = self.product.sku
            if self.unit_price in (None, ""):
                self.unit_price = self.product.price
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))
