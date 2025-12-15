from django.db import models
from django.conf import settings
import slugify


class Vendor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendors")
    name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=50, choices=[
        ('hotel', 'Hotel'),
        ('transport', 'Transport'),
        ('food', 'Food'),
        ('flight', 'Flight')
    ])
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price per unit (e.g., per night for hotels)
    location = models.CharField(max_length=255)
    availability = models.IntegerField(default=10)  # Available slots
    start_date = models.DateField(blank=True, null=True)  # Optional for scheduled services like flights
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.service_type})"

    
class TourPackage(models.Model):
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tour_packages"
    )
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='tourimages/', default='tour_images/default.jpg')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    reviews_count = models.IntegerField(default=0)
    description = models.TextField()
    duration = models.CharField(max_length=100)
    includes = models.TextField()
    excludes = models.TextField()
    cancellation_policy = models.TextField()
    special_offer = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    min_people = models.PositiveIntegerField(default=1)
    max_people = models.PositiveIntegerField(default=10)
    availability = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255)
    coordinates = models.CharField(max_length=100, blank=True, null=True)
    vendors = models.ManyToManyField(Vendor, related_name="tour_packages", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    


class Itinerary(models.Model):
    tour = models.ForeignKey('TourPackage', on_delete=models.CASCADE, related_name='itineraries')
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    accommodation = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"


class Review(models.Model):
    tour = models.ForeignKey(TourPackage, on_delete=models.CASCADE, related_name="tour_reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user} for {self.tour.title}"

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, related_name="bookings", null=True, blank=True)  # ✅ Users can book vendor services separately
    tour = models.ForeignKey(TourPackage, on_delete=models.SET_NULL, related_name="bookings", null=True, blank=True)  # ✅ Users can book tours
    num_people = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    installment_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # ✅ Track installment payments
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking by {self.user.full_name} - {self.status}"
    


class Trip(models.Model):
    planner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trips")  # ✅ The user planning the trip
    trip_name = models.CharField(max_length=255)
    num_people = models.PositiveIntegerField()
    vendors = models.ManyToManyField('Vendor', blank=True)  # ✅ Vendors involved in the trip
    itinerary_details = models.TextField()  # ✅ Schedule of activities
    start_date = models.DateField()  # ✅ When the trip starts
    end_date = models.DateField()  # ✅ When the trip ends
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trip_name} by {self.planner.full_name}"


from django.db import models
from django.utils.text import slugify

class Event(models.Model):
    EVENT_CATEGORIES = [
        ('festival', 'Festival'),
        ('concert', 'Concert'),
        ('workshop', 'Workshop'),
        ('conference', 'Conference'),
        ('marathon', 'Marathon'),
        ('sports', 'Sports Event'),
        ('exhibition', 'Exhibition'),
        ('nightlife', 'Nightlife'),
        ('tour', 'Tour'),
        ('webinar', 'Webinar'),
        ('networking', 'Networking Event'),
    ]

    EVENT_STATUSES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Basic Details
    planner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='planned_events', on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=EVENT_CATEGORIES, default='festival')

    # Event Date & Time
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(help_text="Duration in minutes", null=True, blank=True)

    # Location Details
    is_online = models.BooleanField(default=False)
    is_hybrid = models.BooleanField(default=False)
    online_link = models.URLField(blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Event Media
    image = models.ImageField(upload_to='events/')
    gallery = models.JSONField(blank=True, null=True, help_text="List of image URLs")
    video_link = models.URLField(blank=True, null=True, help_text="Optional promotional video link")

    # Ticketing & Capacity
    capacity = models.PositiveIntegerField(null=True, blank=True)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    registration_link = models.URLField(blank=True, null=True)

    # Invitations & QR
    join_url = models.URLField(blank=True, null=True, help_text="Public URL used for invites/QR")
    qr_code = models.ImageField(upload_to='event_qr/', blank=True, null=True)

    # Event Status
    status = models.CharField(max_length=20, choices=EVENT_STATUSES, default='upcoming')

    # SEO & Meta
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.CharField(max_length=255, blank=True, null=True)

    # Additional Details
    has_exhibitors = models.BooleanField(default=False)
    extra_details = models.JSONField(blank=True, null=True, help_text="For storing custom event data")

    def save(self, *args, **kwargs):
        # Auto-generate slug from title and ensure uniqueness
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 2

            # Ensure the slug is unique
            from .models import Event  # local import to avoid circulars at module load
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        # Ensure 'is_hybrid' consistency
        if self.is_hybrid:
            self.is_online = True

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Attendee(models.Model):
    event = models.ForeignKey(Event, related_name='attendees', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    ticket_type = models.CharField(max_length=50, choices=[('regular', 'Regular'), ('vip', 'VIP')], default='regular')
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.event.title}"


class EventSession(models.Model):
    event = models.ForeignKey(Event, related_name='sessions', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    speaker = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.event.title})"


