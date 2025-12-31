from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.loader import render_to_string
from django.db import transaction, models
from copy import deepcopy
import logging, json
from weasyprint import HTML
from .models import TripRequest, Itinerary, Activity, LocalExperience, UserFeedback
from .forms import TripPlanningForm, ItineraryFeedbackForm, ChatRefinementForm
from .tasks import generate_trip_itinerary, update_weather_data_sync

logger = logging.getLogger(__name__)

def home(request):
    """Home page view"""
    return render(request, 'core/home.html')


@login_required
def plan_trip(request):
    """Trip planning form view"""
    if request.method == 'POST':
        form = TripPlanningForm(request.POST)
        
        if form.is_valid():
            trip_request = form.save(commit=False)
            trip_request.user = request.user
            
            # Convert multi-choice fields to JSON
            trip_request.interests = form.cleaned_data.get('interests', [])
            trip_request.dietary_restrictions = form.cleaned_data.get('dietary_restrictions', [])
            
            trip_request.save()
            
            
            # Call task synchronously (no .delay())
            try:
                # Execute task immediately without Celery
                result = generate_trip_itinerary(str(trip_request.id))
                
                if result.get('status') == 'success':
                    messages.success(
                        request, 
                        'Your trip itinerary has been created successfully!'
                    )
                    itinerary_id = result.get('itinerary_id')
                    return redirect('trips:itinerary_detail', itinerary_id=itinerary_id)
                else:
                    messages.error(
                        request,
                        'Failed to generate itinerary. Please try again.'
                    )
                    return redirect('trips:plan_trip')
                    
            except Exception as e:
                messages.error(
                    request,
                    f'Error generating itinerary: {str(e)}'
                )
                return redirect('trips:plan_trip')
    else:
        form = TripPlanningForm()
    
    return render(request, 'trips/plan_trip.html', {'form': form})


@login_required
def trip_status(request, trip_id):
    """Check status of trip generation"""
    trip_request = get_object_or_404(TripRequest, id=trip_id, user=request.user)
    
    context = {
        'trip_request': trip_request,
        'is_processing': trip_request.status == 'processing',
        'is_completed': trip_request.status == 'completed',
        'is_failed': trip_request.status == 'failed',
    }
    
    # If completed, get the latest itinerary
    if trip_request.status == 'completed':
        itinerary = trip_request.itineraries.filter(is_active=True).first()
        if itinerary:
            return redirect('trips:itinerary_detail', itinerary_id=itinerary.id)
    
    return render(request, 'trips/trip_status.html', context)


@login_required
def check_trip_status_api(request, trip_id):
    """API endpoint to check trip generation status"""
    trip_request = get_object_or_404(TripRequest, id=trip_id, user=request.user)
    
    data = {
        'status': trip_request.status,
        'error_message': trip_request.error_message if trip_request.status == 'failed' else None
    }
    
    # If completed, include itinerary URL
    if trip_request.status == 'completed':
        itinerary = trip_request.itineraries.filter(is_active=True).first()
        if itinerary:
            data['itinerary_url'] = f'/trips/itinerary/{itinerary.id}/'
    
    return JsonResponse(data)


@login_required
def itinerary_detail(request, itinerary_id):
    """View detailed itinerary"""
    itinerary = get_object_or_404(
        Itinerary.objects.select_related('trip_request__user'),
        id=itinerary_id
    )
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        messages.error(request, 'You do not have permission to view this itinerary.')
        return redirect('trips:my_trips')
    
    # Increment view count
    itinerary.increment_views()
    
    # Get activities grouped by day
    activities_by_day = {}
    for activity in itinerary.activities.all():
        if activity.day_number not in activities_by_day:
            activities_by_day[activity.day_number] = []
        activities_by_day[activity.day_number].append(activity)
    
    # Get local experiences
    local_experiences = itinerary.local_experiences.all()
    
    # Calculate some stats
    total_activities = itinerary.activities.count()
    
    # Weather data
    weather_data = None
    raw = getattr(itinerary, "weather_json", None) or getattr(itinerary, "weather", None)
    if raw:
        if isinstance(raw, str):
            try:
                weather_data = json.loads(raw)
            except ValueError:
                weather_data = None
        else:
            weather_data = raw  
    if not weather_data or not isinstance(weather_data, dict) or 'days' not in weather_data:
        weather_data = {'days': []}
    itinerary.weather_data = weather_data
    
    context = {
        'itinerary': itinerary,
        'trip_request': itinerary.trip_request,
        'activities_by_day': dict(sorted(activities_by_day.items())),
        'local_experiences': local_experiences,
        'total_activities': total_activities,
        'feedback_form': ItineraryFeedbackForm(),
        'chat_form': ChatRefinementForm(),
    }
    
    return render(request, 'trips/itinerary_detail.html', context)


@login_required
def my_trips(request):
    """View all user's trips"""
    trips = TripRequest.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        trips = trips.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        trips = trips.filter(
            Q(destination__icontains=search_query) |
            Q(destination_country__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(trips, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'trips': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'trips/my_trips.html', context)


@login_required
@require_http_methods(["POST"])
def submit_feedback(request, itinerary_id):
    """Submit feedback for an itinerary"""
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    form = ItineraryFeedbackForm(request.POST)
    
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.itinerary = itinerary
        feedback.user = request.user
        feedback.save()
        
        # Update itinerary rating if feedback is a rating
        if feedback.feedback_type == 'rating' and feedback.rating:
            itinerary.user_rating = feedback.rating
            itinerary.user_feedback = feedback.comment
            itinerary.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Thank you for your feedback!'
        })
    
    return JsonResponse({
        'status': 'error',
        'errors': form.errors
    }, status=400)


