from django import forms
from .models import TourPackage, Itinerary

class TourPackageForm(forms.ModelForm):
    class Meta:
        model = TourPackage
        fields = [
            'title', 'location', 'start_date', 'end_date', 'duration', 'price',
            'availability', 'min_people', 'max_people', 'includes', 'excludes',
            'cancellation_policy', 'special_offer', 'image'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 border rounded-lg'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 border rounded-lg'}),
            'duration': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'price': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'availability': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'min_people': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'max_people': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'includes': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg h-24'}),
            'excludes': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg h-24'}),
            'cancellation_policy': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg h-24'}),
            'special_offer': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'image': forms.FileInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
        }

class ItineraryForm(forms.ModelForm):
    class Meta:
        model = Itinerary
        fields = ['day_number', 'title', 'description', 'accommodation']
        widgets = {
            'day_number': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'title': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg h-24'}),
            'accommodation': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
        }
