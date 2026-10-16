from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .constants import MAX_ORDER_LINES, MAX_ORDER_UNITS
from .models import Box, Order, OrderItem, Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "length", "width", "height", "weight"]


class BoxForm(forms.ModelForm):
    class Meta:
        model = Box
        fields = ["name", "internal_length", "internal_width", "internal_height", "max_weight", "cost"]
        labels = {"internal_length": "Internal length", "internal_width": "Internal width",
                  "internal_height": "Internal height", "max_weight": "Maximum weight"}


class OrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="Select a product",
    )
    quantity = forms.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ("product", "quantity")


class BaseOrderItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        lines = [form.cleaned_data for form in self.forms
                 if form.cleaned_data and form.cleaned_data.get("product")]
        product_ids = [line["product"].pk for line in lines]
        if len(product_ids) != len(set(product_ids)):
            raise ValidationError("Choose each product once; use its quantity field for multiples.")

        total_units = sum(line["quantity"] for line in lines)
        if total_units > MAX_ORDER_UNITS:
            raise ValidationError(
                f"An order can contain at most {MAX_ORDER_UNITS} physical units; this order has {total_units}."
            )
        super().clean()


OrderItemFormSet = inlineformset_factory(
    Order, OrderItem, form=OrderItemForm, fields=("product", "quantity"), extra=3, can_delete=False,
    formset=BaseOrderItemFormSet, min_num=1, validate_min=True,
    max_num=MAX_ORDER_LINES, validate_max=True,
    widgets={"quantity": forms.NumberInput(attrs={"min": 1})},
)