@login_required
@require_http_methods(["POST"])
def rate_itinerary(request, itinerary_id):
    """
    API endpoint to submit rating for an itinerary
    Handles both initial rating and rating updates
    """
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        
        # Validate rating
        if not rating or not isinstance(rating, int):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid rating value'
            }, status=400)
        
        if rating < 1 or rating > 5:
            return JsonResponse({
                'status': 'error',
                'message': 'Rating must be between 1 and 5'
            }, status=400)
        
        # Check if user already rated this itinerary
        existing_feedback = UserFeedback.objects.filter(
            itinerary=itinerary,
            user=request.user,
            feedback_type='rating'
        ).first()
        
        if existing_feedback:
            # Update existing rating
            existing_feedback.rating = rating
            if comment:
                existing_feedback.comment = comment
            existing_feedback.save()
            
            logger.info(
                f"User {request.user.username} updated rating for itinerary {itinerary_id} to {rating}"
            )
            message = 'Rating updated successfully!'
        else:
            # Create new rating
            UserFeedback.objects.create(
                itinerary=itinerary,
                user=request.user,
                feedback_type='rating',
                rating=rating,
                comment=comment
            )
            
            logger.info(
                f"User {request.user.username} rated itinerary {itinerary_id} with {rating} stars"
            )
            message = 'Thank you for your rating!'
        
        # Update itinerary's rating field
        itinerary.user_rating = rating
        if comment:
            itinerary.user_feedback = comment
        itinerary.save(update_fields=['user_rating', 'user_feedback'])
        
        # Calculate average rating from all feedback
        all_ratings = UserFeedback.objects.filter(
            itinerary=itinerary,
            feedback_type='rating',
            rating__isnull=False
        )
        
        total_ratings = all_ratings.count()
        avg_rating = sum([f.rating for f in all_ratings]) / total_ratings if total_ratings > 0 else 0
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'rating': rating,
            'average_rating': round(avg_rating, 1),
            'total_ratings': total_ratings
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving rating: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to save rating: {str(e)}'
        }, status=500)


@login_required
def get_itinerary_rating(request, itinerary_id):
    """
    API endpoint to get current rating statistics for an itinerary
    """
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get user's rating
        user_feedback = UserFeedback.objects.filter(
            itinerary=itinerary,
            user=request.user,
            feedback_type='rating'
        ).first()
        
        user_rating = user_feedback.rating if user_feedback else None
        user_comment = user_feedback.comment if user_feedback else ''
        
        # Get all ratings
        all_ratings = UserFeedback.objects.filter(
            itinerary=itinerary,
            feedback_type='rating',
            rating__isnull=False
        )
        
        total_ratings = all_ratings.count()
        
        if total_ratings > 0:
            avg_rating = sum([f.rating for f in all_ratings]) / total_ratings
            
            # Rating breakdown (count for each star)
            rating_breakdown = {
                '5': all_ratings.filter(rating=5).count(),
                '4': all_ratings.filter(rating=4).count(),
                '3': all_ratings.filter(rating=3).count(),
                '2': all_ratings.filter(rating=2).count(),
                '1': all_ratings.filter(rating=1).count(),
            }
        else:
            avg_rating = 0
            rating_breakdown = {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
        
        return JsonResponse({
            'status': 'success',
            'user_rating': user_rating,
            'user_comment': user_comment,
            'average_rating': round(avg_rating, 1),
            'total_ratings': total_ratings,
            'rating_breakdown': rating_breakdown
        })
        
    except Exception as e:
        logger.error(f"Error fetching rating: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to fetch rating data'
        }, status=500)
        

@login_required
def export_itinerary_pdf(request, itinerary_id):
    """Export itinerary as PDF"""
    
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        messages.error(request, 'You do not have permission to export this itinerary.')
        return redirect('trips:my_trips')
    
    try:
        # Get activities grouped by day
        activities_by_day = {}
        for activity in itinerary.activities.all():
            if activity.day_number not in activities_by_day:
                activities_by_day[activity.day_number] = []
            activities_by_day[activity.day_number].append(activity)
        
        # Get local experiences
        local_experiences = itinerary.local_experiences.all()
        
        # Prepare context
        context = {
            'itinerary': itinerary,
            'trip_request': itinerary.trip_request,
            'activities_by_day': dict(sorted(activities_by_day.items())),
            'local_experiences': local_experiences,
        }
        
        # Render HTML template
        html_string = render_to_string('trips/pdf/itinerary_pdf.html', context)
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()
        
        # Create response
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="itinerary_{itinerary.trip_request.destination.replace(" ", "_")}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        messages.error(request, f'Failed to generate PDF: {str(e)}')
        return redirect('trips:itinerary_detail', itinerary_id=itinerary_id)


@login_required
def itinerary_versions(request, itinerary_id):
    """
    View all versions of an itinerary for a trip
    
    Args:
        request: HTTP request
        itinerary_id: UUID of the TripRequest
    """
    trip_request = get_object_or_404(TripRequest, id=itinerary_id, user=request.user)
    
    # Get all versions ordered by version number (newest first)
    versions = trip_request.itineraries.all().order_by('-version')
    
    context = {
        'trip_request': trip_request,
        'versions': versions,
    }
    
    return render(request, 'trips/itinerary_versions.html', context)


