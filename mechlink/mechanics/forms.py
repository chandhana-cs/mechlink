from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name',  'price', 'stock', 'image']

from django import forms
from .models import MechanicProfile

class MechanicProfileForm(forms.ModelForm):
    MECHANIC_TYPE_CHOICES = [
        ('two_wheeler', 'Two-Wheeler Mechanic'),
        ('automotive', 'Automotive Mechanic'),
        ('heavy_vehicle', 'Heavy Vehicle Mechanic'),
    ]

    mechanic_types = forms.MultipleChoiceField(
        choices=MECHANIC_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Select Mechanic Type(s)"
    )

    class Meta:
        model = MechanicProfile
        fields = [
            'shop_name', 'phone', 'address', 'location',
            'pincode', 'latitude', 'longitude', 'mechanic_types'
        ]

