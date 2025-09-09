from django.urls import path
from .views import ItineraryView, ReviewView, TourPackageDetailView, TourPackageView, TripCreateView, VendorCreateView, VendorListCreateView, VendorView, attendee_list, change_password_view, create_event, create_tour_package, cruisesView, dashboard, delete_event, edit_event, edit_profile_view, event_dashboard, event_detail, flightsView, get_tours_by_location, hotelsView, marketplace_view, operator_booking_list, planner_dashboard, rental_list, rentals_list, profile_view, restaurants_view, settings_view, unified_feed, vendor_list

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('tours/', create_tour_package, name='tour-list'), 
    path('trips/create/', TripCreateView.as_view(), name='create-trip'),  
    path('vendors/', VendorListCreateView.as_view(), name='vendor-list'),
    path('vendors/create/', VendorCreateView.as_view(), name='create-vendor'),
    path('dashboard/', dashboard, name='dashboard'),
    path('rentals/', rental_list, name='rentals-page'),  # URL for rentals.html
    path("rental-items/", rentals_list, name="rental-items"),
    path('listbookings/', operator_booking_list, name='operator_booking_list'),
    path('litvendors/', vendor_list, name='vendorlist'),
    path('restaurants/', restaurants_view, name='restaurants'),
    path('flights/', flightsView, name='flights'),
    path('hotels/', hotelsView, name='hotels'),
    path('cruises/', cruisesView, name='cruises'),
    path('events/', event_dashboard, name='event-list'), # Added new path for /events/
    path('events/<slug:event_slug>/', event_detail, name='event_detail'),
    path('marketplace/', marketplace_view, name='marketplace'),
    path('create-tour/', create_tour_package, name='tour-create'),

     # Tour Packages
    path('api/tours/', TourPackageView.as_view(), name='tour-list-create'),
    path('api/tours/<int:pk>/', TourPackageDetailView.as_view(), name='tour-detail'),

    # Itineraries
    path('api/itineraries/', ItineraryView.as_view(), name='itinerary-list-create'),

    # Reviews
    path('api/reviews/', ReviewView.as_view(), name='review-list-create'),

    # Vendors
    path('api/vendors/', VendorView.as_view(), name='vendor-list-create'),

    # Custom Route for Filtering
    path('api/tours/location/', get_tours_by_location, name='tours-by-location'),

    path('api/feed/', unified_feed, name='unified-feed'), 

    path('create-event/', create_event, name='create-event'),
    path('edit-event/<int:event_id>/', edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', delete_event, name='delete_event'),
    path('planner-dashboard/', planner_dashboard, name='planner-dashboard'),
    path('attendees/', attendee_list, name='attendee-list'),
    path('event-dashboard/', event_dashboard, name='event-dashboard'),
    path('profile/', profile_view, name='profile'),
    path('edit-profile/', edit_profile_view, name='edit-profile'),
    path('change-password/', change_password_view, name='change-password'),
    path('settings/', settings_view, name='settings'),

     

]