@login_required
@require_http_methods(["POST"])
def restore_version(request, itinerary_id):
    """
    Restore a previous version of an itinerary as the active version
    
    Args:
        request: HTTP request
        itinerary_id: UUID of the version to restore
    """
    version_to_restore = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if version_to_restore.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        trip_request = version_to_restore.trip_request
        
        # Deactivate all current versions
        trip_request.itineraries.update(is_active=False)
        
        # Get the highest version number
        max_version = trip_request.itineraries.aggregate(
            max_ver=models.Max('version')
        )['max_ver'] or 0
        
        # Create new version based on the one being restored
        new_itinerary = Itinerary.objects.create(
            trip_request=trip_request,
            title=version_to_restore.title,
            description=f"Restored from v{version_to_restore.version}",
            generated_data=deepcopy(version_to_restore.generated_data),
            total_cost=version_to_restore.total_cost,
            cost_breakdown=version_to_restore.cost_breakdown,
            weather_data=version_to_restore.weather_data,
            destination_info=version_to_restore.destination_info,
            version=max_version + 1,
            is_active=True
        )
        
        # Copy activities
        for activity in version_to_restore.activities.all():
            Activity.objects.create(
                itinerary=new_itinerary,
                day_number=activity.day_number,
                time_slot=activity.time_slot,
                start_time=activity.start_time,
                duration_minutes=activity.duration_minutes,
                name=activity.name,
                description=activity.description,
                activity_type=activity.activity_type,
                location_name=activity.location_name,
                latitude=activity.latitude,
                longitude=activity.longitude,
                address=activity.address,
                estimated_cost=activity.estimated_cost,
                currency=activity.currency,
                booking_required=activity.booking_required,
                booking_url=activity.booking_url,
                tips=activity.tips,
                is_custom=activity.is_custom,
                order=activity.order
            )
        
        # Copy local experiences
        for experience in version_to_restore.local_experiences.all():
            LocalExperience.objects.create(
                itinerary=new_itinerary,
                name=experience.name,
                category=experience.category,
                description=experience.description,
                location_name=experience.location_name,
                latitude=experience.latitude,
                longitude=experience.longitude,
                estimated_cost=experience.estimated_cost,
                best_time=experience.best_time,
                insider_tip=experience.insider_tip,
                priority=experience.priority
            )
        
        logger.info(f"Restored version {version_to_restore.version} as new version {new_itinerary.version}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Version {version_to_restore.version} restored successfully',
            'new_version_id': str(new_itinerary.id),
            'new_version_number': new_itinerary.version
        })
        
    except Exception as e:
        logger.error(f"Failed to restore version: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Error restoring version: {str(e)}'
        }, status=500)


@login_required
def compare_versions(request):
    """
    Compare two versions of an itinerary
    
    Query params:
        trip_id: UUID of the TripRequest
        version1: Version number 1
        version2: Version number 2
    """
    trip_id = request.GET.get('trip_id')
    version1_num = request.GET.get('version1')
    version2_num = request.GET.get('version2')
    
    if not all([trip_id, version1_num, version2_num]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    trip_request = get_object_or_404(TripRequest, id=trip_id, user=request.user)
    
    try:
        version1 = trip_request.itineraries.get(version=int(version1_num))
        version2 = trip_request.itineraries.get(version=int(version2_num))
        
        # Compare the versions
        comparison = compare_itinerary_data(version1, version2)
        
        context = {
            'trip_request': trip_request,
            'version1': version1,
            'version2': version2,
            'comparison': comparison,
        }
        
        return render(request, 'trips/compare_versions.html', context)
        
    except Itinerary.DoesNotExist:
        return JsonResponse({'error': 'Version not found'}, status=404)
    except Exception as e:
        logger.error(f"Comparison failed: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def compare_itinerary_data(version1, version2):
    """
    Compare two itinerary versions and return differences
    
    Args:
        version1: First Itinerary object
        version2: Second Itinerary object
        
    Returns:
        dict: Comparison results
    """
    comparison = {
        'cost_diff': float(version1.total_cost) - float(version2.total_cost),
        'activity_count_diff': version1.activities.count() - version2.activities.count(),
        'changes': []
    }
    
    # Compare days
    v1_days = {day['day']: day for day in version1.generated_data.get('days', [])}
    v2_days = {day['day']: day for day in version2.generated_data.get('days', [])}
    
    for day_num in sorted(set(v1_days.keys()) | set(v2_days.keys())):
        if day_num in v1_days and day_num in v2_days:
            # Day exists in both - check for changes
            v1_activities = v1_days[day_num].get('activities', [])
            v2_activities = v2_days[day_num].get('activities', [])
            
            if len(v1_activities) != len(v2_activities):
                comparison['changes'].append({
                    'type': 'modified',
                    'day': day_num,
                    'description': f"Day {day_num}: Activity count changed from {len(v2_activities)} to {len(v1_activities)}"
                })
            
            # Check for activity name changes
            v1_names = [a.get('name', '') for a in v1_activities]
            v2_names = [a.get('name', '') for a in v2_activities]
            
            added = set(v1_names) - set(v2_names)
            removed = set(v2_names) - set(v1_names)
            
            if added:
                for name in added:
                    comparison['changes'].append({
                        'type': 'added',
                        'day': day_num,
                        'description': f"Day {day_num}: Added '{name}'"
                    })
            
            if removed:
                for name in removed:
                    comparison['changes'].append({
                        'type': 'removed',
                        'day': day_num,
                        'description': f"Day {day_num}: Removed '{name}'"
                    })
        
        elif day_num in v1_days:
            comparison['changes'].append({
                'type': 'added',
                'day': day_num,
                'description': f"Day {day_num}: Added to itinerary"
            })
        else:
            comparison['changes'].append({
                'type': 'removed',
                'day': day_num,
                'description': f"Day {day_num}: Removed from itinerary"
            })
    
    return comparison

@login_required
@require_http_methods(["POST"])
def delete_version(request, itinerary_id):
    """
    Delete a specific version of an itinerary
    Cannot delete the active version
    
    Args:
        request: HTTP request
        itinerary_id: UUID of the version to delete
    """
    version_to_delete = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if version_to_delete.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Prevent deleting active version
    if version_to_delete.is_active:
        return JsonResponse({
            'status': 'error',
            'message': 'Cannot delete the active version'
        }, status=400)
    
    try:
        version_number = version_to_delete.version
        trip_id = version_to_delete.trip_request.id
        
        # Delete the version
        version_to_delete.delete()
        
        logger.info(f"Deleted version {version_number} for trip {trip_id}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Version {version_number} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete version: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Error deleting version: {str(e)}'
        }, status=500)


@login_required
@require_POST
def delete_trip(request, trip_id):
    """
    Delete a trip request and all associated data
    Uses database transaction to ensure data integrity
    """
    trip_request = get_object_or_404(TripRequest, id=trip_id, user=request.user)
    
    # Store destination name before deletion
    destination = trip_request.destination
    trip_duration = trip_request.duration
    
    try:
        # Use transaction to ensure all related data is deleted properly
        with transaction.atomic():
            # Get counts for logging
            itinerary_count = trip_request.itineraries.count()
            
            # Log deletion for audit trail
            logger.info(
                f"User {request.user.username} is deleting trip {trip_id} "
                f"to {destination} with {itinerary_count} itinerary version(s)"
            )
            
            # Delete the trip (cascading will handle related objects)
            trip_request.delete()
            
            # Success message with details
            messages.success(
                request,
                f'Trip to {destination} ({trip_duration} days) has been successfully deleted. '
                f'{itinerary_count} itinerary version(s) were also removed.'
            )
            
            logger.info(f"Trip {trip_id} successfully deleted by user {request.user.username}")
            
    except Exception as e:
        # Log the error
        logger.error(
            f"Failed to delete trip {trip_id} for user {request.user.username}: {str(e)}",
            exc_info=True
        )
        
        # Show error message to user
        messages.error(
            request,
            f'Failed to delete trip to {destination}. Please try again or contact support if the issue persists.'
        )
    
    return redirect('trips:my_trips')


@login_required
@require_POST
def bulk_delete_trips(request):
    """
    Delete multiple trips at once
    Expects JSON body with array of trip IDs
    """
    try:
        data = json.loads(request.body)
        trip_ids = data.get('trip_ids', [])
        
        if not trip_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'No trip IDs provided'
            }, status=400)
        
        # Get trips owned by user
        trips = TripRequest.objects.filter(
            id__in=trip_ids,
            user=request.user
        )
        
        deleted_count = trips.count()
        
        if deleted_count == 0:
            return JsonResponse({
                'status': 'error',
                'message': 'No valid trips found to delete'
            }, status=404)
        
        # Delete in transaction
        with transaction.atomic():
            trips.delete()
            logger.info(f"User {request.user.username} bulk deleted {deleted_count} trips")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Successfully deleted {deleted_count} trip(s)',
            'deleted_count': deleted_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Bulk delete failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to delete trips'
        }, status=500)


