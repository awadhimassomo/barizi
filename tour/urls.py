from django.urls import path
from .views import ItineraryView, ReviewView, TourPackageDetailView, TourPackageView, TripCreateView, VendorCreateView, VendorListCreateView, VendorView, all_events_view, attendee_list, change_password_view, create_event, create_tour_package, cruisesView, dashboard, delete_event, edit_event, edit_event_agenda, edit_profile_view, event_dashboard, event_detail, exhibitor_book_space, ExhibitorBookingCreateView, ExhibitorSpaceListView, flightsView, get_tours_by_location, hotelsView, manage_exhibitor_bookings, manage_exhibitor_spaces, marketplace_view, my_events_view, exhibitors_overview, operator_booking_list, planner_dashboard, rental_list, rentals_list, profile_view, restaurants_view, settings_view, unified_feed, upload_invitees, vendor_list

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
    path('events/', all_events_view, name='all-events'), # All events page
    path('events/my/', my_events_view, name='my-events'), # Events created by logged-in planner
    path('events/exhibitors/overview/', exhibitors_overview, name='exhibitors_overview'),
    path('events/<int:event_id>/invitees/upload/', upload_invitees, name='upload-invitees'),
    path('events/dashboard/', event_dashboard, name='event-dashboard'), # Event management dashboard
    path('events/<slug:event_slug>/', event_detail, name='event_detail'),
    path('events/<int:event_id>/agenda/', edit_event_agenda, name='edit-event-agenda'),
    path('events/<int:event_id>/exhibitors/', manage_exhibitor_spaces, name='manage-exhibitor-spaces'),
    path('events/<int:event_id>/exhibitors/bookings/', manage_exhibitor_bookings, name='manage-exhibitor-bookings'),
    path('events/exhibitor-space/<int:space_id>/book/', exhibitor_book_space, name='exhibitor-book-space'),
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

    # Exhibitors
    path('api/events/<slug:event_slug>/exhibitor-spaces/', ExhibitorSpaceListView.as_view(), name='event-exhibitor-spaces'),
    path('api/exhibitor-spaces/<int:space_id>/bookings/', ExhibitorBookingCreateView.as_view(), name='exhibitor-space-bookings'),

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


