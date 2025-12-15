"""
Flight Price Scraper & API Tool
Fetches flight prices from various sources when database is empty.
"""
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime, timedelta
import json
import re


# Common Tanzania domestic flight routes with typical price ranges (USD)
TANZANIA_ROUTES = {
    # Northern Circuit
    ('JRO', 'ARK'): {'min': 80, 'max': 150, 'duration': '30m', 'airlines': ['Coastal', 'Auric']},
    ('ARK', 'JRO'): {'min': 80, 'max': 150, 'duration': '30m', 'airlines': ['Coastal', 'Auric']},
    
    # Serengeti Routes
    ('ARK', 'SEU'): {'min': 280, 'max': 400, 'duration': '1h 15m', 'airlines': ['Coastal', 'Auric']},
    ('SEU', 'ARK'): {'min': 280, 'max': 400, 'duration': '1h 15m', 'airlines': ['Coastal', 'Auric']},
    ('JRO', 'SEU'): {'min': 320, 'max': 450, 'duration': '1h 30m', 'airlines': ['Coastal']},
    ('SEU', 'JRO'): {'min': 320, 'max': 450, 'duration': '1h 30m', 'airlines': ['Coastal']},
    
    # Zanzibar Routes
    ('DAR', 'ZNZ'): {'min': 80, 'max': 150, 'duration': '20m', 'airlines': ['Precision', 'Coastal', 'Air Tanzania']},
    ('ZNZ', 'DAR'): {'min': 80, 'max': 150, 'duration': '20m', 'airlines': ['Precision', 'Coastal', 'Air Tanzania']},
    ('ARK', 'ZNZ'): {'min': 200, 'max': 320, 'duration': '1h 30m', 'airlines': ['Coastal', 'Precision']},
    ('ZNZ', 'ARK'): {'min': 200, 'max': 320, 'duration': '1h 30m', 'airlines': ['Coastal', 'Precision']},
    ('JRO', 'ZNZ'): {'min': 180, 'max': 300, 'duration': '1h 15m', 'airlines': ['Precision', 'Coastal']},
    ('ZNZ', 'JRO'): {'min': 180, 'max': 300, 'duration': '1h 15m', 'airlines': ['Precision', 'Coastal']},
    ('SEU', 'ZNZ'): {'min': 400, 'max': 550, 'duration': '2h', 'airlines': ['Coastal']},
    ('ZNZ', 'SEU'): {'min': 400, 'max': 550, 'duration': '2h', 'airlines': ['Coastal']},
    
    # Dar es Salaam Routes
    ('DAR', 'JRO'): {'min': 150, 'max': 250, 'duration': '1h 15m', 'airlines': ['Precision', 'Air Tanzania', 'Fastjet']},
    ('JRO', 'DAR'): {'min': 150, 'max': 250, 'duration': '1h 15m', 'airlines': ['Precision', 'Air Tanzania', 'Fastjet']},
    ('DAR', 'ARK'): {'min': 180, 'max': 280, 'duration': '1h 30m', 'airlines': ['Precision', 'Air Tanzania']},
    ('ARK', 'DAR'): {'min': 180, 'max': 280, 'duration': '1h 30m', 'airlines': ['Precision', 'Air Tanzania']},
    ('DAR', 'SEU'): {'min': 350, 'max': 500, 'duration': '2h', 'airlines': ['Coastal']},
    ('SEU', 'DAR'): {'min': 350, 'max': 500, 'duration': '2h', 'airlines': ['Coastal']},
    
    # Ruaha & Southern
    ('DAR', 'IRG'): {'min': 200, 'max': 350, 'duration': '1h 30m', 'airlines': ['Coastal', 'Safari Airlink']},
    ('IRG', 'DAR'): {'min': 200, 'max': 350, 'duration': '1h 30m', 'airlines': ['Coastal', 'Safari Airlink']},
    ('DAR', 'JRO'): {'min': 150, 'max': 250, 'duration': '1h 15m', 'airlines': ['Air Tanzania', 'Precision']},
    
    # Lake Manyara
    ('ARK', 'LKY'): {'min': 150, 'max': 250, 'duration': '45m', 'airlines': ['Coastal', 'Auric']},
    ('LKY', 'ARK'): {'min': 150, 'max': 250, 'duration': '45m', 'airlines': ['Coastal', 'Auric']},
    
    # Selous/Nyerere
    ('DAR', 'SGX'): {'min': 180, 'max': 280, 'duration': '45m', 'airlines': ['Coastal', 'Safari Airlink']},
    ('SGX', 'DAR'): {'min': 180, 'max': 280, 'duration': '45m', 'airlines': ['Coastal', 'Safari Airlink']},
}

