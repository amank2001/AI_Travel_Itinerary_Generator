"""
Weather API Module - Simplified Version with Mock Fallback
Replaces the old complex weather.py
"""

import requests
import logging
import random
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)


# MAIN FUNCTION 

def get_weather_forecast(city_name=None, lat=None, lon=None, days=7):
    """
    Main weather fetching function with automatic fallback
    
    Args:
        city_name: City name (preferred method)
        lat: Latitude (optional)
        lon: Longitude (optional)
        days: Number of days
        
    Returns:
        dict: Weather forecast data
    """
    # If coordinates provided, convert to city name lookup
    if lat and lon and not city_name:
        city_name = "Location"  # Generic name for coordinate-based lookup
    
    if not city_name:
        logger.error("No location provided")
        return get_mock_weather("Unknown", days)
    
    # Try real API first
    api_key = getattr(settings, 'WEATHER_API_KEY', None)
    
    if not api_key:
        logger.warning(f"No API key, using mock weather for {city_name}")
        return get_mock_weather(city_name, days)
    
    try:
        logger.info(f"Fetching real weather for: {city_name}")
        return fetch_real_weather(city_name, days, api_key)
    except Exception as e:
        logger.warning(f"Real API failed: {str(e)}, using mock weather")
        return get_mock_weather(city_name, days)


# REAL WEATHER API

def fetch_real_weather(city_name, days, api_key):
    """Fetch real weather from OpenWeatherMap API"""
    
    # Step 1: Geocode city name
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {'q': city_name, 'limit': 1, 'appid': api_key}
    
    geo_response = requests.get(geo_url, params=geo_params, timeout=10)
    geo_response.raise_for_status()
    geo_data = geo_response.json()
    
    if not geo_data:
        raise ValueError(f"Location not found: {city_name}")
    
    lat = geo_data[0]['lat']
    lon = geo_data[0]['lon']
    location_name = geo_data[0]['name']
    
    logger.info(f"Found coordinates: {lat}, {lon}")
    
    # Step 2: Get weather forecast
    weather_url = "https://api.openweathermap.org/data/2.5/forecast"
    weather_params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric',
        'cnt': min(days * 8, 40)
    }
    
    weather_response = requests.get(weather_url, params=weather_params, timeout=10)
    weather_response.raise_for_status()
    weather_data = weather_response.json()
    
    # Step 3: Parse data
    return parse_weather_data(weather_data, location_name, days)


def parse_weather_data(api_data, location_name, days):
    """Parse OpenWeatherMap API response"""
    forecast = {'location': location_name, 'days': []}
    daily_data = {}
    
    for item in api_data.get('list', []):
        dt = datetime.fromtimestamp(item['dt'])
        date_key = dt.date()
        
        if date_key not in daily_data:
            daily_data[date_key] = {
                'date': date_key.isoformat(),
                'temps': [], 'conditions': [], 'descriptions': [],
                'humidity': [], 'wind_speed': []
            }
        
        daily_data[date_key]['temps'].append(item['main']['temp'])
        daily_data[date_key]['conditions'].append(item['weather'][0]['main'])
        daily_data[date_key]['descriptions'].append(item['weather'][0]['description'])
        daily_data[date_key]['humidity'].append(item['main']['humidity'])
        daily_data[date_key]['wind_speed'].append(item['wind']['speed'])
    
    for date_key in sorted(daily_data.keys())[:days]:
        data = daily_data[date_key]
        forecast['days'].append({
            'date': data['date'],
            'temp_min': round(min(data['temps']), 1),
            'temp_max': round(max(data['temps']), 1),
            'temp_avg': round(sum(data['temps']) / len(data['temps']), 1),
            'condition': max(set(data['conditions']), key=data['conditions'].count),
            'description': max(set(data['descriptions']), key=data['descriptions'].count),
            'humidity': round(sum(data['humidity']) / len(data['humidity'])),
            'wind_speed': round(sum(data['wind_speed']) / len(data['wind_speed']), 1)
        })
    
    return forecast


# MOCK WEATHER (Offline Fallback)

