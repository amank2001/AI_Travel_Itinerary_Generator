from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
import logging, time
from decimal import Decimal
from .geocoding import add_coordinates_to_activity
from .models import TripRequest, Itinerary, Activity, LocalExperience
from apps.external_apis.weather import get_weather_forecast
from apps.external_apis.maps import get_location_coordinates, get_attractions
from apps.ai_engine.chains import generate_itinerary


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_trip_itinerary(self, trip_request_id):
    """
    Main Celery task for generating a complete trip itinerary
    
    Args:
        trip_request_id: UUID of the TripRequest
        
    Returns:
        dict: Generation result
    """
    try:
        # Fetch trip request
        trip_request = TripRequest.objects.get(id=trip_request_id)
        trip_request.status = 'processing'
        trip_request.save()
        
        logger.info(f"Processing trip request: {trip_request_id}")
        
        # Step 1: Gather external data
        external_data = gather_external_data(trip_request)
        
        # Step 2: Prepare trip data for AI
        trip_data = prepare_trip_data(trip_request)
        
        # Step 3: Generate itinerary using AI
        result = generate_itinerary(trip_data, external_data)
        
        # Step 4: Save itinerary to database
        itinerary = save_itinerary_to_db(trip_request, result)
        
        # Step 5: Mark trip request as completed
        trip_request.mark_completed()
        
        # Step 6: Optionally send email notification (synchronously)
        try:
            from django.conf import settings
            if getattr(settings, 'SEND_EMAIL_NOTIFICATIONS', False):
                send_itinerary_email_sync(str(itinerary.id), trip_request.user.email)
        except Exception as e:
            logger.warning(f"Email notification failed (non-critical): {str(e)}")
        
        logger.info(f"Successfully generated itinerary: {itinerary.id}")
        
        return {
            'status': 'success',
            'itinerary_id': str(itinerary.id),
            'trip_request_id': str(trip_request_id)
        }
        
    except TripRequest.DoesNotExist:
        logger.error(f"TripRequest {trip_request_id} not found")
        return {'status': 'error', 'message': 'Trip request not found'}
        
    except Exception as e:
        logger.error(f"Itinerary generation failed: {str(e)}", exc_info=True)
        
        # Mark as failed and retry
        try:
            trip_request = TripRequest.objects.get(id=trip_request_id)
            trip_request.mark_failed(str(e))
        except:
            pass
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'message': str(e),
            'trip_request_id': str(trip_request_id)
        }


def gather_external_data(trip_request):
    """
    Gather data from external APIs
    
    Args:
        trip_request: TripRequest instance
        
    Returns:
        dict: External data
    """
    logger.info(f"Gathering external data for {trip_request.destination}")
    
    external_data = {}
    
    # Get location coordinates
    try:
        location = get_location_coordinates(trip_request.destination)
        if location:
            external_data['destination_info'] = location
            
            # Get weather forecast
            weather = get_weather_forecast(
                lat=location['lat'],
                lon=location['lng'],
                days=min(trip_request.duration, 7)
            )
            external_data['weather_data'] = weather
            
    except Exception as e:
        logger.warning(f"Failed to get location data: {str(e)}")
        external_data['destination_info'] = {}
        external_data['weather_data'] = {}
    
    # Get top attractions
    try:
        attractions = get_attractions(trip_request.destination, limit=15)
        external_data['attractions'] = attractions
    except Exception as e:
        logger.warning(f"Failed to get attractions: {str(e)}")
        external_data['attractions'] = []
    
    return external_data


def prepare_trip_data(trip_request):
    """
    Prepare trip request data for AI processing
    
    Args:
        trip_request: TripRequest instance
        
    Returns:
        dict: Formatted trip data
    """
    return {
        'destination': trip_request.destination,
        'duration': trip_request.duration,
        'budget': float(trip_request.budget),
        'currency': trip_request.currency,
        'travel_style': trip_request.travel_style,
        'group_size': trip_request.group_size,
        'interests': trip_request.interests or [],
        'dietary_restrictions': trip_request.dietary_restrictions or [],
        'accommodation_preference': trip_request.accommodation_preference or 'hotel',
        'accessibility_needs': trip_request.accessibility_needs or '',
        'start_date': trip_request.start_date.isoformat(),
        'season': trip_request.start_date.strftime('%B')  # Month name
    }


