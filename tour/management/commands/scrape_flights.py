"""
Management command to scrape live flight prices.
Usage: python manage.py scrape_flights [--route JRO ZNZ] [--update-db]
"""
from django.core.management.base import BaseCommand
from tour.flight_scraper import FlightPriceFetcher, TANZANIA_ROUTES, AIRPORT_NAMES
from decimal import Decimal


class Command(BaseCommand):
    help = 'Scrape live flight prices from airline websites'

    def add_arguments(self, parser):
        parser.add_argument('--route', nargs=2, metavar=('ORIGIN', 'DEST'), 
                          help='Specific route to check, e.g., --route JRO ZNZ')
        parser.add_argument('--update-db', action='store_true', 
                          help='Update database with scraped prices')
        parser.add_argument('--all', action='store_true',
                          help='Check all known routes')

    def handle(self, *args, **options):
        fetcher = FlightPriceFetcher()
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✈️  TANZANIA FLIGHT PRICE SCRAPER"))
        self.stdout.write("=" * 60 + "\n")
        
        if options['route']:
            origin, dest = options['route']
            self.check_route(fetcher, origin.upper(), dest.upper(), options['update_db'])
        elif options['all']:
            self.check_all_routes(fetcher, options['update_db'])
        else:
            # Show sample routes
            self.stdout.write("Available routes:\n")
            unique_routes = set()
            for (o, d) in TANZANIA_ROUTES.keys():
                route_str = f"  {o} → {d}"
                if route_str not in unique_routes:
                    unique_routes.add(route_str)
                    origin_name = AIRPORT_NAMES.get(o, o)
                    dest_name = AIRPORT_NAMES.get(d, d)
                    self.stdout.write(f"  {o} → {d}  ({origin_name[:20]} to {dest_name[:20]})")
            
            self.stdout.write("\n" + self.style.WARNING(
                "Use --route ORIGIN DEST to check a specific route\n"
                "Use --all to check all routes\n"
                "Use --update-db to save prices to database"
            ))
    
    def check_route(self, fetcher, origin, dest, update_db=False):
        """Check a single route."""
        self.stdout.write(f"\nChecking: {origin} → {dest}")
        self.stdout.write("-" * 40)
        
        result = fetcher.get_air_tanzania_prices(origin, dest)
        
        if result:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Found price data:"))
            self.stdout.write(f"   Route: {result.get('origin')} → {result.get('destination')}")
            self.stdout.write(f"   Price: ${result.get('price_avg', result.get('price_economy', 'N/A'))}")
            if result.get('price_min') and result.get('price_max'):
                self.stdout.write(f"   Range: ${result['price_min']} - ${result['price_max']}")
            self.stdout.write(f"   Source: {result.get('source', 'unknown')}")
            if result.get('airlines'):
                self.stdout.write(f"   Airlines: {', '.join(result['airlines'])}")
            
            if update_db:
                self.update_database(origin, dest, result)
        else:
            self.stdout.write(self.style.ERROR(f"\n❌ No price data found for {origin} → {dest}"))
    
    def check_all_routes(self, fetcher, update_db=False):
        """Check all known routes."""
        checked = set()
        found = 0
        not_found = 0
        
        for (origin, dest) in TANZANIA_ROUTES.keys():
            route_key = (origin, dest)
            if route_key in checked:
                continue
            checked.add(route_key)
            
            self.stdout.write(f"\n{'='*40}")
            self.stdout.write(f"Route: {origin} → {dest}")
            
            result = fetcher.get_air_tanzania_prices(origin, dest)
            
            if result:
                found += 1
                price = result.get('price_avg', result.get('price_economy', 0))
                source = result.get('source', 'unknown')
                self.stdout.write(self.style.SUCCESS(f"  ✓ ${price} ({source})"))
                
                if update_db:
                    self.update_database(origin, dest, result)
            else:
                not_found += 1
                self.stdout.write(self.style.WARNING(f"  ✗ Not found"))
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"Summary: {found} routes found, {not_found} not found")
        self.stdout.write("=" * 60)
    
    def update_database(self, origin, dest, result):
        """Update FlightRate in database."""
        from tour.models import FlightRate
        
        price = result.get('price_avg', result.get('price_economy', 0))
        airlines = result.get('airlines', ['other'])
        
        # Map airline name to code
        airline_codes = {
            'Coastal Aviation': 'coastal',
            'Coastal': 'coastal',
            'Auric Air': 'auric',
            'Auric': 'auric',
            'Precision Air': 'precision',
            'Precision': 'precision',
            'Air Tanzania': 'air_tanzania',
            'Fastjet': 'fastjet',
            'FlightLink': 'flightlink',
        }
        
        for airline_name in airlines[:1]:  # Use first airline
            airline_code = airline_codes.get(airline_name, 'other')
            
            flight, created = FlightRate.objects.update_or_create(
                origin_code=origin,
                destination_code=dest,
                airline=airline_code,
                defaults={
                    'origin': AIRPORT_NAMES.get(origin, origin),
                    'destination': AIRPORT_NAMES.get(dest, dest),
                    'price_economy': Decimal(str(price)),
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"   → Created: {flight}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"   → Updated: {flight}"))
