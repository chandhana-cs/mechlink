from django import forms
from .models import ServiceRequest

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['issue_description', 'location']
        widgets = {
            'issue_description': forms.Textarea(attrs={'rows':4}),
            'location': forms.TextInput(),
        }
