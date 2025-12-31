from django.urls import path
from . import views

app_name = 'trips_api'

urlpatterns = [
    path('status/<uuid:trip_id>/', views.check_trip_status_api, name='check_status'),
    path('activity/<uuid:activity_id>/', views.get_activity_details, name='activity_detail'),
    path('activity/<uuid:activity_id>/update/', views.update_activity, name='update_activity'),
    path('itinerary/<uuid:itinerary_id>/feedback/', views.submit_feedback, name='submit_feedback'),
]