class ExhibitorSpace(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="exhibitor_spaces")
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_slots = models.IntegerField(default=1)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.event.title}"


class ExhibitorBooking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    space = models.ForeignKey(ExhibitorSpace, on_delete=models.CASCADE, related_name="bookings")
    exhibitor_name = models.CharField(max_length=255)
    business_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} - {self.space.name} ({self.status})"


class ServiceProvider(models.Model):
    """Service providers that can be matched with event planners."""
    SERVICE_TYPES = [
        ('mc', 'MC / Host'),
        ('venue', 'Venue / Space'),
        ('catering', 'Food & Catering'),
        ('photography', 'Photography'),
        ('videography', 'Videography'),
        ('sound', 'Sound & Audio'),
        ('lighting', 'Lighting'),
        ('decoration', 'Decoration'),
        ('security', 'Security'),
        ('printing', 'Printing & Publishing'),
        ('transport', 'Transport'),
        ('entertainment', 'Entertainment'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="service_providers", null=True, blank=True)
    name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES)
    description = models.TextField(blank=True, null=True)
    price_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    image = models.ImageField(upload_to='service_providers/', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    reviews_count = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"

    class Meta:
        ordering = ['-rating', 'name']


class ServiceMatch(models.Model):
    """Track service matches/requests for events."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('confirmed', 'Confirmed'),
        ('declined', 'Declined'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="service_matches")
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name="matches")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'provider')

    def __str__(self):
        return f"{self.event.title} - {self.provider.name}"


# =============================================================================
# TOUR PRICING & ITINERARY GENERATION MODELS
# =============================================================================

class Destination(models.Model):
    """Popular destinations with relevant info for itinerary generation."""
    name = models.CharField(max_length=255)  # e.g., "Serengeti National Park"
    region = models.CharField(max_length=100)  # e.g., "Northern Circuit"
    country = models.CharField(max_length=100, default="Tanzania")
    description = models.TextField(blank=True)
    best_time_to_visit = models.CharField(max_length=255, blank=True)  # e.g., "June-October"
    highlights = models.TextField(blank=True)  # Key attractions
    avg_time_needed = models.PositiveIntegerField(default=2, help_text="Recommended days to spend")
    coordinates = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}, {self.region}"

    class Meta:
        ordering = ['region', 'name']


class HotelRate(models.Model):
    """Admin-managed hotel pricing for accurate itinerary costing."""
    TIER_CHOICES = [
        ('budget', 'Budget'),
        ('mid_range', 'Mid-Range'),
        ('semi_luxury', 'Semi-Luxury'),
        ('luxury', 'Luxury'),
    ]
    ROOM_TYPES = [
        ('single', 'Single'),
        ('double', 'Double/Twin'),
        ('triple', 'Triple'),
        ('family', 'Family Room'),
    ]
    MEAL_PLANS = [
        ('bb', 'Bed & Breakfast'),
        ('hb', 'Half Board'),
        ('fb', 'Full Board'),
        ('ai', 'All Inclusive'),
    ]

    name = models.CharField(max_length=255)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='hotels')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='double')
    meal_plan = models.CharField(max_length=10, choices=MEAL_PLANS, default='fb')
    
    # Pricing (per person per night)
    rate_low_season = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USD - Low Season")
    rate_high_season = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USD - High Season")
    
    # Season dates
    high_season_start = models.CharField(max_length=10, default="06-01", help_text="MM-DD format")
    high_season_end = models.CharField(max_length=10, default="10-31", help_text="MM-DD format")
    
    contact_info = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_tier_display()}) - {self.destination.name}"

    class Meta:
        ordering = ['destination', 'tier', 'name']


class TransportRate(models.Model):
    """Admin-managed transport/vehicle pricing."""
    VEHICLE_TYPES = [
        ('sedan', 'Sedan Car'),
        ('suv', '4x4 SUV'),
        ('landcruiser', 'Toyota Land Cruiser'),
        ('minivan', 'Minivan (7-seater)'),
        ('minibus', 'Minibus (15-seater)'),
        ('bus', 'Coach Bus (30+ seater)'),
    ]

    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    description = models.CharField(max_length=255, blank=True)
    
    # Pricing
    rate_per_day = models.DecimalField(max_digits=10, decimal_places=2, help_text="Daily rate in USD (includes driver)")
    rate_per_km = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Additional per-km charge if applicable")
    fuel_consumption = models.DecimalField(max_digits=4, decimal_places=1, help_text="Liters per 100km")
    
    max_passengers = models.PositiveIntegerField()
    ideal_for = models.CharField(max_length=255, blank=True, help_text="e.g., 'Safari, rough terrain'")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_vehicle_type_display()} - ${self.rate_per_day}/day"

    class Meta:
        ordering = ['vehicle_type']


class ActivityRate(models.Model):
    """Admin-managed activity/park fees pricing."""
    ACTIVITY_TYPES = [
        ('park_fee', 'National Park Entry Fee'),
        ('game_drive', 'Game Drive'),
        ('walking_safari', 'Walking Safari'),
        ('boat_safari', 'Boat Safari'),
        ('balloon_safari', 'Hot Air Balloon Safari'),
        ('cultural_visit', 'Cultural Village Visit'),
        ('hiking', 'Hiking/Trekking'),
        ('snorkeling', 'Snorkeling'),
        ('diving', 'Scuba Diving'),
        ('spice_tour', 'Spice Tour'),
        ('city_tour', 'City Tour'),
        ('other', 'Other Activity'),
    ]

    name = models.CharField(max_length=255)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    
    # Pricing
    rate_adult = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per adult in USD")
    rate_child = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Price per child in USD")
    
    duration = models.CharField(max_length=50, blank=True, help_text="e.g., '3 hours', 'Full day'")
    description = models.TextField(blank=True)
    includes = models.TextField(blank=True, help_text="What's included in the price")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        dest = f" - {self.destination.name}" if self.destination else ""
        return f"{self.name}{dest}"

    class Meta:
        ordering = ['activity_type', 'name']


class FuelPrice(models.Model):
    """Current fuel prices - updated by admin."""
    fuel_type = models.CharField(max_length=20, choices=[('petrol', 'Petrol'), ('diesel', 'Diesel')])
    price_per_liter = models.DecimalField(max_digits=6, decimal_places=2, help_text="Price in TZS")
    price_per_liter_usd = models.DecimalField(max_digits=6, decimal_places=2, help_text="Price in USD")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_fuel_type_display()} - {self.price_per_liter} TZS/L"

    class Meta:
        verbose_name_plural = "Fuel Prices"


class FlightRate(models.Model):
    """Admin-managed domestic/regional flight pricing."""
    AIRLINES = [
        ('precision', 'Precision Air'),
        ('coastal', 'Coastal Aviation'),
        ('auric', 'Auric Air'),
        ('flightlink', 'FlightLink'),
        ('air_tanzania', 'Air Tanzania'),
        ('fastjet', 'Fastjet'),
        ('other', 'Other'),
    ]
    
    airline = models.CharField(max_length=30, choices=AIRLINES)
    origin = models.CharField(max_length=100, help_text="e.g., JRO - Kilimanjaro, DAR - Dar es Salaam")
    origin_code = models.CharField(max_length=10, blank=True, help_text="Airport code e.g., JRO, DAR, ZNZ")
    destination = models.CharField(max_length=100, help_text="e.g., ZNZ - Zanzibar, SEU - Seronera")
    destination_code = models.CharField(max_length=10, blank=True, help_text="Airport code")
    
    # Pricing
    price_economy = models.DecimalField(max_digits=10, decimal_places=2, help_text="Economy class price per person USD")
    price_business = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Business class if available")
    baggage_allowance = models.CharField(max_length=50, default="15kg", help_text="e.g., 15kg, 20kg")
    
    # Flight details
    flight_duration = models.CharField(max_length=20, blank=True, help_text="e.g., 1h 30m")
    frequency = models.CharField(max_length=100, blank=True, help_text="e.g., Daily, Mon/Wed/Fri")
    
    notes = models.TextField(blank=True, help_text="Additional info about this route")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_airline_display()}: {self.origin_code or self.origin} → {self.destination_code or self.destination} (${self.price_economy})"
    
    class Meta:
        ordering = ['origin', 'destination']
        verbose_name = "Flight Rate"
        verbose_name_plural = "Flight Rates"


class TourRequest(models.Model):
    """Client tour request - captures requirements before AI generation."""
    TOUR_TYPES = [
        ('budget', 'Budget'),
        ('mid_range', 'Mid-Range'),
        ('semi_luxury', 'Semi-Luxury'),
        ('luxury', 'Luxury'),
    ]
    GROUP_TYPES = [
        ('solo', 'Solo Traveler'),
        ('couple', 'Couple'),
        ('family', 'Family'),
        ('small_group', 'Small Group (3-6)'),
        ('large_group', 'Large Group (7+)'),
        ('corporate', 'Corporate/Team'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('itinerary_generated', 'Itinerary Generated'),
        ('sent_to_client', 'Sent to Client'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Operator who creates/manages this request
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tour_requests')
    
    # Client info
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=50, blank=True)
    
    # Tour requirements
    tour_type = models.CharField(max_length=20, choices=TOUR_TYPES)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES)
    num_adults = models.PositiveIntegerField(default=2)
    num_children = models.PositiveIntegerField(default=0)
    
    # Budget
    budget_per_person = models.DecimalField(max_digits=10, decimal_places=2, help_text="Budget per person in USD")
    budget_flexible = models.BooleanField(default=False, help_text="Is budget flexible?")
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, help_text="Operator profit margin %")
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    dates_flexible = models.BooleanField(default=False)
    
    # Preferred Start Time
    START_TIME_CHOICES = [
        ('early_morning', 'Early Morning (5:00 - 7:00 AM)'),
        ('morning', 'Morning (7:00 - 9:00 AM)'),
        ('mid_morning', 'Mid-Morning (9:00 - 11:00 AM)'),
        ('flexible', 'Flexible / No Preference'),
    ]
    preferred_start_time = models.CharField(max_length=20, choices=START_TIME_CHOICES, default='morning', 
                                           help_text="What time does the guest prefer to start each day?")
    
    # Guest Location & Arrival
    ARRIVAL_METHODS = [
        ('flight_international', 'International Flight'),
        ('flight_domestic', 'Domestic Flight'),
        ('already_in_country', 'Already in Tanzania'),
        ('land_border', 'Land Border Crossing'),
        ('ferry', 'Ferry/Sea'),
    ]
    arrival_method = models.CharField(max_length=30, choices=ARRIVAL_METHODS, default='flight_international')
    arrival_location = models.CharField(max_length=255, blank=True, help_text="Airport/City where guest arrives (e.g., JRO - Kilimanjaro, DAR - Dar es Salaam)")
    current_location = models.CharField(max_length=255, blank=True, help_text="Where guest is currently (if already in Tanzania)")
    pickup_location = models.CharField(max_length=255, blank=True, help_text="Where to pick up the guest")
    departure_location = models.CharField(max_length=255, blank=True, help_text="Where guest departs from (e.g., ZNZ - Zanzibar)")
    
    # Preferences
    preferred_destinations = models.ManyToManyField(Destination, blank=True, related_name='tour_requests')
    special_requests = models.TextField(blank=True, help_text="e.g., 'Must visit Zanzibar', 'Interested in wildlife photography'")
    dietary_requirements = models.CharField(max_length=255, blank=True)
    mobility_requirements = models.CharField(max_length=255, blank=True)
    
    # Generated content
    generated_itinerary = models.TextField(blank=True, help_text="AI-generated itinerary JSON")
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, help_text="Internal notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client_name} - {self.start_date} ({self.get_tour_type_display()})"

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    @property
    def total_travelers(self):
        return self.num_adults + self.num_children

    class Meta:
        ordering = ['-created_at']


class UploadedPackage(models.Model):
    """Ready-made tour packages uploaded with PDF itineraries and images."""
    
    PACKAGE_STATUS = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]
    
    PACKAGE_TYPES = [
        ('safari', 'Safari'),
        ('beach', 'Beach Holiday'),
        ('cultural', 'Cultural Tour'),
        ('adventure', 'Adventure'),
        ('honeymoon', 'Honeymoon'),
        ('family', 'Family Package'),
        ('budget', 'Budget Package'),
        ('luxury', 'Luxury Package'),
        ('combined', 'Combined Safari & Beach'),
        ('other', 'Other'),
    ]
    
    # Owner
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_packages')
    
    # Basic Info
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Brief description of the package")
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, default='safari')
    duration_days = models.PositiveIntegerField(default=1, help_text="Number of days")
    
    # Destinations
    destinations = models.CharField(max_length=500, blank=True, help_text="Comma-separated list of destinations")
    
    # Pricing
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_group_size = models.PositiveIntegerField(default=1)
    max_group_size = models.PositiveIntegerField(default=20)
    
    # Files
    pdf_itinerary = models.FileField(upload_to='package_pdfs/')
    cover_image = models.ImageField(upload_to='package_images/')
    
    # Additional Images (optional)
    image_2 = models.ImageField(upload_to='package_images/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='package_images/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='package_images/', blank=True, null=True)
    
    # Internal: Extracted content for system use (hidden from users)
    extracted_text = models.TextField(blank=True)
    is_analyzed = models.BooleanField(default=False)
    
    # Sharing
    share_token = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Token for sharing with clients")
    is_public = models.BooleanField(default=False, help_text="Show in public marketplace")
    
    # Status
    status = models.CharField(max_length=20, choices=PACKAGE_STATUS, default='draft')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_package_type_display()})"
    
    def save(self, *args, **kwargs):
        # Generate share token if not exists
        if not self.share_token:
            import secrets
            self.share_token = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)
    
    @property
    def all_images(self):
        """Return list of all available images."""
        images = [self.cover_image]
        if self.image_2:
            images.append(self.image_2)
        if self.image_3:
            images.append(self.image_3)
        if self.image_4:
            images.append(self.image_4)
        return images
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Uploaded Package'
        verbose_name_plural = 'Uploaded Packages'


# ═══════════════════════════════════════════════════════════════════════════════
# AI TRAINING DATA PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class ScrapingSource(models.Model):
    """Tour operator websites to scrape itineraries from."""
    
    name = models.CharField(max_length=255, help_text="Tour operator name")
    base_url = models.URLField(help_text="Website base URL")
    is_active = models.BooleanField(default=True)
    requires_javascript = models.BooleanField(default=False, help_text="Use Selenium/Playwright if True")
    rate_limit_seconds = models.PositiveIntegerField(default=5, help_text="Seconds between requests")
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    total_scraped = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.base_url})"
    
    class Meta:
        verbose_name = 'Scraping Source'
        verbose_name_plural = 'Scraping Sources'


class ScrapeQueue(models.Model):
    """Queue of URLs to scrape."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    source = models.ForeignKey(ScrapingSource, on_delete=models.CASCADE, related_name='queue_items')
    url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.PositiveIntegerField(default=0, help_text="Higher = processed first")
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.url} ({self.status})"
    
    class Meta:
        ordering = ['-priority', 'created_at']
        verbose_name = 'Scrape Queue Item'
        verbose_name_plural = 'Scrape Queue'