@login_required
def share_itinerary(request, itinerary_id):
    """Generate shareable link for itinerary"""
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        messages.error(request, 'You do not have permission to share this itinerary.')
        return redirect('trips:my_trips')
    
    # Generate a shareable URL (in production, consider using a share token)
    share_url = request.build_absolute_uri(
        f'/trips/shared/{itinerary_id}/'
    )
    
    context = {
        'itinerary': itinerary,
        'share_url': share_url,
    }
    
    return render(request, 'trips/share_itinerary.html', context)


def shared_itinerary_view(request, itinerary_id):
    """Public view of shared itinerary (read-only)"""
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Increment view count (even for public views)
    itinerary.increment_views()
    
    # Get activities grouped by day
    activities_by_day = {}
    for activity in itinerary.activities.all():
        if activity.day_number not in activities_by_day:
            activities_by_day[activity.day_number] = []
        activities_by_day[activity.day_number].append(activity)
    
    context = {
        'itinerary': itinerary,
        'trip_request': itinerary.trip_request,
        'activities_by_day': dict(sorted(activities_by_day.items())),
        'local_experiences': itinerary.local_experiences.all(),
        'is_shared_view': True,
    }
    
    return render(request, 'trips/shared_itinerary.html', context)


@login_required
def get_activity_details(request, activity_id):
    """Get detailed information about an activity"""
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Check permission
    if activity.itinerary.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    data = {
        'id': str(activity.id),
        'name': activity.name,
        'description': activity.description,
        'location': activity.location_name,
        'time': activity.start_time.strftime('%I:%M %p'),
        'duration': activity.duration_minutes,
        'cost': float(activity.estimated_cost),
        'tips': activity.tips,
        'category': activity.get_activity_type_display(),
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def chat_refine_itinerary(request, itinerary_id):
    """
    Refine itinerary using AI chat
    Process user's natural language request to modify itinerary
    """
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get user message
        message = request.POST.get('message', '').strip()
        
        if not message:
            return JsonResponse({
                'status': 'error',
                'message': 'Please enter a message'
            }, status=400)
        
        # Import AI refinement function
        from apps.ai_engine.chains import TravelPlannerChains
        
        # Initialize the chain
        planner = TravelPlannerChains()
        
        # Prepare itinerary summary for AI
        itinerary_summary = {
            'destination': itinerary.trip_request.destination,
            'duration': itinerary.trip_request.duration,
            'budget': float(itinerary.trip_request.budget),
            'currency': itinerary.trip_request.currency,
            'travel_style': itinerary.trip_request.travel_style,
            'current_itinerary': itinerary.generated_data,
        }
        
        logger.info(f"Processing refinement request: {message}")
        
        # Get AI refinement suggestions
        result = planner.refine_with_chat(itinerary_summary, message)
        
        logger.info(f"AI refinement result: {result}")
        
        if result and isinstance(result, dict):
            # Check if AI suggests changes
            updated_sections = result.get('updated_sections', {})
            
            if updated_sections and len(updated_sections) > 0:
                logger.info(f"Creating refined itinerary with updates: {list(updated_sections.keys())}")
                
                # Create new itinerary version with updates
                new_itinerary = create_refined_itinerary(
                    itinerary, 
                    updated_sections,
                    message
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': result.get('response_message', 'Itinerary updated successfully!'),
                    'understanding': result.get('understanding'),
                    'changes': result.get('changes', []),
                    'budget_impact': result.get('budget_impact'),
                    'redirect_url': f'/trips/itinerary/{new_itinerary.id}/',
                    'new_version': True
                })
            else:
                # AI understood but no changes needed
                logger.info("No updates needed or AI didn't provide updated sections")
                return JsonResponse({
                    'status': 'success',
                    'message': result.get('response_message', 'I understand your request. Your current itinerary looks good!'),
                    'understanding': result.get('understanding'),
                    'changes': result.get('changes', []),
                    'new_version': False
                })
        else:
            logger.error(f"Invalid result from AI: {result}")
            return JsonResponse({
                'status': 'error',
                'message': 'Sorry, I had trouble understanding that request. Could you rephrase?'
            }, status=400)
        
    except Exception as e:
        logger.error(f"Chat refinement failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Error processing request: {str(e)}'
        }, status=500)


