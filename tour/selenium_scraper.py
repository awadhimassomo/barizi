"""
Selenium-based Flight Price Scraper
Uses browser automation to get real-time prices from airline booking systems.
"""
import time
import re
from datetime import datetime, timedelta
from decimal import Decimal


class SeleniumFlightScraper:
    """Browser automation scraper for airline websites."""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        
    def _init_driver(self):
        """Initialize WebDriver (tries Edge first on Windows, then Chrome)."""
        if self.driver:
            return self.driver
        
        from selenium import webdriver
        
        # Try Microsoft Edge first (comes with Windows)
        try:
            from selenium.webdriver.edge.service import Service as EdgeService
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            
            options = EdgeOptions()
            if self.headless:
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=options)
            self.driver.implicitly_wait(10)
            print("   ✓ Edge browser initialized")
            return self.driver
        except Exception as e:
            print(f"   ⚠️ Edge failed: {e}")
        
        # Try Chrome as fallback
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = ChromeOptions()
            if self.headless:
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            print("   ✓ Chrome browser initialized")
            return self.driver
        except Exception as e:
            print(f"   ⚠️ Chrome failed: {e}")
        
        print("   ❌ No browser available. Install Chrome or Edge.")
        return None
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def scrape_air_tanzania(self, origin, destination, date=None):
        """
        Scrape Air Tanzania booking system for flight prices.
        
        Args:
            origin: Origin airport code (e.g., 'DAR', 'JRO')
            destination: Destination airport code (e.g., 'ZNZ')
            date: Travel date (defaults to 30 days from now)
        
        Returns:
            dict with flight price info or None
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        
        print(f"\n   🌐 Opening Air Tanzania booking page...")
        
        driver = self._init_driver()
        if not driver:
            return None
        
        # Airport code mapping for Air Tanzania
        airport_mapping = {
            'DAR': 'Dar Es Salaam',
            'JRO': 'Kilimanjaro',
            'ZNZ': 'Zanzibar',
            'ARK': 'Arusha',
            'MWZ': 'Mwanza',
            'DOD': 'Dodoma',
            'KIH': 'Kigoma',
            'BKZ': 'Bukoba',
            'TKQ': 'Kigoma',
        }
        
        origin_name = airport_mapping.get(origin.upper(), origin)
        dest_name = airport_mapping.get(destination.upper(), destination)
        
        if not date:
            date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            # Air Tanzania uses Videcom booking system
            # Their booking URL
            booking_url = "https://book.airtanzania.co.tz"
            
            driver.get(booking_url)
            print(f"   ✓ Page loaded: {driver.title[:50]}...")
            
            # Wait for the page to load
            time.sleep(3)
            
            # Look for booking form elements
            # The exact selectors depend on their current website structure
            
            # Try to find and fill origin
            try:
                # Look for origin input
                origin_inputs = driver.find_elements(By.CSS_SELECTOR, 
                    "input[name*='origin'], input[id*='origin'], input[placeholder*='From'], #departure")
                
                if origin_inputs:
                    origin_input = origin_inputs[0]
                    origin_input.clear()
                    origin_input.send_keys(origin_name)
                    print(f"   ✓ Entered origin: {origin_name}")
                    time.sleep(1)
                    
                    # Click first suggestion if dropdown appears
                    suggestions = driver.find_elements(By.CSS_SELECTOR, 
                        ".autocomplete-suggestion, .dropdown-item, .ui-menu-item")
                    if suggestions:
                        suggestions[0].click()
                        print(f"   ✓ Selected origin from dropdown")
                
                # Look for destination input
                dest_inputs = driver.find_elements(By.CSS_SELECTOR,
                    "input[name*='dest'], input[id*='dest'], input[placeholder*='To'], #arrival")
                
                if dest_inputs:
                    dest_input = dest_inputs[0]
                    dest_input.clear()
                    dest_input.send_keys(dest_name)
                    print(f"   ✓ Entered destination: {dest_name}")
                    time.sleep(1)
                    
                    suggestions = driver.find_elements(By.CSS_SELECTOR,
                        ".autocomplete-suggestion, .dropdown-item, .ui-menu-item")
                    if suggestions:
                        suggestions[0].click()
                        print(f"   ✓ Selected destination from dropdown")
                
                # Look for date input
                date_inputs = driver.find_elements(By.CSS_SELECTOR,
                    "input[type='date'], input[name*='date'], input[id*='date'], .datepicker")
                
                if date_inputs:
                    date_input = date_inputs[0]
                    driver.execute_script(f"arguments[0].value = '{date}'", date_input)
                    print(f"   ✓ Set date: {date}")
                
                # Look for search button
                search_buttons = driver.find_elements(By.CSS_SELECTOR,
                    "button[type='submit'], input[type='submit'], .search-btn, #searchButton")
                
                if search_buttons:
                    search_buttons[0].click()
                    print(f"   ✓ Clicked search button")
                    
                    # Wait for results
                    time.sleep(5)
                
            except Exception as e:
                print(f"   ⚠️ Form interaction error: {e}")
            
            # Now look for prices in the page
            page_source = driver.page_source
            
            # Find all price patterns
            price_patterns = [
                r'USD\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*USD',
                r'TZS\s*(\d+(?:,\d{3})*)',
            ]
            
            prices_found = []
            for pattern in price_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match.replace(',', ''))
                        # Filter reasonable flight prices (between $50 and $2000)
                        if 50 <= price <= 2000:
                            prices_found.append(price)
                    except:
                        pass
            
            # Also look for price elements directly
            price_elements = driver.find_elements(By.CSS_SELECTOR,
                ".price, .fare, .amount, [class*='price'], [class*='fare']")
            
            for elem in price_elements:
                text = elem.text
                matches = re.findall(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
                for match in matches:
                    try:
                        price = float(match.replace(',', ''))
                        if 50 <= price <= 2000:
                            prices_found.append(price)
                    except:
                        pass
            
            if prices_found:
                # Remove duplicates and sort
                prices_found = sorted(set(prices_found))
                
                print(f"\n   💰 Prices found on Air Tanzania:")
                for p in prices_found[:5]:
                    print(f"      • ${p:.2f}")
                
                min_price = min(prices_found)
                max_price = max(prices_found)
                avg_price = sum(prices_found) / len(prices_found)
                
                return {
                    'origin': origin,
                    'destination': destination,
                    'airline': 'Air Tanzania',
                    'price_min': min_price,
                    'price_max': max_price,
                    'price_economy': min_price,  # Use lowest as economy
                    'price_avg': avg_price,
                    'prices_found': prices_found[:10],
                    'source': 'selenium_scrape',
                    'scraped_at': datetime.now().isoformat(),
                }
            else:
                print(f"   ⚠️ No prices found on page")
                
                # Take a screenshot for debugging
                try:
                    screenshot_path = f"debug_airtanzania_{origin}_{destination}.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"   📸 Screenshot saved: {screenshot_path}")
                except:
                    pass
                
                return None
                
        except Exception as e:
            print(f"   ⚠️ Air Tanzania scraping error: {e}")
            return None
        finally:
            # Don't close driver here - reuse for multiple searches
            pass
    
    def scrape_precision_air(self, origin, destination, date=None):
        """
        Scrape Precision Air website for flight prices.
        """
        from selenium.webdriver.common.by import By
        
        print(f"\n   🌐 Opening Precision Air booking page...")
        
        driver = self._init_driver()
        if not driver:
            return None
        
        try:
            # Precision Air booking page
            driver.get("https://www.precisionairtz.com")
            print(f"   ✓ Page loaded: {driver.title[:50]}...")
            
            time.sleep(3)
            
            # Look for prices in the page
            page_source = driver.page_source
            
            # Find price patterns
            prices_found = []
            patterns = [
                r'USD\s*(\d+)',
                r'\$(\d+)',
                r'(\d+)\s*USD',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match)
                        if 50 <= price <= 1000:
                            prices_found.append(price)
                    except:
                        pass
            
            if prices_found:
                prices_found = sorted(set(prices_found))
                print(f"\n   💰 Prices found on Precision Air:")
                for p in prices_found[:5]:
                    print(f"      • ${p:.2f}")
                
                return {
                    'origin': origin,
                    'destination': destination,
                    'airline': 'Precision Air',
                    'price_min': min(prices_found),
                    'price_max': max(prices_found),
                    'price_economy': min(prices_found),
                    'source': 'selenium_scrape',
                }
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Precision Air scraping error: {e}")
            return None
    
    def scrape_all_airlines(self, origin, destination, date=None):
        """
        Try all available airline scrapers and return best result.
        """
        results = []
        
        # Try Air Tanzania
        result = self.scrape_air_tanzania(origin, destination, date)
        if result:
            results.append(result)
        
        # Try Precision Air
        result = self.scrape_precision_air(origin, destination, date)
        if result:
            results.append(result)
        
        # Close browser
        self.close()
        
        if results:
            # Return cheapest option
            cheapest = min(results, key=lambda x: x.get('price_economy', float('inf')))
            return cheapest
        
        return None


def scrape_flight_prices(origin, destination, date=None, headless=True):
    """
    Convenience function to scrape flight prices.
    
    Usage:
        from tour.selenium_scraper import scrape_flight_prices
        result = scrape_flight_prices('DAR', 'ZNZ')
        print(f"Price: ${result['price_economy']}")
    """
    scraper = SeleniumFlightScraper(headless=headless)
    try:
        return scraper.scrape_all_airlines(origin, destination, date)
    finally:
        scraper.close()


def update_database_with_scraped_prices(routes=None):
    """
    Scrape prices for routes and update the database.
    
    Args:
        routes: List of (origin, dest) tuples. If None, uses common routes.
    """
    from tour.models import FlightRate
    from tour.flight_scraper import TANZANIA_ROUTES, AIRPORT_NAMES
    
    if routes is None:
        # Use common routes
        routes = [
            ('DAR', 'ZNZ'),
            ('JRO', 'ZNZ'),
            ('DAR', 'JRO'),
            ('ARK', 'ZNZ'),
        ]
    
    scraper = SeleniumFlightScraper(headless=True)
    updated = 0
    
    try:
        for origin, dest in routes:
            print(f"\n{'='*50}")
            print(f"Scraping: {origin} → {dest}")
            print('='*50)
            
            result = scraper.scrape_air_tanzania(origin, dest)
            
            if result and result.get('price_economy'):
                price = Decimal(str(result['price_economy']))
                
                # Update or create FlightRate
                flight, created = FlightRate.objects.update_or_create(
                    origin_code=origin,
                    destination_code=dest,
                    airline='air_tanzania',
                    defaults={
                        'origin': AIRPORT_NAMES.get(origin, origin),
                        'destination': AIRPORT_NAMES.get(dest, dest),
                        'price_economy': price,
                        'is_active': True,
                    }
                )
                
                action = "Created" if created else "Updated"
                print(f"\n   ✅ {action}: {flight}")
                updated += 1
            else:
                print(f"\n   ❌ No price found for {origin} → {dest}")
            
            # Small delay between requests
            time.sleep(2)
    
    finally:
        scraper.close()
    
    print(f"\n{'='*50}")
    print(f"✅ Updated {updated} flight routes")
    print('='*50)
    
    return updated
