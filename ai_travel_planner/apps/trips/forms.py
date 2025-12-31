from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from .models import TripRequest, UserFeedback


class TripPlanningForm(forms.ModelForm):
    """Form for creating a new trip request"""
    
    # Additional fields not in model
    interests = forms.MultipleChoiceField(
        choices=[
            ('museums', 'Museums & Galleries'),
            ('history', 'Historical Sites'),
            ('nature', 'Nature & Parks'),
            ('adventure', 'Adventure Sports'),
            ('nightlife', 'Nightlife'),
            ('shopping', 'Shopping'),
            ('photography', 'Photography'),
            ('local_cuisine', 'Local Cuisine'),
            ('beaches', 'Beaches'),
            ('hiking', 'Hiking'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select your interests (optional)"
    )
    
    dietary_restrictions = forms.MultipleChoiceField(
        choices=[
            ('vegetarian', 'Vegetarian'),
            ('vegan', 'Vegan'),
            ('halal', 'Halal'),
            ('kosher', 'Kosher'),
            ('gluten_free', 'Gluten-Free'),
            ('dairy_free', 'Dairy-Free'),
            ('nut_allergy', 'Nut Allergy'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select any dietary restrictions (optional)"
    )
    
    class Meta:
        model = TripRequest
        fields = [
            'destination',
            'start_date',
            'duration',
            'budget',
            'currency',
            'travel_style',
            'group_size',
            'accommodation_preference',
            'accessibility_needs',
        ]
        widgets = {
            'destination': forms.TextInput(attrs={
                'class': 'border-2 border-gray-300 focus:border-purple-600 rounded-md px-2 py-1',
                'placeholder': 'e.g., Paris, France',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'border-2 border-gray-300 focus:border-purple-600 rounded-md px-2 py-1',
                'type': 'date',
                'required': True
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'border-2 border-gray-300 focus:border-purple-600 rounded-md px-2 py-1',
                'min': '1',
                'max': '30',
                'placeholder': 'Number of days',
                'required': True
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'border-2 border-gray-300 focus:border-purple-600 rounded-md px-2 py-1',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Enter your budget',
                'required': True
            }),
            'currency': forms.Select(attrs={
                'class': 'border-2 border-gray-300 focus:border-purple-600 rounded-md px-2 py-1'
            }, choices=[
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
                ('GBP', 'GBP - British Pound'),
                ('JPY', 'JPY - Japanese Yen'),
                ('AUD', 'AUD - Australian Dollar'),
                ('CAD', 'CAD - Canadian Dollar'),
                ('INR', 'INR - Indian Rupee'),
            ]),
            'travel_style': forms.Select(attrs={
                'class': 'border-2 border-gray-300 focus:border-purple-600 rounded-md px-2 py-1',
                'required': True
            }),
            'group_size': forms.Select(attrs={
                'class': 'border-2 border-gray-300 focus:border-purple-600 rounded-md px-2 py-1',
                'required': True
            }),
            'accommodation_preference': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'No Preference'),
                ('hotel', 'Hotel'),
                ('hostel', 'Hostel'),
                ('airbnb', 'Airbnb/Vacation Rental'),
                ('resort', 'Resort'),
                ('boutique', 'Boutique Hotel'),
            ]),
            'accessibility_needs': forms.Textarea(attrs={
                'class': 'border-2 border-gray-300 focus:border-purple-600 rounded-md px-2 py-1',
                'rows': 3,
                'placeholder': 'Any accessibility requirements? (wheelchair access, etc.)'
            }),
        }
    
    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        
        if start_date:
            if start_date < date.today():
                raise ValidationError("Start date cannot be in the past.")
            
            if start_date > date.today() + timedelta(days=365):
                raise ValidationError("Start date cannot be more than 1 year in the future.")
        
        return start_date
    
    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        
        if duration:
            if duration < 1:
                raise ValidationError("Duration must be at least 1 day.")
            if duration > 30:
                raise ValidationError("Duration cannot exceed 30 days.")
        
        return duration
    
    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        
        if budget:
            if budget <= 0:
                raise ValidationError("Budget must be greater than 0.")
            if budget > 10000000:
                raise ValidationError("Budget seems unrealistic. Please enter a reasonable amount.")
        
        return budget
    
    def clean_destination(self):
        destination = self.cleaned_data.get('destination')
        
        if destination:
            destination = destination.strip()
            if len(destination) < 2:
                raise ValidationError("Please enter a valid destination.")
        
        return destination


class ItineraryFeedbackForm(forms.ModelForm):
    """Form for submitting feedback on an itinerary"""
    
    class Meta:
        model = UserFeedback
        fields = ['feedback_type', 'rating', 'comment', 'modification_details']
        widgets = {
            'feedback_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'Select Rating'),
                (1, '⭐ Poor'),
                (2, '⭐⭐ Fair'),
                (3, '⭐⭐⭐ Good'),
                (4, '⭐⭐⭐⭐ Very Good'),
                (5, '⭐⭐⭐⭐⭐ Excellent'),
            ]),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your thoughts...'
            }),
            'modification_details': forms.HiddenInput(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        feedback_type = cleaned_data.get('feedback_type')
        rating = cleaned_data.get('rating')
        comment = cleaned_data.get('comment')
        
        if feedback_type == 'rating' and not rating:
            raise ValidationError("Please provide a rating.")
        
        if feedback_type in ['comment', 'modification'] and not comment:
            raise ValidationError("Please provide your feedback.")
        
        return cleaned_data


class ItineraryModificationForm(forms.Form):
    """Form for requesting modifications to an itinerary"""
    
    MODIFICATION_TYPE_CHOICES = [
        ('change_day', 'Modify a specific day'),
        ('add_activity', 'Add an activity'),
        ('remove_activity', 'Remove an activity'),
        ('change_budget', 'Adjust budget allocation'),
        ('change_style', 'Change travel style'),
        ('regenerate_all', 'Regenerate entire itinerary'),
    ]
    
    modification_type = forms.ChoiceField(
        choices=MODIFICATION_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    day_number = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'placeholder': 'Day number'
        }),
        help_text="Which day to modify?"
    )
    
    modification_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe the changes you want...'
        }),
        required=True,
        help_text="Be specific about what you'd like to change"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        modification_type = cleaned_data.get('modification_type')
        day_number = cleaned_data.get('day_number')
        
        if modification_type in ['change_day', 'add_activity', 'remove_activity'] and not day_number:
            raise ValidationError("Please specify which day to modify.")
        
        return cleaned_data


class ChatRefinementForm(forms.Form):
    """Simple form for chat-based itinerary refinement"""
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Ask for changes... e.g., "Make day 2 more adventurous"',
            'required': True
        }),
        max_length=500,
        help_text="Describe how you'd like to refine your itinerary"
    )