def create_refined_itinerary(original_itinerary, updated_sections, user_message):
    """
    Create a new version of itinerary with AI refinements
    
    Args:
        original_itinerary: Original Itinerary object
        updated_sections: Dictionary with updated itinerary sections
        user_message: User's refinement request
        
    Returns:
        New Itinerary object
    """
    
    logger.info(f"Creating refined itinerary. Updated sections: {list(updated_sections.keys())}")
    
    # Deactivate old version
    original_itinerary.is_active = False
    original_itinerary.save()
    
    # Deep copy generated data to avoid modifying original
    new_generated_data = deepcopy(original_itinerary.generated_data)
    
    logger.info(f"Original data structure keys: {list(new_generated_data.keys())}")
    
    # Apply updates to generated data
    new_generated_data = merge_updated_sections(new_generated_data, updated_sections)
    
    logger.info(f"Merged data structure keys: {list(new_generated_data.keys())}")
    
    # Recalculate total cost if budget changed
    total_cost = original_itinerary.total_cost
    if 'total_cost' in updated_sections:
        total_cost = updated_sections['total_cost']
    
    # Create new itinerary version
    new_itinerary = Itinerary.objects.create(
        trip_request=original_itinerary.trip_request,
        title=original_itinerary.title,
        description=f"Refined: {user_message[:100]}" if user_message else original_itinerary.description,
        generated_data=new_generated_data,
        total_cost=total_cost,
        cost_breakdown=original_itinerary.cost_breakdown,
        weather_data=original_itinerary.weather_data,
        destination_info=original_itinerary.destination_info,
        version=original_itinerary.version + 1,
        is_active=True
    )
    
    logger.info(f"Created new itinerary version {new_itinerary.version} with ID {new_itinerary.id}")
    
    # Copy activities from generated_data
    recreate_activities_from_data(new_itinerary, new_generated_data)
    
    # Copy local experiences
    for experience in original_itinerary.local_experiences.all():
        LocalExperience.objects.create(
            itinerary=new_itinerary,
            name=experience.name,
            category=experience.category,
            description=experience.description,
            location_name=experience.location_name,
            latitude=experience.latitude,
            longitude=experience.longitude,
            estimated_cost=experience.estimated_cost,
            best_time=experience.best_time,
            insider_tip=experience.insider_tip,
            priority=experience.priority
        )
    
    return new_itinerary


