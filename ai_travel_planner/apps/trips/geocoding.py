import requests, time, logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def geocode_location(location_name: str, city: str = None, country: str = None) -> Optional[Tuple[float, float]]:
    """ 
    Args:
        location_name: Name of the location/place
        city: City name (optional, improves accuracy)
        country: Country name (optional, improves accuracy)
        
    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    try:
        query_parts = [location_name]
        if city:
            query_parts.append(city)
        if country:
            query_parts.append(country)
        
        query = ", ".join(query_parts)
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 1
        }
        
        headers = {
            'User-Agent': 'AI-Travel-Planner/1.0'  
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                logger.info(f"Geocoded '{query}' to ({lat}, {lon})")
                return (lat, lon)
        
        logger.warning(f"Could not geocode location: {query}")
        return None
        
    except Exception as e:
        logger.error(f"Geocoding error for '{location_name}': {str(e)}")
        return None


def add_coordinates_to_activity(activity, destination_city=None, destination_country=None):
    """
    Args:
        activity: Activity model instance
        destination_city: City name from trip request
        destination_country: Country name from trip request
    """
    if activity.latitude and activity.longitude:
        return  
    
    coords = geocode_location(
        activity.location_name,
        city=destination_city,
        country=destination_country
    )
    
    if coords:
        activity.latitude, activity.longitude = coords
        activity.save()
        logger.info(f"Added coordinates to activity: {activity.name}")
    else:
        if destination_city:
            city_coords = geocode_location(destination_city, country=destination_country)
            if city_coords:
                activity.latitude, activity.longitude = city_coords
                activity.save()
                logger.warning(f"Using city center coordinates for: {activity.name}")