class RawItinerary(models.Model):
    """Raw scraped itinerary data - the messy text exactly as found."""
    
    SOURCE_TYPES = [
        ('scraped', 'Web Scraped'),
        ('uploaded', 'PDF Upload'),
        ('manual', 'Manual Entry'),
    ]
    
    # Source tracking
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='scraped')
    source = models.ForeignKey(ScrapingSource, on_delete=models.SET_NULL, null=True, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    uploaded_package = models.ForeignKey(UploadedPackage, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='raw_itineraries')
    
    # Raw content
    raw_html = models.TextField(blank=True, help_text="Original HTML if scraped")
    raw_text = models.TextField(help_text="Extracted plain text")
    page_title = models.CharField(max_length=500, blank=True)
    
    # Metadata from page
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    
    # Timestamps
    scraped_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Raw: {self.page_title[:50] if self.page_title else self.source_url[:50]}"
    
    class Meta:
        ordering = ['-scraped_at']
        verbose_name = 'Raw Itinerary'
        verbose_name_plural = 'Raw Itineraries'


class ProcessedItinerary(models.Model):
    """Clean, structured itinerary data ready for AI training."""
    
    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]
    
    BUDGET_LEVELS = [
        ('budget', 'Budget'),
        ('mid_range', 'Mid-Range'),
        ('luxury', 'Luxury'),
        ('ultra_luxury', 'Ultra Luxury'),
    ]
    
    TRIP_TYPES = [
        ('safari', 'Safari'),
        ('beach', 'Beach Holiday'),
        ('cultural', 'Cultural Tour'),
        ('adventure', 'Adventure'),
        ('honeymoon', 'Honeymoon'),
        ('family', 'Family Trip'),
        ('wildlife', 'Wildlife Photography'),
        ('trekking', 'Trekking/Hiking'),
        ('combined', 'Combined Tour'),
    ]
    
    # Link to raw data
    raw_itinerary = models.OneToOneField(RawItinerary, on_delete=models.CASCADE, related_name='processed')
    
    # Generated instruction (the "reverse prompt")
    generated_instruction = models.TextField(help_text="The user instruction that would produce this itinerary")
    
    # Extracted metadata
    title = models.CharField(max_length=500)
    destination_country = models.CharField(max_length=100, blank=True)
    destinations = models.JSONField(default=list, help_text="List of specific destinations/parks")
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    budget_level = models.CharField(max_length=20, choices=BUDGET_LEVELS, blank=True)
    estimated_price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPES, blank=True)
    group_type = models.CharField(max_length=100, blank=True, help_text="e.g., Couple, Family, Solo")
    
    # Structured itinerary data (JSON)
    itinerary_json = models.JSONField(default=dict, help_text="Day-by-day structured itinerary")
    
    # Inclusions/Exclusions
    inclusions = models.JSONField(default=list)
    exclusions = models.JSONField(default=list)
    
    # Accommodation info
    accommodations = models.JSONField(default=list, help_text="List of hotels/lodges used")
    
    # Activities
    activities = models.JSONField(default=list, help_text="List of activities")
    
    # Full clean JSON for training
    training_json = models.JSONField(default=dict, help_text="Complete JSON for model training")
    
    # Review status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='reviewed_itineraries')
    reviewer_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # GPT processing info
    gpt_model_used = models.CharField(max_length=50, blank=True)
    gpt_processing_time = models.FloatField(null=True, blank=True, help_text="Seconds")
    gpt_tokens_used = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Processed Itinerary'
        verbose_name_plural = 'Processed Itineraries'


class TrainingExport(models.Model):
    """Record of training data exports."""
    
    exported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='training_exports/')
    record_count = models.PositiveIntegerField()
    export_format = models.CharField(max_length=20, default='jsonl')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_name} ({self.record_count} records)"
    
    class Meta:
        ordering = ['-created_at']

