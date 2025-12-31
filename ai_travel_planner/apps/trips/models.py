from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class TripRequest(models.Model):
    """Main trip planning request model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    TRAVEL_STYLE_CHOICES = [
        ('adventure', 'Adventure'),
        ('relaxation', 'Relaxation'),
        ('cultural', 'Cultural'),
        ('food_tour', 'Food Tour'),
        ('family', 'Family-Friendly'),
        ('romantic', 'Romantic'),
        ('budget', 'Budget Travel'),
        ('luxury', 'Luxury'),
    ]
    
    GROUP_SIZE_CHOICES = [
        ('solo', 'Solo'),
        ('couple', 'Couple'),
        ('family', 'Family (3-5)'),
        ('group', 'Group (6+)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_requests')
    # Trip Details
    destination = models.CharField(max_length=255)
    destination_country = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    duration = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)]) 
    # Budget
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    # Preferences
    travel_style = models.CharField(max_length=20, choices=TRAVEL_STYLE_CHOICES)
    group_size = models.CharField(max_length=20, choices=GROUP_SIZE_CHOICES)
    # Optional preferences
    interests = models.JSONField(default=list, blank=True)  # ["museums", "hiking", "nightlife"]
    dietary_restrictions = models.JSONField(default=list, blank=True)  
    accessibility_needs = models.TextField(blank=True)
    accommodation_preference = models.CharField(max_length=50, blank=True)  
    # Status and processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    celery_task_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.destination} - {self.user.username} ({self.get_status_display()})"
    
    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_msg):
        self.status = 'failed'
        self.error_message = error_msg
        self.save()
        
        
class Itinerary(models.Model):
    """Generated itinerary for a trip request"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip_request = models.ForeignKey(TripRequest, on_delete=models.CASCADE, related_name='itineraries')
    # Generated data
    title = models.CharField(max_length=255)
    description = models.TextField()
    generated_data = models.JSONField()  
    # Cost breakdown
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    cost_breakdown = models.JSONField()  # {accommodation, food, activities, transport}
    # Weather and context
    weather_data = models.JSONField(blank=True, default=dict)
    weather_last_updated = models.DateTimeField(null=True, blank=True)
    destination_info = models.JSONField(blank=True, default=dict)
    # Version control for regenerations
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    # User interaction
    user_rating = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    user_feedback = models.TextField(blank=True)
    times_viewed = models.IntegerField(default=0)
    is_favorite = models.BooleanField(default=False)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-version', '-created_at']
        indexes = [
            models.Index(fields=['trip_request', '-version']),
        ]
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def increment_views(self):
        self.times_viewed += 1
        self.save(update_fields=['times_viewed'])
        
        
class Activity(models.Model):
    """Individual activity within an itinerary"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('sightseeing', 'Sightseeing'),
        ('food', 'Food & Dining'),
        ('adventure', 'Adventure'),
        ('relaxation', 'Relaxation'),
        ('cultural', 'Cultural'),
        ('entertainment', 'Entertainment'),
        ('shopping', 'Shopping'),
        ('transport', 'Transportation'),
    ]
    
    TIME_SLOT_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('night', 'Night'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='activities')
    
    # Activity details
    day_number = models.IntegerField(validators=[MinValueValidator(1)])
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES)
    start_time = models.TimeField()
    duration_minutes = models.IntegerField()
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    
    location_name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.TextField(blank=True)
    
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    booking_required = models.BooleanField(default=False)
    booking_url = models.URLField(blank=True)
    tips = models.TextField(blank=True)
    
    # User modifications
    is_custom = models.BooleanField(default=False)  
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['day_number', 'order', 'start_time']
        indexes = [
            models.Index(fields=['itinerary', 'day_number']),
        ]
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"Day {self.day_number}: {self.name}"


class LocalExperience(models.Model):
    """Curated local experiences and hidden gems"""
    
    CATEGORY_CHOICES = [
        ('food', 'Local Food'),
        ('culture', 'Cultural Experience'),
        ('adventure', 'Adventure'),
        ('nightlife', 'Nightlife'),
        ('shopping', 'Shopping'),
        ('nature', 'Nature'),
        ('hidden_gem', 'Hidden Gem'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='local_experiences')
    
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    
    location_name = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
  
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    best_time = models.CharField(max_length=100, blank=True)  
    insider_tip = models.TextField(blank=True)
    
    priority = models.IntegerField(default=1)  # Higher = more recommended
    
    class Meta:
        ordering = ['-priority', 'category']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    
class UserFeedback(models.Model):
    """User feedback and modifications to itineraries"""
    
    FEEDBACK_TYPE_CHOICES = [
        ('rating', 'Rating'),
        ('modification', 'Modification Request'),
        ('regeneration', 'Regeneration Request'),
        ('comment', 'General Comment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    rating = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    modification_details = models.JSONField(blank=True, default=dict)
    
    # Response tracking
    was_addressed = models.BooleanField(default=False)
    response = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_feedback_type_display()} - {self.user.username}"