def save_itinerary_to_db(trip_request, ai_result):
    """
    Save generated itinerary to database
    
    Args:
        trip_request: TripRequest instance
        ai_result: Result from AI generation
        
    Returns:
        Itinerary: Saved itinerary instance
    """
    logger.info("Saving itinerary to database")
    
    itinerary_data = ai_result.get('itinerary', {})
    
    # Create main itinerary
    itinerary = Itinerary.objects.create(
        trip_request=trip_request,
        title=itinerary_data.get('trip_title', f"{trip_request.destination} Trip"),
        description=itinerary_data.get('overview', ''),
        generated_data=itinerary_data,
        total_cost=Decimal(str(ai_result.get('total_cost', 0))),
        cost_breakdown=calculate_cost_breakdown(itinerary_data),
        weather_data=ai_result.get('weather_data', {}),
        destination_info=ai_result.get('destination_info', {}),
        version=1,
        is_active=True
    )
    
    # Save individual activities
    for day_data in itinerary_data.get('days', []):
        day_number = day_data.get('day', 1)
        order = 0
        
        for activity_data in day_data.get('activities', []):
            create_activity_from_data(itinerary, day_number, activity_data, order)
            order += 1
    
    # Save local experiences
    for exp_data in ai_result.get('local_experiences', []):
        create_local_experience_from_data(itinerary, exp_data)
    
    logger.info(f"Itinerary saved: {itinerary.id}")
    return itinerary


def create_activity_from_data(itinerary, day_number, activity_data, order):
    """Create Activity instance from AI-generated data"""
    from datetime import datetime
    
    # Parse time
    time_str = activity_data.get('time', '09:00 AM')
    try:
        start_time = datetime.strptime(time_str, '%I:%M %p').time()
    except:
        start_time = datetime.strptime('09:00 AM', '%I:%M %p').time()
    
    # Parse duration
    duration_str = activity_data.get('duration', '2 hours')
    duration_minutes = parse_duration_to_minutes(duration_str)
    
    # Determine time slot
    hour = start_time.hour
    if hour < 12:
        time_slot = 'morning'
    elif hour < 17:
        time_slot = 'afternoon'
    elif hour < 21:
        time_slot = 'evening'
    else:
        time_slot = 'night'
    
    activity = Activity.objects.create(
        itinerary=itinerary,
        day_number=day_number,
        time_slot=time_slot,
        start_time=start_time,
        duration_minutes=duration_minutes,
        name=activity_data.get('activity', 'Activity'),
        description=activity_data.get('description', ''),
        activity_type=map_category_to_type(activity_data.get('category', 'sightseeing')),
        location_name=activity_data.get('location', ''),
        estimated_cost=Decimal(str(activity_data.get('cost', 0))),
        currency=itinerary.trip_request.currency,
        tips=activity_data.get('tips', ''),
        order=order
    )
    
    try:
        from apps.trips.geocoding import add_coordinates_to_activity
    
        add_coordinates_to_activity(
            activity=activity,
            destination_city=activity.itinerary.trip_request.destination,
            destination_country=activity.itinerary.trip_request.destination_country
        )
    
        import time
        time.sleep(1)
    
    except Exception as e:
        logger.warning(f"Could not add coordinates to activity {activity.name}: {str(e)}")


def create_local_experience_from_data(itinerary, exp_data):
    """Create LocalExperience instance from AI-generated data"""
    LocalExperience.objects.create(
        itinerary=itinerary,
        name=exp_data.get('name', 'Local Experience'),
        category=exp_data.get('category', 'hidden_gem'),
        description=exp_data.get('description', ''),
        estimated_cost=Decimal(str(exp_data.get('cost', 0))) if exp_data.get('cost') else None,
        best_time=exp_data.get('best_time', ''),
        insider_tip=exp_data.get('insider_tip', ''),
        priority=exp_data.get('priority', 1)
    )


def calculate_cost_breakdown(itinerary_data):
    """Calculate cost breakdown from itinerary data"""
    breakdown = {
        'accommodation': 0,
        'food': 0,
        'activities': 0,
        'transport': 0,
        'miscellaneous': 0
    }
    
    for day in itinerary_data.get('days', []):
        for activity in day.get('activities', []):
            cost = float(activity.get('cost', 0))
            category = activity.get('category', 'activities')
            
            if 'food' in category.lower() or 'restaurant' in category.lower():
                breakdown['food'] += cost
            elif 'transport' in category.lower():
                breakdown['transport'] += cost
            else:
                breakdown['activities'] += cost
    
    # Estimate accommodation (35% of non-food costs typically)
    other_costs = sum(breakdown.values())
    breakdown['accommodation'] = other_costs * 0.35
    breakdown['miscellaneous'] = other_costs * 0.10
    
    return breakdown


def parse_duration_to_minutes(duration_str):
    """Parse duration string to minutes"""
    duration_str = duration_str.lower()
    
    if 'hour' in duration_str:
        try:
            hours = float(duration_str.split('hour')[0].strip())
            return int(hours * 60)
        except:
            return 120
    elif 'minute' in duration_str:
        try:
            minutes = int(duration_str.split('minute')[0].strip())
            return minutes
        except:
            return 60
    
    return 120  # Default 2 hours


