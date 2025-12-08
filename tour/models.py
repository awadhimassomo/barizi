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

