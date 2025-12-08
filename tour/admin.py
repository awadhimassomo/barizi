from django.contrib import admin
from .models import (
    Vendor,
    TourPackage,
    Itinerary,
    Review,
    Booking,
    Trip,
    Event,
    Attendee,
    EventSession,
)

class ItineraryInline(admin.TabularInline):
    model = Itinerary
    extra = 1

class TourPackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'price', 'availability', 'start_date', 'end_date', 'operator')
    list_filter = ('location', 'start_date', 'price')
    search_fields = ('title', 'location', 'operator__username')
    inlines = [ItineraryInline]

admin.site.register(Vendor)
admin.site.register(TourPackage, TourPackageAdmin)
admin.site.register(Itinerary)
admin.site.register(Review)
admin.site.register(Booking)
admin.site.register(Trip)
admin.site.register(Event)
admin.site.register(Attendee)
admin.site.register(EventSession)