def map_category_to_type(category):
    """Map AI category to Activity type"""
    category_mapping = {
        'sightseeing': 'sightseeing',
        'food': 'food',
        'dining': 'food',
        'restaurant': 'food',
        'adventure': 'adventure',
        'relaxation': 'relaxation',
        'cultural': 'cultural',
        'culture': 'cultural',
        'entertainment': 'entertainment',
        'shopping': 'shopping',
        'transport': 'transport',
        'transportation': 'transport'
    }
    
    return category_mapping.get(category.lower(), 'sightseeing')


def create_itinerary_version(original_itinerary, modified_day_number, new_day_data):
    """Create a new version of itinerary with modified day"""

    original_itinerary.is_active = False
    original_itinerary.save()
    
    new_generated_data = original_itinerary.generated_data.copy()
    for i, day in enumerate(new_generated_data['days']):
        if day['day'] == modified_day_number:
            new_generated_data['days'][i] = new_day_data
            break
    
    new_itinerary = Itinerary.objects.create(
        trip_request=original_itinerary.trip_request,
        title=original_itinerary.title,
        description=original_itinerary.description,
        generated_data=new_generated_data,
        total_cost=original_itinerary.total_cost,  
        cost_breakdown=original_itinerary.cost_breakdown,
        weather_data=original_itinerary.weather_data,
        destination_info=original_itinerary.destination_info,
        version=original_itinerary.version + 1,
        is_active=True
    )
    
    return new_itinerary


@shared_task
def update_weather_data(itinerary_id):
    """
    Update weather data for an itinerary (can be scheduled OR manually triggered)
    
    Args:
        itinerary_id: UUID of the Itinerary
        
    Returns:
        dict: Status and message
    """
    try:
        itinerary = Itinerary.objects.get(id=itinerary_id)
        destination_info = itinerary.destination_info
        
        logger.info(f"=== Weather Update Debug Info ===")
        logger.info(f"Itinerary ID: {itinerary_id}")
        logger.info(f"Destination from trip_request: {itinerary.trip_request.destination}")
        logger.info(f"Destination_info: {destination_info}")
        
        # Try multiple ways to get location
        lat = None
        lon = None
        city_name = None
        
        # Method 1: Check destination_info
        if destination_info:
            lat = destination_info.get('lat') or destination_info.get('latitude')
            lon = destination_info.get('lng') or destination_info.get('longitude') or destination_info.get('lon')
            city_name = destination_info.get('name') or destination_info.get('city')
            logger.info(f"From destination_info - lat: {lat}, lon: {lon}, city: {city_name}")
        
        # Method 2: Use trip request destination as city name
        if not (lat and lon) and not city_name:
            city_name = itinerary.trip_request.destination
            logger.info(f"Using city name from trip request: {city_name}")
        
        logger.info(f"Final values - lat: {lat}, lon: {lon}, city_name: {city_name}")
        logger.info(f"=== End Debug Info ===")
        
        # If we have coordinates, use them
        if lat and lon:
            logger.info(f"Fetching weather for itinerary {itinerary_id} at {lat}, {lon}")
            weather = get_weather_forecast(lat=lat, lon=lon, days=min(itinerary.trip_request.duration, 7))
        # If we only have city name, use that
        elif city_name:
            logger.info(f"Fetching weather for itinerary {itinerary_id} by city: {city_name}")
            weather = get_weather_forecast(city_name=city_name, days=min(itinerary.trip_request.duration, 7))
        else:
            logger.warning(f"No location info for itinerary {itinerary_id}")
            return {
                'status': 'error',
                'message': 'Location information not available. Please ensure destination is set.'
            }
        
        # Fetch weather data
        logger.info(f"Fetching weather for itinerary {itinerary_id} at {lat}, {lon}")
        
        weather = get_weather_forecast(
            lat=lat,
            lon=lon,
            days=min(itinerary.trip_request.duration, 7)
        )
        # If we have coordinates, use them
        if lat and lon:
            logger.info(f"Fetching weather for itinerary {itinerary_id} at {lat}, {lon}")
            weather = get_weather_forecast(lat=lat, lon=lon, days=min(itinerary.trip_request.duration, 7))
        # If we only have city name, use that
        elif city_name:
            logger.info(f"Fetching weather for itinerary {itinerary_id} by city: {city_name}")
            weather = get_weather_forecast(city_name=city_name, days=min(itinerary.trip_request.duration, 7))
        else:
            logger.warning(f"No location info for itinerary {itinerary_id}")
            return {
                'status': 'error',
                'message': 'Location information not available. Please ensure destination is set.'
            }
        
        if weather and weather.get('days'):
            # Update itinerary with new weather data
            itinerary.weather_data = weather
            itinerary.weather_last_updated = timezone.now()
            itinerary.save(update_fields=['weather_data', 'weather_last_updated'])
            
            logger.info(f"Successfully updated weather data for itinerary {itinerary_id}")
            
            return {
                'status': 'success',
                'message': 'Weather data updated successfully',
                'data': weather
            }
        else:
            logger.error(f"Weather API returned no data for itinerary {itinerary_id}")
            return {
                'status': 'error',
                'message': 'Failed to fetch weather data'
            }
            
    except Itinerary.DoesNotExist:
        logger.error(f"Itinerary {itinerary_id} not found")
        return {
            'status': 'error',
            'message': 'Itinerary not found'
        }
        
    except Exception as e:
        logger.error(f"Weather update failed for itinerary {itinerary_id}: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': f'Error updating weather: {str(e)}'
        }


