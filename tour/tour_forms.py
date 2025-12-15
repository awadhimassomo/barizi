"""
Forms for managing tour itineraries and derived questions.
"""
from django import forms
from django.forms import formset_factory
from datetime import datetime, timedelta
from django.utils import timezone

class ItineraryDayForm(forms.Form):
    """Form for a single day in the itinerary."""
    day_number = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-20 p-2 border rounded bg-gray-50',
            'readonly': 'readonly'
        })
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-2 border rounded',
            'onchange': 'updateSubsequentDates(this)'
        })
    )
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border rounded',
            'placeholder': 'E.g., Arrival at Kilimanjaro'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full p-2 border rounded h-20',
            'placeholder': 'Activity details...',
            'rows': 3
        })
    )
    accommodation = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border rounded',
            'placeholder': 'Accommodation details...'
        })
    )
    meals = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border rounded',
            'placeholder': 'E.g., Breakfast, Lunch, Dinner'
        })
    )

ItineraryFormSet = formset_factory(ItineraryDayForm, extra=0)

class TourItineraryForm(forms.Form):
    """Main form for creating/editing tour itineraries."""
    BUDGET_LEVELS = [
        ('', '--Select--'),
        ('budget', 'Budget'),
        ('mid-range', 'Mid-Range'),
        ('luxury', 'Luxury'),
        ('ultra-luxury', 'Ultra Luxury'),
    ]

    TRIP_TYPES = [
        ('', '--Select--'),
        ('safari', 'Safari'),
        ('beach', 'Beach Holiday'),
        ('cultural', 'Cultural Tour'),
        ('adventure', 'Adventure'),
        ('honeymoon', 'Honeymoon'),
        ('family', 'Family Trip'),
        ('photography', 'Wildlife Photography'),
        ('trekking', 'Trekking/Hiking'),
        ('combined', 'Combined Tour'),
    ]

    # Basic Information
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border rounded-lg',
            'placeholder': 'Tour Title'
        })
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border rounded-lg',
            'placeholder': 'Country'
        })
    )
    
    # Duration & Dates
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-3 border rounded-lg',
            'onchange': 'updateItineraryDates()'
        })
    )
    duration_days = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border rounded-lg',
            'onchange': 'updateItineraryDays()',
            'min': '1'
        })
    )
    
    # Trip Details
    budget_level = forms.ChoiceField(
        choices=BUDGET_LEVELS,
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border rounded-lg'
        })
    )
    
    trip_type = forms.ChoiceField(
        choices=TRIP_TYPES,
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border rounded-lg'
        })
    )
    
    group_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border rounded-lg',
            'placeholder': 'E.g., Private, Group, Solo'
        })
    )
    
    estimated_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border rounded-lg',
            'placeholder': 'Estimated price in USD',
            'step': '0.01'
        })
    )
    
    destinations = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full p-3 border rounded-lg',
            'placeholder': 'List main destinations, separated by commas',
            'rows': 2
        })
    )
    
    # Review & Status
    status = forms.ChoiceField(
        choices=[
            ('draft', 'Draft'),
            ('pending_review', 'Pending Review'),
            ('published', 'Published')
        ],
        initial='draft',
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border rounded-lg'
        })
    )
    
    reviewer_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full p-3 border rounded-lg',
            'placeholder': 'Reviewer notes...',
            'rows': 3
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial start date to today if not provided
        if not self.initial.get('start_date'):
            self.initial['start_date'] = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        duration_days = cleaned_data.get('duration_days', 1)
        
        if start_date and duration_days:
            # Calculate end date
            end_date = start_date + timedelta(days=duration_days - 1)
            cleaned_data['end_date'] = end_date
            
        return cleaned_data
