import requests, logging
from django.conf import settings
from django.core.cache import cache
from decimal import Decimal

logger = logging.getLogger(__name__)

class CurrencyAPIClient:
    """Client for currency exchange rate operations"""
    
    BASE_URL = "https://api.exchangerate-api.com/v4/latest"
    
    ALT_BASE_URL = "https://api.exchangerate.host/latest"
    
    def __init__(self):
        self.api_key = settings.CURRENCY_API_KEY
    
    def get_exchange_rate(self, from_currency, to_currency):
        """
        Get exchange rate between two currencies
        
        Args:
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'EUR')
            
        Returns:
            float: Exchange rate
        """
        cache_key = f"exchange_rate_{from_currency}_{to_currency}"
        cached_rate = cache.get(cache_key)
        
        if cached_rate:
            return cached_rate
        
        try:
            url = f"{self.BASE_URL}/{from_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rate = data['rates'].get(to_currency)
            
            if rate:
                # Cache for 6 hours
                cache.set(cache_key, float(rate), 21600)
                return float(rate)
            
        except Exception as e:
            logger.error(f"Exchange rate request failed: {str(e)}")
            return self._get_exchange_rate_fallback(from_currency, to_currency)
        return None
    
    
    def _get_exchange_rate_fallback(self, from_currency, to_currency):
        """Fallback method using alternative API"""
        try:
            url = self.ALT_BASE_URL
            params = {
                'base': from_currency,
                'symbols': to_currency
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rate = data['rates'].get(to_currency)
            
            if rate:
                return float(rate)
                
        except Exception as e:
            logger.error(f"Fallback exchange rate request failed: {str(e)}")
        return 1.0 
    
    
    def convert_amount(self, amount, from_currency, to_currency):
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Decimal: Converted amount
        """
        if from_currency == to_currency:
            return Decimal(str(amount))
        
        rate = self.get_exchange_rate(from_currency, to_currency)
        
        if rate:
            converted = Decimal(str(amount)) * Decimal(str(rate))
            return converted.quantize(Decimal('0.01'))
        
        return Decimal(str(amount))
    
    
    def get_multiple_rates(self, base_currency, target_currencies):
        """
        Get exchange rates for multiple currencies at once
        
        Args:
            base_currency: Base currency code
            target_currencies: List of target currency codes
            
        Returns:
            dict: Dictionary of currency codes to rates
        """
        cache_key = f"multi_rates_{base_currency}_{'_'.join(sorted(target_currencies))}"
        cached_rates = cache.get(cache_key)
        
        if cached_rates:
            return cached_rates
        
        try:
            url = f"{self.BASE_URL}/{base_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rates = {}
            
            for currency in target_currencies:
                if currency in data['rates']:
                    rates[currency] = float(data['rates'][currency])
            
            if rates:
                cache.set(cache_key, rates, 21600)
                return rates
                
        except Exception as e:
            logger.error(f"Multiple exchange rates request failed: {str(e)}")
            
        return {currency: 1.0 for currency in target_currencies}
    
    
    def get_supported_currencies(self):
        """
        Get list of supported currency codes
        
        Returns:
            list: List of currency codes
        """
        cache_key = "supported_currencies"
        cached_currencies = cache.get(cache_key)
        
        if cached_currencies:
            return cached_currencies
        
        try:
            url = f"{self.BASE_URL}/USD"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            currencies = list(data['rates'].keys())
            cache.set(cache_key, currencies, 86400)
            return currencies
            
        except Exception as e:
            logger.error(f"Supported currencies request failed: {str(e)}")
        
        return ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'INR']
    
    
CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'AUD': 'A$',
    'CAD': 'C$',
    'CHF': 'CHF',
    'CNY': '¥',
    'INR': '₹',
    'KRW': '₩',
    'MXN': 'MX$',
    'BRL': 'R$',
    'ZAR': 'R',
    'SGD': 'S$',
    'HKD': 'HK$',
    'NOK': 'kr',
    'SEK': 'kr',
    'DKK': 'kr',
    'NZD': 'NZ$',
}


def get_currency_symbol(currency_code):
    """Get symbol for a currency code"""
    return CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)


def format_currency(amount, currency_code):
    """
    Format amount with currency symbol
    
    Args:
        amount: Numeric amount
        currency_code: Currency code
        
    Returns:
        str: Formatted currency string
    """
    symbol = get_currency_symbol(currency_code)
    
    if isinstance(amount, (int, float, Decimal)):
        formatted_amount = f"{float(amount):,.2f}"
    else:
        formatted_amount = str(amount)
    
    if currency_code.upper() in ['EUR', 'SEK', 'NOK', 'DKK']:
        return f"{formatted_amount} {symbol}"
    
    return f"{symbol}{formatted_amount}"


# Convenience functions
def convert_currency(amount, from_currency, to_currency):
    """Convert currency amount"""
    client = CurrencyAPIClient()
    return client.convert_amount(amount, from_currency, to_currency)


def get_exchange_rate(from_currency, to_currency):
    """Get exchange rate between currencies"""
    client = CurrencyAPIClient()
    return client.get_exchange_rate(from_currency, to_currency)


# Cost estimation helpers
def estimate_daily_budget(total_budget, duration, currency='USD'):
    """
    Estimate daily budget breakdown
    
    Args:
        total_budget: Total trip budget
        duration: Number of days
        currency: Currency code
        
    Returns:
        dict: Daily budget breakdown
    """
    daily_total = Decimal(str(total_budget)) / Decimal(str(duration))
    
    allocation = {
        'accommodation': daily_total * Decimal('0.35'),
        'food': daily_total * Decimal('0.30'),
        'activities': daily_total * Decimal('0.25'),
        'transport': daily_total * Decimal('0.10'),
    }
    
    return {
        'total_per_day': daily_total.quantize(Decimal('0.01')),
        'breakdown': {
            key: value.quantize(Decimal('0.01'))
            for key, value in allocation.items()
        },
        'currency': currency
    }


def adjust_budget_for_destination(budget, currency, destination_country_code):
    """
    Adjust budget based on destination cost of living
    
    Args:
        budget: Budget amount
        currency: Currency code
        destination_country_code: ISO country code
        
    Returns:
        dict: Adjusted budget info
    """
    # Cost of living multipliers (relative to US = 1.0)
    cost_multipliers = {
        'CH': 1.5,   # Switzerland
        'NO': 1.4,   # Norway
        'IS': 1.3,   # Iceland
        'JP': 1.2,   # Japan
        'GB': 1.15,  # UK
        'AU': 1.1,   # Australia
        'US': 1.0,   # USA
        'FR': 0.95,  # France
        'IT': 0.9,   # Italy
        'ES': 0.85,  # Spain
        'GR': 0.75,  # Greece
        'TH': 0.5,   # Thailand
        'IN': 0.3,   # India
        'VN': 0.4,   # Vietnam
    }
    
    multiplier = cost_multipliers.get(destination_country_code, 1.0)
    adjusted_budget = Decimal(str(budget)) * Decimal(str(multiplier))
    
    return {
        'original_budget': Decimal(str(budget)),
        'adjusted_budget': adjusted_budget.quantize(Decimal('0.01')),
        'multiplier': multiplier,
        'currency': currency,
        'note': f"Budget adjusted for {destination_country_code} cost of living"
    }