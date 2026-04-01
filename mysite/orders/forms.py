from django import forms
from django.forms import inlineformset_factory

from products.models import Product

from .models import Order, OrderLine


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["notes"]
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Informations de livraison, contraintes, commentaires...",
                }
            ),
        }


class OrderLineForm(forms.ModelForm):
    class Meta:
        model = OrderLine
        fields = ["product", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by(
            "name"
        )


OrderLineFormSet = inlineformset_factory(
    Order,
    OrderLine,
    form=OrderLineForm,
    fields=["product", "quantity"],
    extra=2,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
