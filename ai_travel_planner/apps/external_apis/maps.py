import googlemaps
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class GoogleMapsClient:
    """Client for Google Maps API interactions"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            self.client = None
        else:
            self.client = googlemaps.Client(key=self.api_key)
    
    def geocode_location(self, address):
        """
        Get coordinates for an address
        
        Args:
            address: Address string
            
        Returns:
            dict: Location data with lat, lng, formatted_address
        """
        if not self.client:
            return None
        
        cache_key = f"geocode_{address.lower()}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            result = self.client.geocode(address)
            
            if result:
                location_data = {
                    'lat': result[0]['geometry']['location']['lat'],
                    'lng': result[0]['geometry']['location']['lng'],
                    'formatted_address': result[0]['formatted_address'],
                    'place_id': result[0]['place_id']
                }
                
                # Extract city and country if available
                for component in result[0].get('address_components', []):
                    if 'locality' in component['types']:
                        location_data['city'] = component['long_name']
                    if 'country' in component['types']:
                        location_data['country'] = component['long_name']
                        location_data['country_code'] = component['short_name']
                
                # Cache for 24 hours
                cache.set(cache_key, location_data, 86400)
                
                return location_data
                
        except Exception as e:
            logger.error(f"Geocoding failed: {str(e)}")
        return None
    
    def get_place_details(self, place_id):
        """
        Get detailed information about a place
        
        Args:
            place_id: Google Places ID
            
        Returns:
            dict: Place details
        """
        if not self.client:
            return None
        
        cache_key = f"place_details_{place_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            result = self.client.place(place_id)
            if result.get('status') == 'OK':
                place = result['result']
                place_data = {
                    'name': place.get('name'),
                    'address': place.get('formatted_address'),
                    'phone': place.get('formatted_phone_number'),
                    'rating': place.get('rating'),
                    'website': place.get('website'),
                    'opening_hours': place.get('opening_hours', {}).get('weekday_text', []),
                    'photos': [photo['photo_reference'] for photo in place.get('photos', [])[:3]],
                    'types': place.get('types', []),
                    'price_level': place.get('price_level'),
                }
                
                # Cache for 12 hours
                cache.set(cache_key, place_data, 43200)
                return place_data
            
        except Exception as e:
            logger.error(f"Place details request failed: {str(e)}")
        return None
    
    
    def search_nearby_places(self, lat, lng, place_type, radius=5000, keyword=None):
        """
        Search for places near a location
        
        Args:
            lat: Latitude
            lng: Longitude
            place_type: Type of place (restaurant, museum, etc.)
            radius: Search radius in meters
            keyword: Optional keyword filter
            
        Returns:
            list: List of places
        """
        if not self.client:
            return []
        
        cache_key = f"nearby_{lat}_{lng}_{place_type}_{radius}_{keyword}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            params = {
                'location': (lat, lng),
                'radius': radius,
                'type': place_type
            }
            
            if keyword:
                params['keyword'] = keyword
            
            result = self.client.places_nearby(**params)
            
            places = []
            for place in result.get('results', [])[:20]:
                places.append({
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'address': place.get('vicinity'),
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng'],
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total'),
                    'price_level': place.get('price_level'),
                    'types': place.get('types', []),
                })
            
            # Cache for 6 hours
            cache.set(cache_key, places, 21600)
            return places
            
        except Exception as e:
            logger.error(f"Nearby search failed: {str(e)}") 
        return []
    
    
    def get_top_attractions(self, city_name, limit=15):
        """
        Get top tourist attractions in a city
        
        Args:
            city_name: Name of the city
            limit: Maximum number of results
            
        Returns:
            list: Top attractions
        """
        location = self.geocode_location(city_name)
        if not location:
            return []
        
        attractions = self.search_nearby_places(
            location['lat'],
            location['lng'],
            'tourist_attraction',
            radius=10000
        )
        
        attractions.sort(
            key=lambda x: (x.get('rating', 0) * x.get('user_ratings_total', 0)),
            reverse=True
        )
        return attractions[:limit]
    
    
    def get_restaurants(self, lat, lng, cuisine_type=None, limit=10):
        """
        Get restaurant recommendations
        
        Args:
            lat: Latitude
            lng: Longitude
            cuisine_type: Optional cuisine filter
            limit: Maximum number of results
            
        Returns:
            list: Restaurant recommendations
        """
        restaurants = self.search_nearby_places(
            lat, lng,
            'restaurant',
            radius=5000,
            keyword=cuisine_type
        )
        
        restaurants.sort(
            key=lambda x: (x.get('rating', 0), x.get('user_ratings_total', 0)),
            reverse=True
        )
        return restaurants[:limit]
    
    
    def calculate_distance_matrix(self, origins, destinations):
        """
        Calculate travel time and distance between multiple points
        
        Args:
            origins: List of origin coordinates [(lat, lng), ...]
            destinations: List of destination coordinates [(lat, lng), ...]
            
        Returns:
            dict: Distance matrix data
        """
        if not self.client:
            return None
        
        try:
            result = self.client.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode='driving',
                units='metric'
            )
            
            if result.get('status') == 'OK':
                matrix = {
                    'origins': result['origin_addresses'],
                    'destinations': result['destination_addresses'],
                    'rows': []
                }
                
                for row in result['rows']:
                    elements = []
                    for element in row['elements']:
                        if element['status'] == 'OK':
                            elements.append({
                                'distance': element['distance']['value'],  # meters
                                'distance_text': element['distance']['text'],
                                'duration': element['duration']['value'],  # seconds
                                'duration_text': element['duration']['text']
                            })
                        else:
                            elements.append(None)
                    
                    matrix['rows'].append(elements)
                return matrix
                
        except Exception as e:
            logger.error(f"Distance matrix calculation failed: {str(e)}")
        return None
    
    
# Convenience functions
def get_location_coordinates(address):
    """Get coordinates for an address"""
    client = GoogleMapsClient()
    return client.geocode_location(address)


def get_attractions(city_name, limit=15):
    """Get top attractions in a city"""
    client = GoogleMapsClient()
    return client.get_top_attractions(city_name, limit)


def get_nearby_restaurants(lat, lng, cuisine_type=None, limit=10):
    """Get nearby restaurants"""
    client = GoogleMapsClient()
    return client.get_restaurants(lat, lng, cuisine_type, limit)


def calculate_travel_time(locations):
    """
    Calculate travel time between sequential locations
    
    Args:
        locations: List of (lat, lng) tuples
        
    Returns:
        list: Travel times between consecutive points
    """
    if len(locations) < 2:
        return []
    
    client = GoogleMapsClient()
    travel_times = []
    
    for i in range(len(locations) - 1):
        directions = client.get_directions(locations[i], locations[i + 1])
        if directions:
            travel_times.append({
                'from_index': i,
                'to_index': i + 1,
                'duration': directions['duration'],
                'duration_text': directions['duration_text'],
                'distance': directions['distance'],
                'distance_text': directions['distance_text']
            })
    
    return travel_times