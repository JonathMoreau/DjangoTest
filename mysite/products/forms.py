from django import forms

from .models import Category, Product


class CategoryApiForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class ProductApiForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category",
            "sku",
            "name",
            "slug",
            "description",
            "image",
            "price",
            "stock",
            "is_active",
        ]
