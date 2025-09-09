from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404
from django.views import View
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import CreateView
from .forms import ItineraryForm, TourPackageForm
from .models import  Attendee, Booking, Itinerary, TourPackage, Trip, Vendor,Event
from .serializers import   EventSerializer, VendorSerializer
from users.permissions import IsCustomer, IsPlanner, IsOperator
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework import status
from .models import TourPackage, Itinerary, Review, Vendor
from .serializers import TourPackageSerializer, ItinerarySerializer, ReviewSerializer, VendorSerializer
from itertools import chain


#..................................views.............................................................................................................

@login_required
def dashboard(request):
    return render(request, "tours/dashboard.html")# Import role-based permissions



# Vendor API (For Operators)
class VendorListCreateView(generics.ListCreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated, IsOperator]
    

class TripCreateView(CreateView):
    model = Trip
    fields = ['trip_name', 'num_people', 'vendors', 'itinerary_details', 'start_date', 'end_date']
    template_name = "tours/create_trip.html"
    success_url = reverse_lazy('dashboard')

class VendorCreateView(CreateView):
    model = Vendor
    fields = ['name', 'service_type', 'description', 'price', 'location', 'availability', 'start_date']
    template_name = "tours/create_vendor.html"
    success_url = reverse_lazy('vendor-list')
    
def create_tour_package(request):
    if request.method == 'POST':
        form = TourPackageForm(request.POST, request.FILES)
        if form.is_valid():
            # ✅ Save the tour package
            tour_package = form.save(commit=False)
            tour_package.operator = request.user  # Ensure user is logged in
            tour_package.save()

            # ✅ Save itineraries
            day_count = 1
            while f'itinerary_day_{day_count}' in request.POST:
                Itinerary.objects.create(
                    tour=tour_package,
                    day_number=request.POST.get(f'itinerary_day_{day_count}'),
                    title=request.POST.get(f'itinerary_title_{day_count}'),
                    description=request.POST.get(f'itinerary_description_{day_count}'),
                    accommodation=request.POST.get(f'itinerary_accommodation_{day_count}')
                )
                day_count += 1

            return redirect('marketplace')  # Redirect after successful save
        else:
            # ✅ Log form errors if not valid
            print("Form errors:", form.errors)
    else:
        form = TourPackageForm()


    return render(request, 'tours/create_tour.html', {'form': form, })

@login_required
def operator_booking_list(request):
    bookings = Booking.objects.filter(tour__operator=request.user).order_by('-created_at')
    return render(request, 'tours/Listing_booking.html', {'bookings': bookings})

@login_required
def vendor_list(request):
    vendors = Vendor.objects.all() 
    return render(request, 'tours/vendor.html', {'vendors': vendors})


#...............................contentview...........................................................................
    
def rental_list(request):
    return render(request, 'tours/rentals.html')



def rentals_list(request):
    rentals = Rental.objects.all()
    print("Rentals found:", rentals)  # Debugging line
    return render(request, "rentals.html", {"rentals": rentals})



#......................................websiteviews.....................................................................................

def restaurants_view(request):
    return render(request, 'pages/restaurant.html')


def flightsView(request):
    return render(request, 'pages/flights.html')

def hotelsView(request):
    return render(request, 'pages/hotels.html')

def cruisesView(request):
    return render(request, 'pages/cruises.html')