def merge_updated_sections(original_data, updated_sections):
    """
    Intelligently merge updated sections into original data
    PRESERVES all original data that wasn't changed
    
    Args:
        original_data: Original generated_data dict
        updated_sections: Dict with updated sections from AI
        
    Returns:
        dict: Merged data
    """
    merged = deepcopy(original_data)
    
    logger.info(f"Merging sections: {list(updated_sections.keys())}")
    logger.info(f"Original days count: {len(merged.get('days', []))}")
    
    # Handle days updates (most common case)
    if 'days' in updated_sections:
        updated_days = updated_sections['days']
        original_days = merged.get('days', [])
        
        logger.info(f"Updating {len(updated_days)} days out of {len(original_days)} total days")
        
        if isinstance(updated_days, list):
            for updated_day in updated_days:
                day_num = updated_day.get('day')
                if day_num:
                    # Find the original day
                    day_found = False
                    for i, day in enumerate(original_days):
                        if day.get('day') == day_num:
                            logger.info(f"Merging day {day_num}")
                            
                            # IMPORTANT: Merge activities, don't replace completely
                            # Preserve all original activities if AI didn't provide full updates
                            original_activities = day.get('activities', [])
                            updated_activities = updated_day.get('activities', [])
                            
                            # If AI provided activities, check if they're complete
                            if updated_activities:
                                # Use updated activities
                                merged_activities = updated_activities
                            else:
                                # Keep original activities
                                merged_activities = original_activities
                            
                            # Merge the day, keeping original data where not updated
                            merged_day = {
                                'day': day_num,
                                'date': updated_day.get('date') or day.get('date'),
                                'title': updated_day.get('title') or day.get('title'),
                                'activities': merged_activities,
                                'accommodation': updated_day.get('accommodation') or day.get('accommodation'),
                                'transportation': updated_day.get('transportation') or day.get('transportation'),
                                'meals': updated_day.get('meals') or day.get('meals'),
                                'total_day_cost': updated_day.get('total_day_cost') or day.get('total_day_cost')
                            }
                            
                            original_days[i] = merged_day
                            day_found = True
                            logger.info(f"Day {day_num} merged with {len(merged_activities)} activities")
                            break
                    
                    if not day_found:
                        # Day not found, append it
                        logger.info(f"Appending new day {day_num}")
                        original_days.append(updated_day)
            
            merged['days'] = original_days
    
    # Handle other top-level updates
    for key in ['summary', 'overview', 'title', 'highlights', 'total_cost', 'accommodation', 'transportation']:
        if key in updated_sections:
            logger.info(f"Updating {key}")
            merged[key] = updated_sections[key]
    
    # Handle nested updates (accommodation, transportation per day)
    if 'accommodation_updates' in updated_sections:
        for day_num, accommodation in updated_sections['accommodation_updates'].items():
            for day in merged.get('days', []):
                if day.get('day') == int(day_num):
                    day['accommodation'] = accommodation
                    logger.info(f"Updated accommodation for day {day_num}")
    
    if 'transportation_updates' in updated_sections:
        for day_num, transportation in updated_sections['transportation_updates'].items():
            for day in merged.get('days', []):
                if day.get('day') == int(day_num):
                    day['transportation'] = transportation
                    logger.info(f"Updated transportation for day {day_num}")
    
    logger.info(f"Merge complete. Final days count: {len(merged.get('days', []))}")
    
    return merged


def recreate_activities_from_data(itinerary, generated_data):
    """
    Recreate Activity objects from generated_data to match Activity model exactly
    
    Args:
        itinerary: Itinerary object
        generated_data: Dict containing days and activities
    """
    from apps.trips.models import Activity
    from datetime import time
    
    logger.info("Recreating activities from generated data")
    logger.info(f"Generated data keys: {list(generated_data.keys())}")
    
    days = generated_data.get('days', [])
    logger.info(f"Number of days: {len(days)}")
    
    for day in days:
        day_number = day.get('day', 1)
        activities = day.get('activities', [])
        
        logger.info(f"Day {day_number}: {len(activities)} activities")
        
        for idx, activity_data in enumerate(activities):
            # Debug: Log the activity data structure
            logger.info(f"Activity {idx} keys: {list(activity_data.keys())}")
            logger.info(f"Activity {idx} data: {activity_data}")
            
            # Extract values with multiple possible keys
            name = (activity_data.get('name') or 
                   activity_data.get('activity_name') or 
                   activity_data.get('title') or 
                   f"Activity {idx + 1}")
            
            # Parse duration (handle both minutes and text like "1 hour")
            duration = parse_duration_to_minutes(
                activity_data.get('duration') or 
                activity_data.get('duration_minutes') or 
                120
            )
            
            # Parse cost (handle both numeric and text)
            cost = parse_cost(
                activity_data.get('cost') or 
                activity_data.get('estimated_cost') or 
                activity_data.get('price') or 
                0
            )
            
            # Parse start_time - handle multiple formats
            start_time = parse_time(
                activity_data.get('start_time') or 
                activity_data.get('time') or 
                None
            )
            
            # Parse coordinates
            latitude = parse_coordinate(
                activity_data.get('latitude') or 
                activity_data.get('lat')
            )
            longitude = parse_coordinate(
                activity_data.get('longitude') or 
                activity_data.get('lon') or 
                activity_data.get('lng')
            )
            
            # Parse activity type - try multiple keys
            raw_type = (activity_data.get('type') or 
                       activity_data.get('activity_type') or 
                       activity_data.get('category') or 
                       'sightseeing')
            activity_type = normalize_activity_type(raw_type)
            
            # Parse time_slot - try multiple keys
            raw_slot = (activity_data.get('time_slot') or 
                       activity_data.get('slot') or 
                       activity_data.get('period') or 
                       'morning')
            time_slot = normalize_time_slot(raw_slot)
            
            # Get location with fallbacks
            location = (activity_data.get('location') or 
                       activity_data.get('location_name') or 
                       activity_data.get('place') or 
                       '')
            
            # Get description
            description = (activity_data.get('description') or 
                         activity_data.get('details') or 
                         '')
            
            logger.info(f"Creating activity: {name} at {start_time} ({time_slot})")
            
            # Create activity
            Activity.objects.create(
                itinerary=itinerary,
                day_number=day_number,
                time_slot=time_slot,
                start_time=start_time,
                duration_minutes=duration,
                name=name,
                description=description,
                activity_type=activity_type,
                location_name=location,
                latitude=latitude,
                longitude=longitude,
                address=activity_data.get('address', ''),
                estimated_cost=cost,
                currency=itinerary.trip_request.currency,
                booking_required=parse_boolean(activity_data.get('booking_required', False)),
                booking_url=activity_data.get('booking_url', ''),
                tips=activity_data.get('tips', ''),
                is_custom=False,
                order=idx
            )
    
    activity_count = Activity.objects.filter(itinerary=itinerary).count()
    logger.info(f"Created {activity_count} activities")


