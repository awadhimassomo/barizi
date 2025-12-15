"""
Management command to scrape LIVE flight prices using Selenium browser automation.
Usage: python manage.py scrape_flights_live [--route DAR ZNZ] [--all] [--visible]
"""
from django.core.management.base import BaseCommand
from decimal import Decimal


class Command(BaseCommand):
    help = 'Scrape LIVE flight prices using browser automation (Selenium)'

    def add_arguments(self, parser):
        parser.add_argument('--route', nargs=2, metavar=('ORIGIN', 'DEST'),
                          help='Specific route to scrape, e.g., --route DAR ZNZ')
        parser.add_argument('--all', action='store_true',
                          help='Scrape all common routes')
        parser.add_argument('--visible', action='store_true',
                          help='Show browser window (not headless)')
        parser.add_argument('--update-db', action='store_true',
                          help='Update database with scraped prices')

    def handle(self, *args, **options):
        from tour.selenium_scraper import SeleniumFlightScraper
        from tour.flight_scraper import AIRPORT_NAMES
        
        headless = not options['visible']
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("🌐 LIVE FLIGHT PRICE SCRAPER (Selenium)"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Mode: {'Headless' if headless else 'Visible Browser'}\n")
        
        scraper = SeleniumFlightScraper(headless=headless)
        
        try:
            if options['route']:
                origin, dest = options['route']
                self.scrape_route(scraper, origin.upper(), dest.upper(), options['update_db'])
            elif options['all']:
                self.scrape_common_routes(scraper, options['update_db'])
            else:
                # Demo with one route
                self.stdout.write(self.style.WARNING(
                    "\nNo route specified. Running demo with DAR → ZNZ\n"
                    "Use --route ORIGIN DEST to specify a route\n"
                    "Use --all to scrape common routes\n"
                    "Use --visible to see the browser\n"
                ))
                self.scrape_route(scraper, 'DAR', 'ZNZ', options['update_db'])
        finally:
            scraper.close()
            self.stdout.write("\n✅ Browser closed")
    
    def scrape_route(self, scraper, origin, dest, update_db=False):
        """Scrape a single route."""
        from tour.models import FlightRate
        from tour.flight_scraper import AIRPORT_NAMES
        
        self.stdout.write(f"\n{'─' * 40}")
        self.stdout.write(f"Scraping: {origin} → {dest}")
        self.stdout.write('─' * 40)
        
        result = scraper.scrape_air_tanzania(origin, dest)
        
        if result:
            self.stdout.write(self.style.SUCCESS("\n✅ PRICES FOUND:"))
            self.stdout.write(f"   Airline: {result.get('airline')}")
            self.stdout.write(f"   Economy: ${result.get('price_economy', 'N/A')}")
            
            if result.get('price_min') and result.get('price_max'):
                self.stdout.write(f"   Range: ${result['price_min']:.0f} - ${result['price_max']:.0f}")
            
            if result.get('prices_found'):
                self.stdout.write(f"   All prices: {result['prices_found'][:5]}")
            
            self.stdout.write(f"   Source: {result.get('source')}")
            
            if update_db:
                price = Decimal(str(result['price_economy']))
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
                self.stdout.write(self.style.SUCCESS(f"\n   → {action} in database: {flight}"))
        else:
            self.stdout.write(self.style.ERROR(f"\n❌ No prices found for {origin} → {dest}"))
    
    def scrape_common_routes(self, scraper, update_db=False):
        """Scrape common Tanzania routes."""
        import time
        
        routes = [
            ('DAR', 'ZNZ'),
            ('ZNZ', 'DAR'),
            ('JRO', 'ZNZ'),
            ('ZNZ', 'JRO'),
            ('DAR', 'JRO'),
            ('JRO', 'DAR'),
            ('DAR', 'MWZ'),
            ('ARK', 'ZNZ'),
        ]
        
        found = 0
        not_found = 0
        
        for origin, dest in routes:
            self.scrape_route(scraper, origin, dest, update_db)
            
            # Check if we found prices
            # Small delay between requests to be nice to the server
            time.sleep(2)
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"Completed scraping {len(routes)} routes")
        self.stdout.write("=" * 60)
