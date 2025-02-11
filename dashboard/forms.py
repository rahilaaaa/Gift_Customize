from django import forms
from products.models import Coupon
from products.models import Product,Category

class CouponForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Coupon
        exclude = ['total_uses']  # Exclude total_uses from the form
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'valid_to': 'End date and time for the coupon validity',
            'max_uses': 'Maximum number of times this coupon can be used',
        }