WEATHER_PATTERNS = {
    'tropical': {
        'conditions': ['Sunny', 'Partly Cloudy', 'Rainy', 'Thunderstorm'],
        'temp_range': (25, 35), 'humidity_range': (70, 90)
    },
    'temperate': {
        'conditions': ['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy'],
        'temp_range': (10, 25), 'humidity_range': (50, 70)
    },
    'cold': {
        'conditions': ['Cloudy', 'Snow', 'Clear', 'Overcast'],
        'temp_range': (-5, 10), 'humidity_range': (40, 60)
    },
    'desert': {
        'conditions': ['Clear', 'Sunny', 'Hot'],
        'temp_range': (20, 40), 'humidity_range': (20, 40)
    }
}

CITY_CLIMATE = {
    'kashmir': 'temperate', 'india': 'tropical', 'mumbai': 'tropical',
    'delhi': 'temperate', 'goa': 'tropical', 'manali': 'cold',
    'rajasthan': 'desert', 'jaipur': 'desert', 'paris': 'temperate',
    'london': 'temperate', 'new york': 'temperate', 'dubai': 'desert',
    'singapore': 'tropical', 'tokyo': 'temperate', 'sydney': 'temperate',
}


def get_mock_weather(city_name, days):
    """Generate realistic mock weather data (offline)"""
    logger.info(f"📍 Generating mock weather for: {city_name}")
    
    climate = get_climate_for_city(city_name)
    pattern = WEATHER_PATTERNS[climate]
    
    forecast = {
        'location': city_name.split(',')[0].strip(),
        'days': []
    }
    
    descriptions = {
        'Sunny': 'clear sky', 'Cloudy': 'broken clouds',
        'Rainy': 'light rain', 'Partly Cloudy': 'scattered clouds',
        'Thunderstorm': 'thunderstorm with rain', 'Snow': 'light snow',
        'Clear': 'clear sky', 'Overcast': 'overcast clouds', 'Hot': 'extremely hot'
    }
    
    for i in range(days):
        date = (datetime.now() + timedelta(days=i)).date()
        temp_min = random.randint(pattern['temp_range'][0], pattern['temp_range'][1] - 5)
        temp_max = temp_min + random.randint(5, 10)
        temp_avg = (temp_min + temp_max) // 2
        condition = random.choice(pattern['conditions'])
        
        forecast['days'].append({
            'date': date.isoformat(),
            'temp_min': temp_min,
            'temp_max': temp_max,
            'temp_avg': temp_avg,
            'condition': condition,
            'description': descriptions.get(condition, 'moderate weather'),
            'humidity': random.randint(*pattern['humidity_range']),
            'wind_speed': round(random.uniform(2, 15), 1)
        })
    
    logger.info(f"✅ Generated {days} days of mock weather")
    return forecast


def get_climate_for_city(city_name):
    """Determine climate type from city name"""
    city_lower = city_name.lower()
    for city_key, climate in CITY_CLIMATE.items():
        if city_key in city_lower:
            return climate
    return 'temperate'


# LEGACY COMPATIBILITY

class WeatherAPIClient:
    """Legacy compatibility - redirects to new functions"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'WEATHER_API_KEY', None)
    
    def get_forecast(self, lat, lon, days=7):
        return get_weather_forecast(lat=lat, lon=lon, days=days)
    
    def get_weather_by_city(self, city_name, days=7):
        return get_weather_forecast(city_name=city_name, days=days)


# TEST FUNCTION

def test_weather():
    """Test weather system"""
    print("\n" + "="*60)
    print("TESTING WEATHER SYSTEM")
    print("="*60)
    
    test_cities = ["Kashmir, India", "Paris, France", "Dubai, UAE"]
    
    for city in test_cities:
        print(f"\n🌍 {city}")
        print("-" * 40)
        result = get_weather_forecast(city_name=city, days=3)
        print(f"📍 {result['location']}")
        for day in result['days']:
            print(f"   {day['date']}: {day['condition']}, {day['temp_avg']}°C")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60 + "\n")