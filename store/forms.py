from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from .models import (
    ProductReview, Address, PromoCode, 
    ShippingMethod, SiteSettings, Order, CustomerProfile
)
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomLoginForm(forms.Form):
    """Custom login form that accepts email or username"""
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your email / username / phone number',
            'autofocus': True,
        }),
        label='Email / Username / Phone'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password'
        }),
        label='Password'
    )


class CustomRegisterForm(UserCreationForm):
    """Custom registration form with professional styling"""
    phone = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your phone number'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your email address'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'phone', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Choose a username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Last name'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-control form-control-lg',
                'placeholder': 'Create a password',
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-control form-control-lg',
                'placeholder': 'Confirm password',
            })
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            raise ValidationError('Phone number is required.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=commit)
        phone = self.cleaned_data.get('phone')
        if commit and user and phone:
            CustomerProfile.objects.update_or_create(user=user, defaults={'phone': phone})
        return user


class ProductReviewForm(forms.ModelForm):
    """Form for submitting product reviews"""
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=ProductReview.RATING_CHOICES),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Write your review here...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['rating'].required = True
        self.fields['comment'].required = True


class AddressForm(forms.ModelForm):
    """Form for adding/editing addresses with professional styling"""
    class Meta:
        model = Address
        fields = [
            'full_name', 'phone', 'address_line_1', 'address_line_2',
            'city', 'state', 'postal_code', 'country', 'is_default'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Full name (e.g., John Doe)',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Phone number (e.g., +91 98765 43210)',
                'required': True,
                'type': 'tel'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Street address, building, apartment, etc.',
                'required': True
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Apartment, suite, unit, building, floor, etc. (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'City/Town',
                'required': True
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'State/Province',
                'required': True
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Postal/ZIP code',
                'required': True
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Country',
                'value': 'India',
                'required': True
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_default'
            }),
        }
        labels = {
            'full_name': 'Full Name',
            'phone': 'Phone Number',
            'address_line_1': 'Address Line 1',
            'address_line_2': 'Address Line 2',
            'postal_code': 'Postal Code',
            'is_default': 'Set as default address'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom CSS classes and validation
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['required'] = 'required'
            if 'form-control' in field.widget.attrs.get('class', ''):
                field.widget.attrs['class'] += ' border-0 shadow-sm'


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ContactForm(forms.Form):
    """Contact form"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'})
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your Message'
        })
    )


class PromoCodeForm(forms.Form):
    """Form for applying promo code"""
    promo_code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter promo code'
        })
    )


class CheckoutForm(forms.Form):
    """Enhanced checkout form"""
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address_line_1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address_line_2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    postal_code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(max_length=100, initial='India', widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Optional fields
    shipping_method = forms.ModelChoiceField(
        queryset=ShippingMethod.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    customer_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    save_address = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    # For logged in users - use saved address
    use_saved_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['use_saved_address'].queryset = Address.objects.filter(
                user=user, address_type='shipping'
            )

