from django import forms
from django.contrib.auth.models import User
from .models import (Vehicle, ParkingReceipt, TyreServiceTransaction,
                     TyrePrice, BatteryTransaction, BatteryPrice, UserProfile)
import re


# ─── Validators ────────────────────────────────────────────────────────────────

def validate_name(value):
    if not value[0].isupper():
        raise forms.ValidationError("Name must start with a capital letter.")
    if any(c.isdigit() for c in value):
        raise forms.ValidationError("Name must not contain numbers.")

def validate_plate(value):
    if not value.startswith('U'):
        raise forms.ValidationError("Number plate must start with 'U'.")
    if not value.isalnum():
        raise forms.ValidationError("Number plate must be alphanumeric.")
    if len(value) >= 6:
        raise forms.ValidationError("Number plate must be less than 6 characters.")

def validate_ugandan_phone(value):
    pattern = r'^(\+256|0)(7[0-9]|3[1-9]|4[5-9])\d{7}$'
    if not re.match(pattern, value):
        raise forms.ValidationError("Enter a valid Ugandan phone number (e.g. 0712345678 or +256712345678).")

def validate_nin(value):
    if value:
        pattern = r'^(CM|CF)[A-Z0-9]{12}$'
        if not re.match(pattern, value.upper()):
            raise forms.ValidationError("NIN must start with CM or CF followed by 12 alphanumeric characters.")


# ─── Vehicle Registration Form ─────────────────────────────────────────────────

class VehicleRegistrationForm(forms.ModelForm):
    driver_name = forms.CharField(validators=[validate_name])
    number_plate = forms.CharField(validators=[validate_plate])
    phone_number = forms.CharField(validators=[validate_ugandan_phone])

    class Meta:
        model = Vehicle
        fields = ['driver_name', 'phone_number', 'nin_number', 'vehicle_type',
                  'number_plate', 'vehicle_model', 'vehicle_color']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_driver_name(self):
        val = self.cleaned_data['driver_name']
        validate_name(val)
        return val

    def clean_number_plate(self):
        val = self.cleaned_data['number_plate'].upper()
        validate_plate(val)
        return val

    def clean_phone_number(self):
        val = self.cleaned_data['phone_number']
        validate_ugandan_phone(val)
        return val

    def clean_nin_number(self):
        val = self.cleaned_data.get('nin_number', '')
        vehicle_type = self.cleaned_data.get('vehicle_type', '')
        if vehicle_type == 'boda_boda' and not val:
            raise forms.ValidationError("NIN is required for Boda-boda vehicles.")
        if val:
            validate_nin(val)
        return val.upper() if val else val


# ─── Sign-Out Form ─────────────────────────────────────────────────────────────

class SignOutForm(forms.ModelForm):
    receiver_name = forms.CharField(validators=[validate_name])
    receiver_phone = forms.CharField(validators=[validate_ugandan_phone])

    class Meta:
        model = ParkingReceipt
        fields = ['receiver_name', 'receiver_phone', 'receiver_gender', 'receiver_nin']
        widgets = {
            'receiver_gender': forms.Select(choices=[('', '-- Select --'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
        }

    def clean_receiver_nin(self):
        val = self.cleaned_data.get('receiver_nin', '')
        if val:
            validate_nin(val)
        return val.upper() if val else val


# ─── Tyre Service Form ─────────────────────────────────────────────────────────

class TyreServiceForm(forms.ModelForm):
    vehicle_plate = forms.CharField(validators=[validate_plate])
    driver_name = forms.CharField(validators=[validate_name])
    phone = forms.CharField(required=False, validators=[validate_ugandan_phone])

    class Meta:
        model = TyreServiceTransaction
        fields = ['vehicle_plate', 'driver_name', 'phone', 'service_type',
                  'tyre_size', 'tyre_brand', 'quantity', 'amount', 'notes']
        widgets = {
            'service_type': forms.Select(attrs={'class': 'form-select'}),
        }


class TyrePriceForm(forms.ModelForm):
    class Meta:
        model = TyrePrice
        fields = ['size', 'brand', 'price']


# ─── Battery Forms ─────────────────────────────────────────────────────────────

class BatteryTransactionForm(forms.ModelForm):
    customer_name = forms.CharField(validators=[validate_name])
    phone = forms.CharField(validators=[validate_ugandan_phone])

    class Meta:
        model = BatteryTransaction
        fields = ['customer_name', 'phone', 'vehicle_plate', 'transaction_type',
                  'battery_brand', 'battery_capacity', 'quantity', 'amount',
                  'hire_start', 'hire_end', 'notes']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'hire_start': forms.DateInput(attrs={'type': 'date'}),
            'hire_end': forms.DateInput(attrs={'type': 'date'}),
        }


class BatteryPriceForm(forms.ModelForm):
    class Meta:
        model = BatteryPrice
        fields = ['brand', 'capacity', 'transaction_type', 'price', 'hire_duration']


# ─── User Creation Form ────────────────────────────────────────────────────────

class CreateUserForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=50, validators=[validate_name])
    last_name = forms.CharField(max_length=50, validators=[validate_name])
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    phone = forms.CharField(required=False, validators=[validate_ugandan_phone])

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


# ─── Login Form ────────────────────────────────────────────────────────────────

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
