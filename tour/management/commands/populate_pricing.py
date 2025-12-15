"""
Management command to populate pricing data for tours.
Usage: python manage.py populate_pricing [--flights] [--destinations] [--hotels] [--activities] [--all]
"""
from django.core.management.base import BaseCommand
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate tour pricing data (flights, hotels, destinations, activities)'

    def add_arguments(self, parser):
        parser.add_argument('--flights', action='store_true', help='Populate flight rates')
        parser.add_argument('--destinations', action='store_true', help='Populate destinations')
        parser.add_argument('--hotels', action='store_true', help='Populate hotel rates')
        parser.add_argument('--activities', action='store_true', help='Populate activity rates')
        parser.add_argument('--transport', action='store_true', help='Populate transport rates')
        parser.add_argument('--all', action='store_true', help='Populate all pricing data')

    def handle(self, *args, **options):
        if options['all']:
            options['flights'] = True
            options['destinations'] = True
            options['hotels'] = True
            options['activities'] = True
            options['transport'] = True
        
        if options['destinations']:
            self.populate_destinations()
        
        if options['hotels']:
            self.populate_hotels()
        
        if options['flights']:
            self.populate_flights()
        
        if options['activities']:
            self.populate_activities()
        
        if options['transport']:
            self.populate_transport()
        
        if not any([options['flights'], options['destinations'], options['hotels'], 
                    options['activities'], options['transport']]):
            self.stdout.write(self.style.WARNING(
                'No option specified. Use --flights, --destinations, --hotels, --activities, --transport, or --all'
            ))

    def populate_destinations(self):
        """Populate common Tanzania safari destinations."""
        from tour.models import Destination
        
        destinations_data = [
            {
                'name': 'Serengeti National Park',
                'region': 'Northern Tanzania',
                'country': 'Tanzania',
                'description': 'World-famous for the Great Migration of over 1.5 million wildebeest and zebras.',
                'highlights': 'Great Migration, Big Five, endless plains, hot air balloon safaris',
                'best_time_to_visit': 'June-October (dry season) or January-March (calving season)',
                'avg_time_needed': 3,
            },
            {
                'name': 'Ngorongoro Crater',
                'region': 'Northern Tanzania',
                'country': 'Tanzania',
                'description': 'UNESCO World Heritage Site with the highest density of wildlife in Africa.',
                'highlights': 'Big Five in one day, crater views, Maasai villages',
                'best_time_to_visit': 'Year-round, best June-October',
                'avg_time_needed': 2,
            },
            {
                'name': 'Zanzibar',
                'region': 'Zanzibar Archipelago',
                'country': 'Tanzania',
                'description': 'Exotic island paradise with pristine beaches and rich Swahili culture.',
                'highlights': 'Stone Town, spice tours, white sand beaches, snorkeling',
                'best_time_to_visit': 'June-October and December-February',
                'avg_time_needed': 3,
            },
            {
                'name': 'Tarangire National Park',
                'region': 'Northern Tanzania',
                'country': 'Tanzania',
                'description': 'Known for large elephant herds and iconic baobab trees.',
                'highlights': 'Elephant herds, baobab trees, diverse birdlife',
                'best_time_to_visit': 'June-October (dry season)',
                'avg_time_needed': 2,
            },
            {
                'name': 'Lake Manyara National Park',
                'region': 'Northern Tanzania',
                'country': 'Tanzania',
                'description': 'Compact park famous for tree-climbing lions and flamingos.',
                'highlights': 'Tree-climbing lions, flamingos, diverse ecosystems',
                'best_time_to_visit': 'July-October',
                'avg_time_needed': 1,
            },
            {
                'name': 'Arusha',
                'region': 'Northern Tanzania',
                'country': 'Tanzania',
                'description': 'Safari gateway city at the foot of Mount Meru.',
                'highlights': 'Arusha National Park, cultural tours, Mount Meru',
                'best_time_to_visit': 'Year-round',
                'avg_time_needed': 1,
            },
            {
                'name': 'Selous Game Reserve',
                'region': 'Southern Tanzania',
                'country': 'Tanzania',
                'description': "Africa's largest game reserve, offering exclusive wilderness experience.",
                'highlights': 'Boat safaris, walking safaris, wild dogs',
                'best_time_to_visit': 'June-October',
                'avg_time_needed': 3,
            },
            {
                'name': 'Ruaha National Park',
                'region': 'Southern Tanzania',
                'country': 'Tanzania',
                'description': "Tanzania's largest national park with excellent off-the-beaten-path safaris.",
                'highlights': 'Large predator populations, baobab forests, Great Ruaha River',
                'best_time_to_visit': 'May-December',
                'avg_time_needed': 3,
            },
        ]
        
        created = 0
        for dest_data in destinations_data:
            dest, was_created = Destination.objects.get_or_create(
                name=dest_data['name'],
                defaults=dest_data
            )
            if was_created:
                created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ Destinations: {created} created'))

    def populate_hotels(self):
        """Populate hotel rates for each destination."""
        from tour.models import Destination, HotelRate
        
        # Hotel data by destination
        hotels_data = {
            'Serengeti National Park': [
                {'name': 'Serengeti Serena Safari Lodge', 'tier': 'luxury', 'rate_low': 650, 'rate_high': 850},
                {'name': 'Four Seasons Safari Lodge Serengeti', 'tier': 'luxury', 'rate_low': 1500, 'rate_high': 2000},
                {'name': 'Serengeti Sopa Lodge', 'tier': 'semi_luxury', 'rate_low': 350, 'rate_high': 450},
                {'name': 'Kati Kati Tented Camp', 'tier': 'mid_range', 'rate_low': 250, 'rate_high': 350},
                {'name': 'Serengeti Heritage Tented Camp', 'tier': 'mid_range', 'rate_low': 200, 'rate_high': 280},
                {'name': 'Seronera Campsite', 'tier': 'budget', 'rate_low': 50, 'rate_high': 80},
            ],
            'Ngorongoro Crater': [
                {'name': 'Ngorongoro Crater Lodge', 'tier': 'luxury', 'rate_low': 1200, 'rate_high': 1600},
                {'name': 'Ngorongoro Serena Safari Lodge', 'tier': 'luxury', 'rate_low': 500, 'rate_high': 700},
                {'name': 'Ngorongoro Sopa Lodge', 'tier': 'semi_luxury', 'rate_low': 300, 'rate_high': 400},
                {'name': 'Ngorongoro Farm House', 'tier': 'mid_range', 'rate_low': 180, 'rate_high': 250},
                {'name': 'Simba Campsite', 'tier': 'budget', 'rate_low': 60, 'rate_high': 90},
            ],
            'Zanzibar': [
                {'name': 'The Residence Zanzibar', 'tier': 'luxury', 'rate_low': 600, 'rate_high': 900},
                {'name': 'Baraza Resort & Spa', 'tier': 'luxury', 'rate_low': 500, 'rate_high': 750},
                {'name': 'Diamonds La Gemma Dell\'Est', 'tier': 'semi_luxury', 'rate_low': 250, 'rate_high': 380},
                {'name': 'DoubleTree by Hilton Zanzibar', 'tier': 'semi_luxury', 'rate_low': 180, 'rate_high': 280},
                {'name': 'Zanzibar Beach Resort', 'tier': 'mid_range', 'rate_low': 120, 'rate_high': 180},
                {'name': 'Flame Tree Cottages', 'tier': 'mid_range', 'rate_low': 80, 'rate_high': 120},
                {'name': 'Lost & Found Hostel', 'tier': 'budget', 'rate_low': 30, 'rate_high': 50},
            ],
            'Tarangire National Park': [
                {'name': 'Tarangire Treetops Lodge', 'tier': 'luxury', 'rate_low': 700, 'rate_high': 950},
                {'name': 'Tarangire Sopa Lodge', 'tier': 'semi_luxury', 'rate_low': 280, 'rate_high': 380},
                {'name': 'Maramboi Tented Lodge', 'tier': 'mid_range', 'rate_low': 180, 'rate_high': 260},
                {'name': 'Tarangire Safari Lodge', 'tier': 'mid_range', 'rate_low': 150, 'rate_high': 220},
            ],
            'Arusha': [
                {'name': 'Gran Meliá Arusha', 'tier': 'luxury', 'rate_low': 350, 'rate_high': 500},
                {'name': 'Mount Meru Hotel', 'tier': 'semi_luxury', 'rate_low': 150, 'rate_high': 220},
                {'name': 'Arusha Coffee Lodge', 'tier': 'semi_luxury', 'rate_low': 280, 'rate_high': 380},
                {'name': 'African Tulip Hotel', 'tier': 'mid_range', 'rate_low': 100, 'rate_high': 150},
                {'name': 'Outpost Lodge', 'tier': 'mid_range', 'rate_low': 80, 'rate_high': 120},
                {'name': 'Arusha Backpackers', 'tier': 'budget', 'rate_low': 25, 'rate_high': 40},
            ],
        }
        
        created = 0
        for dest_name, hotels in hotels_data.items():
            try:
                destination = Destination.objects.get(name=dest_name)
                for hotel in hotels:
                    _, was_created = HotelRate.objects.get_or_create(
                        name=hotel['name'],
                        destination=destination,
                        defaults={
                            'tier': hotel['tier'],
                            'room_type': 'double',
                            'meal_plan': 'fb',  # Full board
                            'rate_low_season': Decimal(str(hotel['rate_low'])),
                            'rate_high_season': Decimal(str(hotel['rate_high'])),
                            'is_active': True,
                        }
                    )
                    if was_created:
                        created += 1
            except Destination.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Destination not found: {dest_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Hotels: {created} created'))

    def populate_flights(self):
        """Populate flight rates from scraper data."""
        from tour.flight_scraper import populate_flight_rates_from_scraper
        
        created, updated = populate_flight_rates_from_scraper()
        self.stdout.write(self.style.SUCCESS(f'✅ Flights: {created} created, {updated} updated'))

    def populate_activities(self):
        """Populate activity and park fee rates."""
        from tour.models import Destination, ActivityRate
        
        # Park fees (per person per day)
        park_fees = [
            {'name': 'Serengeti National Park Entry', 'dest': 'Serengeti National Park', 'type': 'park_fee', 'adult': 70, 'child': 20},
            {'name': 'Ngorongoro Crater Entry', 'dest': 'Ngorongoro Crater', 'type': 'park_fee', 'adult': 70, 'child': 20},
            {'name': 'Ngorongoro Crater Vehicle Fee', 'dest': 'Ngorongoro Crater', 'type': 'park_fee', 'adult': 295, 'child': 295},
            {'name': 'Tarangire National Park Entry', 'dest': 'Tarangire National Park', 'type': 'park_fee', 'adult': 53, 'child': 17},
            {'name': 'Lake Manyara National Park Entry', 'dest': 'Lake Manyara National Park', 'type': 'park_fee', 'adult': 53, 'child': 17},
            {'name': 'Arusha National Park Entry', 'dest': 'Arusha', 'type': 'park_fee', 'adult': 53, 'child': 17},
        ]
        
        # Activities
        activities = [
            {'name': 'Hot Air Balloon Safari', 'dest': 'Serengeti National Park', 'type': 'balloon_safari', 'adult': 599, 'child': 450, 'duration': '3 hours'},
            {'name': 'Game Drive (Half Day)', 'dest': 'Serengeti National Park', 'type': 'game_drive', 'adult': 50, 'child': 30, 'duration': '4 hours'},
            {'name': 'Game Drive (Full Day)', 'dest': 'Serengeti National Park', 'type': 'game_drive', 'adult': 80, 'child': 50, 'duration': '8 hours'},
            {'name': 'Spice Tour', 'dest': 'Zanzibar', 'type': 'spice_tour', 'adult': 40, 'child': 25, 'duration': '4 hours'},
            {'name': 'Stone Town Walking Tour', 'dest': 'Zanzibar', 'type': 'city_tour', 'adult': 30, 'child': 20, 'duration': '3 hours'},
            {'name': 'Snorkeling Trip', 'dest': 'Zanzibar', 'type': 'snorkeling', 'adult': 60, 'child': 40, 'duration': '5 hours'},
            {'name': 'Scuba Diving (2 dives)', 'dest': 'Zanzibar', 'type': 'diving', 'adult': 150, 'child': 0, 'duration': '4 hours'},
            {'name': 'Prison Island Tour', 'dest': 'Zanzibar', 'type': 'other', 'adult': 50, 'child': 30, 'duration': '3 hours'},
            {'name': 'Maasai Village Visit', 'dest': 'Ngorongoro Crater', 'type': 'cultural_visit', 'adult': 30, 'child': 20, 'duration': '2 hours'},
            {'name': 'Walking Safari', 'dest': 'Arusha', 'type': 'walking_safari', 'adult': 40, 'child': 25, 'duration': '3 hours'},
        ]
        
        created = 0
        for item in park_fees + activities:
            try:
                destination = Destination.objects.get(name=item['dest'])
                _, was_created = ActivityRate.objects.get_or_create(
                    name=item['name'],
                    destination=destination,
                    defaults={
                        'activity_type': item['type'],
                        'rate_adult': Decimal(str(item['adult'])),
                        'rate_child': Decimal(str(item['child'])),
                        'duration': item.get('duration', 'Per day'),
                        'is_active': True,
                    }
                )
                if was_created:
                    created += 1
            except Destination.DoesNotExist:
                pass
        
        self.stdout.write(self.style.SUCCESS(f'✅ Activities: {created} created'))

    def populate_transport(self):
        """Populate ground transport rates."""
        from tour.models import TransportRate
        
        transport_data = [
            {'type': 'sedan', 'rate': 80, 'passengers': 3, 'fuel': 8.0, 'desc': 'Standard sedan for airport transfers'},
            {'type': 'suv', 'rate': 150, 'passengers': 4, 'fuel': 12.0, 'desc': '4x4 SUV suitable for game drives'},
            {'type': 'landcruiser', 'rate': 250, 'passengers': 6, 'fuel': 15.0, 'desc': 'Pop-up roof Land Cruiser for safaris'},
            {'type': 'minivan', 'rate': 180, 'passengers': 7, 'fuel': 10.0, 'desc': 'Safari minivan with pop-up roof'},
            {'type': 'minibus', 'rate': 300, 'passengers': 15, 'fuel': 14.0, 'desc': 'Minibus for larger groups'},
            {'type': 'bus', 'rate': 500, 'passengers': 35, 'fuel': 20.0, 'desc': 'Coach bus for large groups'},
        ]
        
        created = 0
        for item in transport_data:
            _, was_created = TransportRate.objects.get_or_create(
                vehicle_type=item['type'],
                defaults={
                    'description': item['desc'],
                    'rate_per_day': Decimal(str(item['rate'])),
                    'fuel_consumption': Decimal(str(item['fuel'])),
                    'max_passengers': item['passengers'],
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ Transport: {created} created'))