# Airport code to full name mapping
AIRPORT_NAMES = {
    'JRO': 'Kilimanjaro International Airport',
    'ARK': 'Arusha Airport',
    'DAR': 'Julius Nyerere International Airport',
    'ZNZ': 'Abeid Amani Karume International Airport (Zanzibar)',
    'SEU': 'Seronera Airstrip (Serengeti)',
    'LKY': 'Lake Manyara Airport',
    'IRG': 'Iringa Airport (Ruaha)',
    'SGX': 'Songea Airport (Selous/Nyerere)',
    'MWZ': 'Mwanza Airport',
    'DOD': 'Dodoma Airport',
}


class FlightPriceFetcher:
    """Fetch flight prices from various sources."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def scrape_air_tanzania(self, origin, destination, date=None):
        """
        Scrape Air Tanzania website for flight prices.
        Website: https://www.airtanzania.co.tz
        """
        print(f"   🔍 Attempting to scrape Air Tanzania: {origin} → {destination}")
        
        try:
            # Air Tanzania main site - they use Videcom booking system
            url = "https://www.airtanzania.co.tz"
            
            # First, get the booking page to understand the form structure
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for price information in the page
                # Note: Air Tanzania uses a dynamic booking engine (Videcom)
                # Actual prices require form submission with JavaScript
                
                # Try to find any static price mentions
                price_elements = soup.find_all(text=re.compile(r'\$\d+|\d+\s*USD', re.IGNORECASE))
                
                if price_elements:
                    print(f"   ✓ Found price references on Air Tanzania site")
                    # Parse prices if found
                    for elem in price_elements[:3]:
                        print(f"      • {elem.strip()[:50]}")
                
                # Air Tanzania uses Videcom booking system which requires JS
                print(f"   ⚠️ Air Tanzania uses dynamic booking - falling back to API")
                return None
            else:
                print(f"   ⚠️ Air Tanzania returned status {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Air Tanzania request timed out")
            return None
        except Exception as e:
            print(f"   ⚠️ Air Tanzania scraping error: {e}")
            return None
    
    def scrape_precision_air(self, origin, destination, date=None):
        """
        Scrape Precision Air website for flight prices.
        Website: https://www.precisionairtz.com
        """
        print(f"   🔍 Attempting to scrape Precision Air: {origin} → {destination}")
        
        try:
            # Precision Air uses a third-party booking engine
            url = "https://www.precisionairtz.com/book-a-flight/"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for route/price info
                # Precision Air redirects to external booking
                print(f"   ⚠️ Precision Air uses external booking system")
                return None
            
        except Exception as e:
            print(f"   ⚠️ Precision Air scraping error: {e}")
            return None
        
        return None
    
    def scrape_coastal_aviation(self, origin, destination, date=None):
        """
        Scrape Coastal Aviation website for charter/scheduled flight prices.
        Website: https://www.coastal.co.tz
        """
        print(f"   🔍 Attempting to scrape Coastal Aviation: {origin} → {destination}")
        
        try:
            # Coastal Aviation - popular for safari circuits
            # Their main domain is coastalaviation.co.tz
            url = "https://www.coastalaviation.co.tz/scheduled-flights/"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for schedule/pricing tables
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        text = ' '.join([c.get_text(strip=True) for c in cells])
                        
                        # Check if this row contains our route
                        if origin.upper() in text.upper() or destination.upper() in text.upper():
                            # Look for price pattern
                            price_match = re.search(r'\$\s*(\d+)', text)
                            if price_match:
                                price = int(price_match.group(1))
                                print(f"   ✓ Found Coastal price: ${price}")
                                return {
                                    'origin': origin,
                                    'destination': destination,
                                    'price_economy': price,
                                    'airline': 'Coastal Aviation',
                                    'source': 'scraped'
                                }
                
                print(f"   ⚠️ Route not found in Coastal schedule")
                return None
                
        except Exception as e:
            print(f"   ⚠️ Coastal Aviation scraping error: {e}")
            return None
        
        return None
    
    def get_amadeus_prices(self, origin, destination, date=None):
        """
        Use Amadeus API for flight prices (requires API key).
        Sign up at: https://developers.amadeus.com
        """
        from django.conf import settings
        
        api_key = getattr(settings, 'AMADEUS_API_KEY', None)
        api_secret = getattr(settings, 'AMADEUS_API_SECRET', None)
        
        if not api_key or not api_secret:
            return None
        
        print(f"   🔍 Checking Amadeus API: {origin} → {destination}")
        
        try:
            # Get access token
            auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            auth_response = self.session.post(auth_url, data={
                'grant_type': 'client_credentials',
                'client_id': api_key,
                'client_secret': api_secret
            })
            
            if auth_response.status_code != 200:
                print(f"   ⚠️ Amadeus auth failed")
                return None
            
            token = auth_response.json().get('access_token')
            
            # Search flights
            search_date = date or (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            search_url = f"https://test.api.amadeus.com/v2/shopping/flight-offers"
            
            headers = {'Authorization': f'Bearer {token}'}
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': search_date,
                'adults': 1,
                'max': 3
            }
            
            response = self.session.get(search_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('data', [])
                
                if offers:
                    # Get cheapest offer
                    cheapest = min(offers, key=lambda x: float(x['price']['total']))
                    price = float(cheapest['price']['total'])
                    
                    print(f"   ✓ Amadeus found: ${price}")
                    return {
                        'origin': origin,
                        'destination': destination,
                        'price_economy': price,
                        'airline': 'Various',
                        'source': 'amadeus_api'
                    }
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Amadeus API error: {e}")
            return None
    
    def get_air_tanzania_prices(self, origin, destination, date=None):
        """
        Try multiple sources to fetch Air Tanzania/Tanzania flight prices.
        Priority: 1) Live scraping, 2) APIs, 3) Typical rates
        """
        # Try scraping airlines directly
        result = self.scrape_coastal_aviation(origin, destination, date)
        if result:
            return result
        
        result = self.scrape_air_tanzania(origin, destination, date)
        if result:
            return result
        
        # Try Amadeus API if configured
        result = self.get_amadeus_prices(origin, destination, date)
        if result:
            return result
        
        # Fallback to typical prices
        print(f"   📊 Using typical market rates for {origin} → {destination}")
        return self.get_typical_prices(origin, destination)
    
    def get_typical_prices(self, origin, destination):
        """Get typical flight prices for a route based on industry data."""
        route = (origin.upper(), destination.upper())
        
        if route in TANZANIA_ROUTES:
            data = TANZANIA_ROUTES[route]
            # Return average price
            avg_price = (data['min'] + data['max']) / 2
            return {
                'origin': origin,
                'origin_name': AIRPORT_NAMES.get(origin, origin),
                'destination': destination,
                'destination_name': AIRPORT_NAMES.get(destination, destination),
                'price_min': data['min'],
                'price_max': data['max'],
                'price_avg': avg_price,
                'duration': data['duration'],
                'airlines': data['airlines'],
                'source': 'typical_rates'
            }
        
        return None
    
    def get_all_routes(self):
        """Get all available flight routes with pricing."""
        routes = []
        for (origin, dest), data in TANZANIA_ROUTES.items():
            routes.append({
                'origin': origin,
                'origin_name': AIRPORT_NAMES.get(origin, origin),
                'destination': dest,
                'destination_name': AIRPORT_NAMES.get(dest, dest),
                'price_min': data['min'],
                'price_max': data['max'],
                'price_avg': (data['min'] + data['max']) / 2,
                'duration': data['duration'],
                'airlines': data['airlines'],
            })
        return routes
    
    def search_flights(self, origin, destination, date=None):
        """
        Search for flights between two airports.
        First tries live APIs, then falls back to typical rates.
        """
        print(f"   🔍 Searching flights: {origin} → {destination}")
        
        # Try Air Tanzania
        result = self.get_air_tanzania_prices(origin, destination, date)
        if result:
            return result
        
        # Try typical prices
        result = self.get_typical_prices(origin, destination)
        if result:
            return result
        
        # No route found
        print(f"   ⚠️ No flight data found for {origin} → {destination}")
        return None


def get_flights_for_itinerary(pickup_location, destinations, departure_location):
    """
    Get relevant flight options for an itinerary.
    
    Args:
        pickup_location: Where guest starts (e.g., "JRO - Kilimanjaro")
        destinations: List of destinations to visit
        departure_location: Where guest ends (e.g., "ZNZ - Zanzibar")
    
    Returns:
        List of relevant flight options with pricing
    """
    fetcher = FlightPriceFetcher()
    
    # Extract airport codes from location strings
    def extract_code(location):
        if not location:
            return None
        # Look for 3-letter airport code
        match = re.search(r'\b([A-Z]{3})\b', location.upper())
        if match:
            return match.group(1)
        # Check if location name contains airport name
        location_upper = location.upper()
        if 'KILIMANJARO' in location_upper or 'JRO' in location_upper:
            return 'JRO'
        if 'ZANZIBAR' in location_upper or 'ZNZ' in location_upper:
            return 'ZNZ'
        if 'DAR' in location_upper or 'SALAAM' in location_upper:
            return 'DAR'
        if 'ARUSHA' in location_upper or 'ARK' in location_upper:
            return 'ARK'
        if 'SERENGETI' in location_upper or 'SEU' in location_upper:
            return 'SEU'
        return None
    
    pickup_code = extract_code(pickup_location)
    departure_code = extract_code(departure_location)
    
    flights = []
    
    # Get flights from pickup to destinations
    if pickup_code:
        for dest in destinations:
            dest_code = extract_code(dest) if isinstance(dest, str) else None
            if dest_code and pickup_code != dest_code:
                flight = fetcher.search_flights(pickup_code, dest_code)
                if flight:
                    flights.append(flight)
    
    # Get flights between destinations
    # (Would need to analyze itinerary order)
    
    # Get flights to departure
    if departure_code and pickup_code != departure_code:
        # Common ending flights
        for origin in ['SEU', 'ARK', 'DAR']:
            if origin != departure_code:
                flight = fetcher.search_flights(origin, departure_code)
                if flight:
                    flights.append(flight)
    
    return flights


def populate_flight_rates_from_scraper():
    """
    Populate FlightRate model with data from scraper/typical rates.
    Call this from Django shell or management command.
    """
    from tour.models import FlightRate
    
    fetcher = FlightPriceFetcher()
    routes = fetcher.get_all_routes()
    
    created_count = 0
    updated_count = 0
    
    # Airline name to code mapping
    airline_codes = {
        'Coastal': 'coastal',
        'Auric': 'auric',
        'Precision': 'precision',
        'Air Tanzania': 'air_tanzania',
        'Fastjet': 'fastjet',
        'FlightLink': 'flightlink',
        'Safari Airlink': 'other',
    }
    
    for route in routes:
        for airline_name in route['airlines']:
            airline_code = airline_codes.get(airline_name, 'other')
            
            # Check if route exists
            existing = FlightRate.objects.filter(
                origin_code=route['origin'],
                destination_code=route['destination'],
                airline=airline_code
            ).first()
            
            if existing:
                # Update price
                existing.price_economy = Decimal(str(route['price_avg']))
                existing.save()
                updated_count += 1
            else:
                # Create new
                FlightRate.objects.create(
                    airline=airline_code,
                    origin=route['origin_name'],
                    origin_code=route['origin'],
                    destination=route['destination_name'],
                    destination_code=route['destination'],
                    price_economy=Decimal(str(route['price_avg'])),
                    flight_duration=route['duration'],
                    frequency='Daily',
                    is_active=True
                )
                created_count += 1
    
    print(f"✅ Flight rates populated: {created_count} created, {updated_count} updated")
    return created_count, updated_count
