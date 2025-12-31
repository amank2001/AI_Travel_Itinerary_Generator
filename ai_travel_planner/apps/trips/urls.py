from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    # Main trip planning
    path('plan/', views.plan_trip, name='plan_trip'),
    path('my-trips/', views.my_trips, name='my_trips'),
    # Trip status
    path('status/<uuid:trip_id>/', views.trip_status, name='trip_status'),
    path('api/status/<uuid:trip_id>/', views.check_trip_status_api, name='check_status_api'),
    # Itinerary views
    path('itinerary/<uuid:itinerary_id>/', views.itinerary_detail, name='itinerary_detail'),
    path('itinerary/<uuid:itinerary_id>/versions/', views.itinerary_versions, name='itinerary_versions'),
    path('itinerary/<uuid:itinerary_id>/restore/', views.restore_version, name='restore_version'),
    path('itinerary/<uuid:itinerary_id>/delete/', views.delete_version, name='delete_version'),
    path('compare-versions/', views.compare_versions, name='compare_versions'),
    # Itinerary actions
    path('itinerary/<uuid:itinerary_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('itinerary/<uuid:itinerary_id>/export-pdf/', views.export_itinerary_pdf, name='export_pdf'),
    path('itinerary/<uuid:itinerary_id>/share/', views.share_itinerary, name='share_itinerary'),
    path('itinerary/<uuid:itinerary_id>/chat-refine/', views.chat_refine_itinerary, name='chat_refine'),
    # Activity management
    path('activity/<uuid:activity_id>/', views.get_activity_details, name='activity_details'),
    path('activity/<uuid:activity_id>/update/', views.update_activity, name='update_activity'),
    # Trip Management
    path('trip/<uuid:trip_id>/delete/', views.delete_trip, name='delete_trip'),
    path('trips/bulk-delete/', views.bulk_delete_trips, name='bulk_delete_trips'),
    # Public sharing
    path('shared/<uuid:itinerary_id>/', views.shared_itinerary_view, name='shared_itinerary'),
    # Feedback and Rating 
    path('itinerary/<uuid:itinerary_id>/submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('itinerary/<uuid:itinerary_id>/rate/', views.rate_itinerary, name='rate_itinerary'),
    path('itinerary/<uuid:itinerary_id>/get-rating/', views.get_itinerary_rating, name='get_rating'),
    #Map Data
    path('itinerary/<uuid:itinerary_id>/map-data/', views.get_map_data, name='get_map_data'),
    # Weather refresh route
    path('itinerary/<uuid:itinerary_id>/refresh-weather/',  views.refresh_weather,  name='refresh_weather'),
]