def parse_time(time_value):
    """
    Parse time value to Python time object
    
    Args:
        time_value: Can be string like "09:00", "9:00 AM", or time object
        
    Returns:
        time: Python time object
    """
    from datetime import time as dt_time
    import re
    
    if isinstance(time_value, dt_time):
        return time_value
    
    if not time_value:
        return dt_time(9, 0)  # Default to 9:00 AM
    
    if isinstance(time_value, str):
        time_value = time_value.strip()
        
        # Handle 24-hour format (e.g., "09:00", "14:30")
        match = re.match(r'(\d{1,2}):(\d{2})', time_value)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            # Handle AM/PM if present
            if 'pm' in time_value.lower() and hour < 12:
                hour += 12
            elif 'am' in time_value.lower() and hour == 12:
                hour = 0
            
            # Validate
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return dt_time(hour, minute)
        
        # Try parsing just hour (e.g., "9", "14")
        try:
            hour = int(time_value)
            if 0 <= hour <= 23:
                return dt_time(hour, 0)
        except ValueError:
            pass
    
    # Default fallback
    logger.warning(f"Could not parse time: {time_value}, defaulting to 09:00")
    return dt_time(9, 0)


def parse_coordinate(coord_value):
    """
    Parse coordinate value to Decimal
    
    Args:
        coord_value: Can be float, int, string, or None
        
    Returns:
        Decimal or None: Parsed coordinate
    """
    from decimal import Decimal, InvalidOperation
    
    if coord_value is None:
        return None
    
    try:
        # Convert to string first, then to Decimal
        coord_str = str(coord_value).strip()
        if coord_str:
            return Decimal(coord_str)
    except (InvalidOperation, ValueError):
        logger.warning(f"Could not parse coordinate: {coord_value}")
    
    return None


def normalize_activity_type(activity_type):
    """
    Normalize activity type to match model choices
    
    Args:
        activity_type: Raw activity type string
        
    Returns:
        str: Valid activity type
    """
    if not activity_type:
        return 'sightseeing'
    
    activity_type = activity_type.lower().strip()
    
    # Valid choices from model
    valid_types = {
        'sightseeing', 'food', 'adventure', 'relaxation',
        'cultural', 'entertainment', 'shopping', 'transport'
    }
    
    # Direct match
    if activity_type in valid_types:
        return activity_type
    
    # Mapping common variations
    type_mapping = {
        'dining': 'food',
        'restaurant': 'food',
        'meal': 'food',
        'breakfast': 'food',
        'lunch': 'food',
        'dinner': 'food',
        'tour': 'sightseeing',
        'visit': 'sightseeing',
        'activity': 'adventure',
        'sport': 'adventure',
        'rest': 'relaxation',
        'spa': 'relaxation',
        'culture': 'cultural',
        'museum': 'cultural',
        'show': 'entertainment',
        'performance': 'entertainment',
        'theater': 'entertainment',
        'market': 'shopping',
        'mall': 'shopping',
        'taxi': 'transport',
        'bus': 'transport',
        'train': 'transport',
        'flight': 'transport',
        'transportation': 'transport',
    }
    
    # Check mapping
    for key, value in type_mapping.items():
        if key in activity_type:
            return value
    
    # Default fallback
    return 'sightseeing'


def normalize_time_slot(time_slot):
    """
    Normalize time slot to match model choices
    
    Args:
        time_slot: Raw time slot string
        
    Returns:
        str: Valid time slot
    """
    if not time_slot:
        return 'morning'
    
    time_slot = time_slot.lower().strip()
    
    # Valid choices from model
    valid_slots = {'morning', 'afternoon', 'evening', 'night'}
    
    # Direct match
    if time_slot in valid_slots:
        return time_slot
    
    # Mapping variations
    slot_mapping = {
        'am': 'morning',
        'breakfast': 'morning',
        'early': 'morning',
        'pm': 'afternoon',
        'lunch': 'afternoon',
        'noon': 'afternoon',
        'midday': 'afternoon',
        'eve': 'evening',
        'dinner': 'evening',
        'sunset': 'evening',
        'late': 'night',
        'midnight': 'night',
    }
    
    # Check mapping
    for key, value in slot_mapping.items():
        if key in time_slot:
            return value
    
    # Default fallback
    return 'morning'