def update_weather_data_sync(itinerary_id):
    """
    Synchronous version for manual refresh (no Celery delay)
    Call this directly from views for immediate response
    
    Args:
        itinerary_id: UUID of the Itinerary
        
    Returns:
        dict: Status and message
    """
    return update_weather_data(itinerary_id)


@shared_task
def bulk_update_weather_for_active_itineraries():
    """
    Scheduled task to update weather for all active itineraries
    Run this daily via Celery Beat
    """
    from datetime import timedelta
    
    # Get active itineraries with trips in the next 30 days
    upcoming_itineraries = Itinerary.objects.filter(
        is_active=True,
        trip_request__start_date__gte=timezone.now().date(),
        trip_request__start_date__lte=timezone.now().date() + timedelta(days=30)
    )
    
    updated = 0
    failed = 0
    
    for itinerary in upcoming_itineraries:
        try:
            result = update_weather_data(str(itinerary.id))
            if result['status'] == 'success':
                updated += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Failed to update weather for {itinerary.id}: {str(e)}")
            failed += 1
    
    logger.info(f"Bulk weather update complete: {updated} updated, {failed} failed")
    
    return {
        'status': 'success',
        'updated': updated,
        'failed': failed
    }

@shared_task
def send_itinerary_email(itinerary_id, user_email):
    """
    Send itinerary details via email (SYNCHRONOUS VERSION)
    Can be called directly: send_itinerary_email(id, email)
    Or async if Celery configured: send_itinerary_email.delay(id, email)
    
    Args:
        itinerary_id: UUID of the Itinerary
        user_email: Email address to send to
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        itinerary = Itinerary.objects.get(id=itinerary_id)
        
        context = {
            'itinerary': itinerary,
            'trip_request': itinerary.trip_request,
            'user': itinerary.trip_request.user,
        }
        
        try:
            html_message = render_to_string('trips/email/itinerary_ready.html', context)
        except:
            html_message = None
        
        plain_message = f"""
Hello {itinerary.trip_request.user.username},

Your travel itinerary for {itinerary.trip_request.destination} is ready!

Trip Details:
- Destination: {itinerary.trip_request.destination}
- Duration: {itinerary.trip_request.duration} days
- Start Date: {itinerary.trip_request.start_date}
- Budget: {itinerary.trip_request.currency} {itinerary.trip_request.budget}

View your complete itinerary at:
{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/trips/itinerary/{itinerary.id}/

Happy travels!
AI Travel Planner Team
        """
        
        send_mail(
            subject=f"Your {itinerary.trip_request.destination} Itinerary is Ready!",
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@aitravelplanner.com',
            recipient_list=[user_email],
            fail_silently=False
        )
        
        logger.info(f"Itinerary email sent to {user_email}")
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}


def send_itinerary_email_sync(itinerary_id, user_email):
    """
    Send email synchronously (without Celery)
    Use this when you want immediate email sending
    """
    return send_itinerary_email(itinerary_id, user_email)


def batch_geocode_activities():
    """
    Run this in Django shell to geocode all existing activities
    Usage:
    python manage.py shell
    >>> from apps.trips.geocoding import batch_geocode_activities
    >>> batch_geocode_activities()
    """
    from apps.trips.models import Activity
    
    activities = Activity.objects.filter(latitude__isnull=True)
    total = activities.count()
    
    print(f"Found {total} activities without coordinates")
    
    for i, activity in enumerate(activities, 1):
        print(f"\nProcessing {i}/{total}: {activity.name}")
        
        destination = activity.itinerary.trip_request.destination
        country = activity.itinerary.trip_request.destination_country
        
        add_coordinates_to_activity(activity, destination, country)
        
        if i < total:
            time.sleep(1)
    
    print(f"\n✓ Completed! Updated {total} activities")