"""
Live exchange rate fetcher for USD to NGN
Uses ExchangeRate-API (free tier)
"""
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Cache for exchange rate
_cached_rate = None
_cache_timestamp = None
_cache_duration = timedelta(hours=1)  # Cache for 1 hour

# Default fallback rate
DEFAULT_DOLLAR_RATE = float(os.getenv("DOLLAR_RATE", "1500"))

def get_live_dollar_rate() -> float:
    """
    Get live USD to NGN exchange rate
    Returns cached rate if available and not expired
    Falls back to default rate if API fails
    """
    global _cached_rate, _cache_timestamp
    
    # Check if we have a valid cached rate
    if _cached_rate and _cache_timestamp:
        if datetime.now() - _cache_timestamp < _cache_duration:
            logger.debug(f"Using cached exchange rate: {_cached_rate}")
            return _cached_rate
    
    # Try to fetch live rate
    try:
        # Using exchangerate-api.com (free, no API key needed for basic use)
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        
        logger.info("Fetching live exchange rate...")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        # Get NGN rate
        if 'rates' in data and 'NGN' in data['rates']:
            rate = float(data['rates']['NGN'])
            
            # Update cache
            _cached_rate = rate
            _cache_timestamp = datetime.now()
            
            logger.info(f"Live exchange rate fetched: 1 USD = {rate} NGN")
            return rate
        else:
            logger.warning("NGN rate not found in API response")
            return DEFAULT_DOLLAR_RATE
            
    except requests.RequestException as e:
        logger.error(f"Error fetching exchange rate: {e}")
        return DEFAULT_DOLLAR_RATE
    except Exception as e:
        logger.error(f"Unexpected error fetching exchange rate: {e}")
        return DEFAULT_DOLLAR_RATE

def clear_rate_cache():
    """Clear the cached exchange rate"""
    global _cached_rate, _cache_timestamp
    _cached_rate = None
    _cache_timestamp = None
    logger.info("Exchange rate cache cleared")

def get_cached_rate_info() -> dict:
    """Get information about the cached rate"""
    if _cached_rate and _cache_timestamp:
        age = datetime.now() - _cache_timestamp
        return {
            "rate": _cached_rate,
            "cached_at": _cache_timestamp.isoformat(),
            "age_seconds": age.total_seconds(),
            "expires_in_seconds": (_cache_duration - age).total_seconds()
        }
    return {
        "rate": None,
        "cached_at": None,
        "age_seconds": None,
        "expires_in_seconds": None
    }