def parse_boolean(value):
    """
    Parse boolean value from various formats
    
    Args:
        value: Can be bool, string, int, etc.
        
    Returns:
        bool: Parsed boolean
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'on')
    
    if isinstance(value, int):
        return value != 0
    
    return False


def copy_activities_from_original(new_itinerary, original_itinerary):
    """
    Copy activities directly from original itinerary (preserves all data perfectly)
    
    Args:
        new_itinerary: New Itinerary object to copy TO
        original_itinerary: Original Itinerary object to copy FROM
    """
    logger.info("Copying activities directly from original itinerary")
    
    for activity in original_itinerary.activities.all():
        Activity.objects.create(
            itinerary=new_itinerary,
            day_number=activity.day_number,
            time_slot=activity.time_slot,
            start_time=activity.start_time,
            duration_minutes=activity.duration_minutes,
            name=activity.name,
            description=activity.description,
            activity_type=activity.activity_type,
            location_name=activity.location_name,
            latitude=activity.latitude,
            longitude=activity.longitude,
            address=activity.address,
            estimated_cost=activity.estimated_cost,
            currency=activity.currency,
            booking_required=activity.booking_required,
            booking_url=activity.booking_url,
            tips=activity.tips,
            is_custom=activity.is_custom,
            order=activity.order
        )
    
    logger.info(f"Copied {new_itinerary.activities.count()} activities from original")


def parse_duration_to_minutes(duration):
    """
    Parse duration value to minutes (integer)
    
    Args:
        duration: Can be int (minutes), or string like "1 hour", "30 minutes", "2.5 hours"
        
    Returns:
        int: Duration in minutes
    """
    if isinstance(duration, int):
        return duration
    
    if isinstance(duration, (float)):
        return int(duration)
    
    if isinstance(duration, str):
        duration = duration.lower().strip()
        
        # Try to extract number and unit
        import re
        
        # Match patterns like "1 hour", "30 minutes", "2.5 hours", "90 mins"
        hour_match = re.search(r'(\d+\.?\d*)\s*(hour|hr|h)', duration)
        minute_match = re.search(r'(\d+\.?\d*)\s*(minute|min|m)', duration)
        
        if hour_match:
            hours = float(hour_match.group(1))
            return int(hours * 60)
        elif minute_match:
            minutes = float(minute_match.group(1))
            return int(minutes)
        else:
            # Try to parse as just a number
            try:
                return int(float(duration))
            except:
                logger.warning(f"Could not parse duration: {duration}, defaulting to 120 minutes")
                return 120
    
    # Default fallback
    return 120


def parse_cost(cost):
    """
    Parse cost value to float
    
    Args:
        cost: Can be numeric, or string like "$50", "50 USD", "50.00"
        
    Returns:
        float: Cost as number
    """
    if isinstance(cost, (int, float)):
        return float(cost)
    
    if isinstance(cost, str):
        # Remove currency symbols and text
        import re
        cost = re.sub(r'[^\d.]', '', cost)
        try:
            return float(cost) if cost else 0.0
        except:
            logger.warning(f"Could not parse cost: {cost}, defaulting to 0")
            return 0.0
    
    return 0.0


@login_required
def update_activity(request, activity_id):
    """Update activity details"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Check permission
    if activity.itinerary.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Update allowed fields
        if 'notes' in data:
            activity.tips = data['notes']
        if 'is_completed' in data:
            activity.is_custom = data['is_completed']  # Repurpose field
        
        activity.save()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Failed to update activity: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
    
    
@login_required
def get_map_data(request, itinerary_id):
    """
    API endpoint to get map data for an itinerary
    Returns activities with coordinates in JSON format
    """
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get all activities with their locations
        activities = itinerary.activities.all().order_by('day_number', 'start_time')
        
        activities_data = []
        for activity in activities:
            # Only include activities with valid coordinates
            if activity.latitude and activity.longitude:
                activities_data.append({
                    'id': str(activity.id),
                    'name': activity.name,
                    'day': activity.day_number,
                    'time': activity.start_time.strftime('%I:%M %p'),
                    'location': activity.location_name,
                    'description': activity.description[:150] + '...' if len(activity.description) > 150 else activity.description,
                    'activity_type': activity.activity_type,
                    'lat': float(activity.latitude),
                    'lng': float(activity.longitude),
                    'cost': f"{activity.currency} {float(activity.estimated_cost)}",
                    'address': activity.address or ''
                })
        
        return JsonResponse({
            'status': 'success',
            'activities': activities_data,
            'total_days': itinerary.trip_request.duration,
            'destination': itinerary.trip_request.destination
        })
        
    except Exception as e:
        logger.error(f"Error fetching map data: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to load map data'
        }, status=500)
        
        
@login_required
@require_http_methods(["POST"])
def refresh_weather(request, itinerary_id):
    """
    Manually refresh weather data for an itinerary
    
    Args:
        request: HTTP request
        itinerary_id: UUID of the itinerary
        
    Returns:
        JsonResponse with updated weather data
    """
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Check permission
    if itinerary.trip_request.user != request.user:
        return JsonResponse({
            'status': 'error',
            'message': 'Permission denied'
        }, status=403)
    
    try:
        logger.info(f"Manual weather refresh requested for itinerary {itinerary_id}")
        logger.info(f"Destination: {itinerary.trip_request.destination}")
        logger.info(f"Destination info: {itinerary.destination_info}")
        
        # Call synchronous version for immediate response
        result = update_weather_data_sync(str(itinerary_id))
        
        logger.info(f"Weather update result: {result}")
        
        if result['status'] == 'success':
            # Refresh the itinerary to get updated weather data
            itinerary.refresh_from_db()
            
            # Format weather data for response
            weather_html = format_weather_html(itinerary.weather_data)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Weather data refreshed successfully',
                'weather_data': itinerary.weather_data,
                'weather_html': weather_html,
                'last_updated': itinerary.weather_last_updated.isoformat() if hasattr(itinerary, 'weather_last_updated') and itinerary.weather_last_updated else None
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result.get('message', 'Failed to refresh weather data')
            }, status=500)
            
    except Exception as e:
        logger.error(f"Weather refresh failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Error refreshing weather: {str(e)}'
        }, status=500)


def format_weather_html(weather_data):
    """
    Format weather data as HTML for dynamic updates
    
    Args:
        weather_data: Dictionary with weather information
        
    Returns:
        str: HTML string
    """
    if not weather_data or 'days' not in weather_data:
        return '<p class="text-gray-500">No weather data available</p>'
    
    html_parts = []
    
    for day in weather_data['days'][:5]:  # First 5 days
        html_parts.append(f'''
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <div>
                <p class="font-semibold text-gray-800">{day.get('date', 'N/A')}</p>
                <p class="text-sm text-gray-600">{day.get('description', 'N/A').title()}</p>
            </div>
            <div class="text-right">
                <p class="text-2xl font-bold text-gray-800">{day.get('temp_avg', 'N/A')}°C</p>
                <p class="text-xs text-gray-500">{day.get('temp_min', 'N/A')}° - {day.get('temp_max', 'N/A')}°</p>
            </div>
        </div>
        ''')
    
    return ''.join(html_parts)