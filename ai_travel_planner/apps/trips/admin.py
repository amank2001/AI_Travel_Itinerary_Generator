from django.contrib import admin
from django.utils.html import format_html
from .models import TripRequest, Itinerary, Activity, LocalExperience, UserFeedback

# Register your models here.
@admin.register(TripRequest)
class TripRequestAdmin(admin.ModelAdmin):
    list_display = ['destination', 'user', 'start_date', 'duration', 'status', 'created_at']
    list_filter = ['status', 'travel_style', 'group_size', 'created_at']
    search_fields = ['destination', 'user__username', 'destination_country']
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at', 'celery_task_id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'status', 'celery_task_id')
        }),
        ('Trip Details', {
            'fields': ('destination', 'destination_country', 'start_date', 'duration')
        }),
        ('Budget', {
            'fields': ('budget', 'currency')
        }),
        ('Preferences', {
            'fields': ('travel_style', 'group_size', 'interests', 'dietary_restrictions', 
                      'accessibility_needs', 'accommodation_preference')
        }),
        ('Processing', {
            'fields': ('error_message', 'created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 0
    fields = ['day_number', 'name', 'start_time', 'duration_minutes', 'estimated_cost', 'activity_type']
    readonly_fields = ['id']


class LocalExperienceInline(admin.TabularInline):
    model = LocalExperience
    extra = 0
    fields = ['name', 'category', 'priority', 'estimated_cost']


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ['title', 'trip_destination', 'version', 'total_cost', 'user_rating', 'is_active', 'created_at']
    list_filter = ['is_active', 'user_rating', 'created_at']
    search_fields = ['title', 'description', 'trip_request__destination']
    readonly_fields = ['id', 'created_at', 'updated_at', 'times_viewed']
    inlines = [ActivityInline, LocalExperienceInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'trip_request', 'title', 'description')
        }),
        ('Cost Details', {
            'fields': ('total_cost', 'cost_breakdown')
        }),
        ('Generated Data', {
            'fields': ('generated_data', 'weather_data', 'destination_info'),
            'classes': ('collapse',)
        }),
        ('Version & Status', {
            'fields': ('version', 'is_active')
        }),
        ('User Interaction', {
            'fields': ('user_rating', 'user_feedback', 'times_viewed', 'is_favorite')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def trip_destination(self, obj):
        return obj.trip_request.destination
    trip_destination.short_description = 'Destination'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('trip_request')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'itinerary_title', 'day_number', 'time_slot', 'activity_type', 'estimated_cost']
    list_filter = ['activity_type', 'time_slot', 'day_number', 'is_custom']
    search_fields = ['name', 'description', 'location_name']
    readonly_fields = ['id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'itinerary', 'name', 'description', 'activity_type')
        }),
        ('Scheduling', {
            'fields': ('day_number', 'time_slot', 'start_time', 'duration_minutes', 'order')
        }),
        ('Location', {
            'fields': ('location_name', 'address', 'latitude', 'longitude')
        }),
        ('Cost & Booking', {
            'fields': ('estimated_cost', 'currency', 'booking_required', 'booking_url')
        }),
        ('Additional Info', {
            'fields': ('tips', 'is_custom')
        }),
    )
    
    def itinerary_title(self, obj):
        return obj.itinerary.title
    itinerary_title.short_description = 'Itinerary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('itinerary')


@admin.register(LocalExperience)
class LocalExperienceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'itinerary_title', 'priority', 'estimated_cost']
    list_filter = ['category', 'priority']
    search_fields = ['name', 'description', 'location_name']
    readonly_fields = ['id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'itinerary', 'name', 'category', 'description')
        }),
        ('Location', {
            'fields': ('location_name', 'latitude', 'longitude')
        }),
        ('Details', {
            'fields': ('estimated_cost', 'best_time', 'insider_tip', 'priority')
        }),
    )
    
    def itinerary_title(self, obj):
        return obj.itinerary.title
    itinerary_title.short_description = 'Itinerary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('itinerary')


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'itinerary_title', 'feedback_type', 'rating', 'was_addressed', 'created_at']
    list_filter = ['feedback_type', 'was_addressed', 'rating', 'created_at']
    search_fields = ['comment', 'user__username']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'itinerary', 'user', 'feedback_type')
        }),
        ('Feedback Content', {
            'fields': ('rating', 'comment', 'modification_details')
        }),
        ('Response', {
            'fields': ('was_addressed', 'response')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def itinerary_title(self, obj):
        return obj.itinerary.title
    itinerary_title.short_description = 'Itinerary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('itinerary', 'user')