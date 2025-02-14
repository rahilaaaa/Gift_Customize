# forms.py
from django import forms
from .models import Address, Customer



class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['name', 'mobile', 'country', 'state', 'city', 'street', 'pincode']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Name'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mobile Number'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Country'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter State'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter City'}),
            'street': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Street Address', 'rows': 2}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Pincode'}),
        }
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if len(pincode) != 6 or not pincode.isdigit():
            raise forms.ValidationError("Pincode must be 6 digits.")
        return pincode

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if len(mobile) != 10 or not mobile.isdigit():
            raise forms.ValidationError("Mobile number must be 10 digits.")
        return mobile


    



class EditAccountForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['username', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super(EditAccountForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['readonly'] = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Customer.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Customer.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if len(phone) != 10 or not phone.isdigit():
            raise forms.ValidationError("Phone number must be 10 digits.")
        return phone