def event_detail(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    return render(request, 'pages/eventdetails.html', {'event': event})


def marketplace_view(request):
    tours = TourPackage.objects.all() 
    print("Tours from DB:", tours) 
    return render(request, 'pages/marketplace.html', {'tours': tours, 'debug_message': 'THIS IS THE CORRECT TEMPLATE'})

#..............................................................api...............................................................................................................................................

# ---- Tour Package Views ----
class TourPackageView(APIView):
    def get(self, request):
        tours = TourPackage.objects.all()
        serializer = TourPackageSerializer(tours, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TourPackageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TourPackageDetailView(APIView):
    def get_object(self, pk):
        try:
            return TourPackage.objects.get(pk=pk)
        except TourPackage.DoesNotExist:
            return None

    def get(self, request, pk):
        tour = self.get_object(pk)
        if not tour:
            return Response({"error": "Tour not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = TourPackageSerializer(tour)
        return Response(serializer.data)

    def put(self, request, pk):
        tour = self.get_object(pk)
        if not tour:
            return Response({"error": "Tour not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = TourPackageSerializer(tour, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tour = self.get_object(pk)
        if not tour:
            return Response({"error": "Tour not found"}, status=status.HTTP_404_NOT_FOUND)
        tour.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---- Itinerary Views ----
class ItineraryView(APIView):
    def get(self, request):
        itineraries = Itinerary.objects.all()
        serializer = ItinerarySerializer(itineraries, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ItinerarySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---- Review Views ----
class ReviewView(APIView):
    def get(self, request):
        reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---- Vendor Views ----
class VendorView(APIView):
    def get(self, request):
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---- Custom GET Route Example ----
@api_view(['GET'])
def get_tours_by_location(request):
    location = request.query_params.get('location', None)
    if location:
        tours = TourPackage.objects.filter(location__icontains=location)
    else:
        tours = TourPackage.objects.all()
    serializer = TourPackageSerializer(tours, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def unified_feed(request):
    # Fetch data from TourPackage and Event models
    tours = TourPackage.objects.all()
    events = Event.objects.all()

    # Serialize data
    tour_data = TourPackageSerializer(tours, many=True).data
    event_data = EventSerializer(events, many=True).data

    # Add content_type for frontend identification
    for item in tour_data:
        item['content_type'] = 'tour'

    for item in event_data:
        # Use the event category (e.g., 'festival', 'marathon') for sub-classification
        item['content_type'] = item.get('category', 'event')  # Defaults to 'event' if no category

    # Combine and sort by 'created_at' or 'start_date'
    combined_feed = sorted(
        chain(tour_data, event_data),
        key=lambda x: x.get('created_at') or x.get('start_date'),
        reverse=True  # Newest items first
    )

    return Response(combined_feed, status=status.HTTP_200_OK)

#............................................................planner view.....................................................................

@login_required
def create_event(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        date = request.POST.get('date')
        location = request.POST.get('location')

        # Validate required fields
        if not title or not date or not location:
            messages.error(request, 'All fields are required!')
            return render(request, 'events/eventcreate.html')

        # Create Event
        Event.objects.create(
            title=title,
            date=date,
            location=location,
            planner=request.user
        )

        messages.success(request, 'Event created successfully!')
        return redirect('event-dashboard')

    # Handle GET request to display form
    return render(request, 'events/eventcreate.html')


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        event.title = request.POST.get('title')
        event.date = request.POST.get('date')
        event.location = request.POST.get('location')
        event.save()

        messages.success(request, 'Event updated successfully!')
        return redirect('dashboard')

    return render(request, 'edit_event.html', {'event': event})

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()

    messages.success(request, 'Event deleted successfully!')
    return redirect('dashboard')

@login_required
def planner_dashboard(request):
    # You can pass events or user data if needed
    return render(request, 'events/eventdashboard.html', {'user': request.user})

@login_required
def event_dashboard(request):
    # Fetch event data here if needed
    context = {
        'events': [],  # Replace with actual events from the database
    }
    return render(request, 'events/eventdashboard.html', context)


@login_required
def attendee_list(request):
    attendees = Attendee.objects.all()
    return render(request, 'events/attendee_list.html', {'attendees': attendees})

@login_required
def profile_view(request):
    return render(request, 'events/profile.html')

@login_required
def edit_profile_view(request):
    return render(request, 'events/edit_profile.html')

@login_required
def change_password_view(request):
    return render(request, 'events/change_password.html')

@login_required
def settings_view(request):
    return render(request, 'users/settings.html')
