from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import HttpResponse
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import CreateView
from django.conf import settings
from django.utils import timezone
from .forms import ItineraryForm, TourPackageForm
from .tour_forms import TourItineraryForm, ItineraryFormSet
from .models import (
    Attendee, Booking, Event, EventSession, ExhibitorBooking, ExhibitorSpace, 
    Itinerary, TourPackage, Trip, Vendor, ServiceProvider, ServiceMatch,
    # Tour pricing models
    Destination, HotelRate, TransportRate, ActivityRate, FuelPrice, FlightRate, TourRequest,
    UploadedPackage,
    # AI Training Pipeline
    ScrapingSource, ScrapeQueue, RawItinerary, ProcessedItinerary, TrainingExport
)
from .serializers import EventSerializer, VendorSerializer, ExhibitorSpaceSerializer, ExhibitorBookingSerializer
from users.permissions import IsCustomer, IsPlanner, IsOperator
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import TourPackageSerializer, ItinerarySerializer, ReviewSerializer, VendorSerializer
from itertools import chain
import csv
from io import TextIOWrapper, BytesIO
import json
from openai import OpenAI
import qrcode
from django.core.files.base import ContentFile
from decimal import Decimal
from django.db.models import Count, Sum, F, Value
from django.db.models.functions import Coalesce


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

def marketplace_view(request):
    return render(request, 'pages/marketplace.html')

def all_events_view(request):
    # Public listing of all events (not filtered by planner)
    events = Event.objects.all().order_by('-date')
    return render(request, 'events/all_events.html', {'events': events})


@login_required
def my_events_view(request):
    """Show only events created by the logged-in planner."""
    events = Event.objects.filter(planner=request.user).annotate(
        attendee_count=Count('attendees')
    ).order_by('-date')
    return render(request, 'events/my_events_dashboard.html', {'events': events})


@login_required
def exhibitors_overview(request):
    """Overview page listing the planner's events with exhibitor management links."""
    events = Event.objects.filter(planner=request.user).prefetch_related('exhibitor_spaces').order_by('-date')
    return render(request, 'events/exhibitors_overview.html', {'events': events})


def _ensure_event_join_url_and_qr(event, request=None):
    """Ensure the event has a join_url and qr_code generated."""
    updated = False
    if not event.join_url:
        # Default to public event detail page
        path = reverse('event_detail', args=[event.slug])
        base = request.build_absolute_uri('/') if request else ''
        event.join_url = base.rstrip('/') + path
        updated = True

    if not event.qr_code:
        qr = qrcode.make(event.join_url)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        event.qr_code.save(f"{event.slug}_qr.png", ContentFile(buffer.getvalue()), save=False)
        updated = True

    if updated:
        event.save()


@login_required
def upload_invitees(request, event_id):
    """Upload a CSV of invitees (name,email) for an event and create Attendee records."""
    event = get_object_or_404(Event, id=event_id, planner=request.user)

    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            wrapped = TextIOWrapper(file.file, encoding='utf-8')
            reader = csv.DictReader(wrapped)
            count = 0
            for row in reader:
                name = row.get('name') or row.get('Name') or ''
                email = row.get('email') or row.get('Email') or ''
                if not email:
                    continue
                Attendee.objects.get_or_create(
                    event=event,
                    email=email,
                    defaults={'name': name or email},
                )
                count += 1
            messages.success(request, f"Uploaded {count} invitees for this event.")
        except Exception as e:
            messages.error(request, f"Could not process file: {e}")

        return redirect('my-events')

    return render(request, 'events/upload_invitees.html', {'event': event})

def restaurants_view(request):
    return render(request, 'pages/restaurants.html')

def flightsView(request):
    return render(request, 'pages/flights.html')

def hotelsView(request):
    return render(request, 'pages/hotels.html')

def cruisesView(request):
    return render(request, 'pages/cruises.html')

def event_detail(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)

    if request.method == 'POST':
        registration_type = request.POST.get('registration_type')
        
        if registration_type == 'visitor':
            # Handle visitor registration
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            ticket_type = request.POST.get('ticket_type', 'regular')
            payment_method = request.POST.get('payment_method', 'full')
            payment_gateway = request.POST.get('payment_gateway', 'vodacom')
            
            if name and email:
                Attendee.objects.create(
                    event=event,
                    name=name,
                    email=email,
                    phone_number=phone_number or '',
                    ticket_type=ticket_type,
                )
                
                # Display payment gateway info
                if payment_gateway == 'vodacom':
                    messages.success(request, f'Registration successful! Please complete payment via Vodacom M-Pesa (*150*00#). You will receive payment instructions via SMS to {phone_number}.')
                else:
                    messages.success(request, 'Registration successful! You will be redirected to the payment page shortly.')
                return redirect('event_detail', event_slug=event.slug)
        
        elif registration_type == 'exhibitor':
            # Handle exhibitor registration
            space_id = request.POST.get('space_id')
            business_name = request.POST.get('business_name')
            exhibitor_name = request.POST.get('exhibitor_name')
            phone_number = request.POST.get('phone_number')
            
            if space_id and business_name and exhibitor_name and phone_number:
                space = get_object_or_404(ExhibitorSpace, id=space_id, event=event)
                
                # Check availability
                current_count = space.bookings.exclude(status='cancelled').count()
                if current_count >= space.total_slots:
                    messages.error(request, 'No slots available for this exhibitor space.')
                else:
                    ExhibitorBooking.objects.create(
                        space=space,
                        exhibitor_name=exhibitor_name,
                        business_name=business_name,
                        phone_number=phone_number,
                    )
                    messages.success(request, 'Exhibitor booking submitted successfully! The event planner will review your request.')
                    return redirect('event_detail', event_slug=event.slug)

    exhibitor_spaces = []
    if event.has_exhibitors:
        spaces = list(event.exhibitor_spaces.all())
        for s in spaces:
            used = s.bookings.exclude(status='cancelled').count()
            s.available_slots = max(s.total_slots - used, 0)
        exhibitor_spaces = spaces

    return render(request, 'events/event_detail.html', {
        'event': event,
        'exhibitor_spaces': exhibitor_spaces,
    })


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


class ExhibitorSpaceListView(APIView):
    def get(self, request, event_slug):
        event = get_object_or_404(Event, slug=event_slug)
        if not event.has_exhibitors:
            return Response([], status=status.HTTP_200_OK)
        spaces = event.exhibitor_spaces.all()
        serializer = ExhibitorSpaceSerializer(spaces, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExhibitorBookingCreateView(APIView):
    def post(self, request, space_id):
        space = get_object_or_404(ExhibitorSpace, id=space_id, event__has_exhibitors=True)

        current_count = space.bookings.exclude(status='cancelled').count()
        if current_count >= space.total_slots:
            return Response({"detail": "No slots available for this space."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ExhibitorBookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(space=space)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

def _generate_event_agenda_with_ai(event, user_prompt=None):
    """Call OpenAI to generate a list of session dicts for the given event.

    user_prompt: optional extra instructions from the planner (e.g. desired tone,
    number of sessions, special constraints).
    """
    print("[AI] Generating agenda for event:", event.id, event.title)  # debug
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        print("[AI] OPENAI_API_KEY is not set; skipping agenda generation")  # debug
        return []

    client = OpenAI(api_key=api_key)

    extra_instructions = user_prompt or "Create a clear, realistic agenda with logical flow."

    prompt = f"""
    You are an expert event planner.
    Create a detailed agenda and timetable for this event.

    Event details:
    Title: {event.title}
    Category: {event.category}
    Date: {event.date} at {event.time}
    Duration (minutes): {event.duration or 'unknown'}
    City: {event.city or ''}, Country: {event.country or ''}
    Venue: {event.venue or ''}
    Description: {event.description}

    Planner instructions:
    {extra_instructions}

    IMPORTANT:
    - Return ONLY raw JSON. Do NOT wrap it in ``` or ```json code fences.
    - Do NOT include any explanation text.

    Expected JSON structure:
    {{"sessions": [
      {{
        "title": "Session title",
        "start_time": "YYYY-MM-DDTHH:MM",
        "end_time": "YYYY-MM-DDTHH:MM",
        "location": "Room or area",
        "speaker": "Speaker name (or empty string)",
        "description": "Short description"
      }},
      ...
    ]}}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs only JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )

    content = response.choices[0].message.content
    print("[AI] Raw response (truncated):", content[:400])  # debug

    # Some models still wrap JSON in ```json fences; strip them if present
    cleaned = content.strip()
    if cleaned.startswith("```"):
        # Remove first ```... line
        parts = cleaned.split("\n", 1)
        if len(parts) == 2:
            cleaned = parts[1]
        # Remove trailing ```
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        print("[AI] JSON decode failed; returning no sessions")  # debug
        return []

    sessions = data.get("sessions", [])
    print(f"[AI] Parsed {len(sessions)} sessions from response")  # debug
    return sessions


@login_required
def create_event(request):
    if request.method == 'POST':
        print("[EVENT] Create event POST:", request.POST)  # debug
        title = request.POST.get('title')
        category = request.POST.get('category') or 'festival'
        date = request.POST.get('date')
        time_value = request.POST.get('time')
        location = request.POST.get('location')
        ticket_price = request.POST.get('ticket_price') or None
        capacity = request.POST.get('capacity') or None
        description = request.POST.get('description') or ''
        image = request.FILES.get('image')
        has_exhibitors = bool(request.POST.get('has_exhibitors'))

        # Optional initial exhibitor space details
        exhibitor_space_name = request.POST.get('exhibitor_space_name')
        exhibitor_space_price = request.POST.get('exhibitor_space_price')
        exhibitor_space_slots = request.POST.get('exhibitor_space_slots') or 1
        exhibitor_space_description = request.POST.get('exhibitor_space_description') or ''

        # Validate required fields
        if not title or not date or not time_value or not location:
            messages.error(request, 'Title, date, time and location are required!')
            return render(request, 'events/eventcreate.html')

        # Create Event (using venue and city for the location string)
        event = Event.objects.create(
            planner=request.user,
            title=title,
            description=description,
            category=category,
            date=date,
            time=time_value,
            venue=location,
            city=location,
            ticket_price=ticket_price or None,
            capacity=capacity or None,
            image=image,
            has_exhibitors=has_exhibitors,
        )

        # If the planner enabled exhibitors and provided an initial space, create it now
        if has_exhibitors and exhibitor_space_name and exhibitor_space_price:
            ExhibitorSpace.objects.create(
                event=event,
                name=exhibitor_space_name,
                price=exhibitor_space_price,
                total_slots=exhibitor_space_slots,
                description=exhibitor_space_description,
            )

        # Ensure event has a join URL and QR code generated
        _ensure_event_join_url_and_qr(event, request)

        # Automatically generate an initial agenda with the AI assistant
        sessions = _generate_event_agenda_with_ai(event)
        print(f"[EVENT] AI returned {len(sessions)} sessions for event {event.id}")  # debug
        for index, s in enumerate(sessions):
            EventSession.objects.create(
                event=event,
                title=s.get('title', 'Session'),
                start_time=s.get('start_time', event.date),
                end_time=s.get('end_time', event.date),
                location=s.get('location', location),
                speaker=s.get('speaker', ''),
                description=s.get('description', ''),
                order=index,
            )

        messages.success(request, 'Event created successfully! Now match with service providers.')
        print(f"[EVENT] Created {len(sessions)} EventSession rows for event {event.id}")  # debug
        return redirect('event-match-services', event_id=event.id)

    # Handle GET request to display form
    return render(request, 'events/eventcreate.html')


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        event.title = request.POST.get('title')
        event.date = request.POST.get('date')
        # Use venue/city fields instead of non-existent `location`
        location = request.POST.get('location')
        if location:
            event.venue = location
            event.city = location

        event.has_exhibitors = bool(request.POST.get('has_exhibitors'))

        event.save()

        messages.success(request, 'Event updated successfully!')
        return redirect('my-events')

    return render(request, 'events/edit_event.html', {'event': event})


@login_required
def edit_event_agenda(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    sessions = list(event.sessions.order_by('order', 'start_time'))

    if request.method == 'POST':
        action = request.POST.get('action') or 'save'

        if action == 'generate_ai':
            ai_prompt = request.POST.get('ai_prompt') or ''
            new_sessions = _generate_event_agenda_with_ai(event, user_prompt=ai_prompt)
            print(f"[EVENT] AI returned {len(new_sessions)} sessions for event {event.id}")  # debug

            # Replace existing sessions with the AI-generated ones
            event.sessions.all().delete()
            for index, s in enumerate(new_sessions):
                EventSession.objects.create(
                    event=event,
                    title=s.get('title', 'Session'),
                    start_time=s.get('start_time', event.date),
                    end_time=s.get('end_time', event.date),
                    location=s.get('location', event.venue or ''),
                    speaker=s.get('speaker', ''),
                    description=s.get('description', ''),
                    order=index,
                )

            messages.success(request, 'Agenda assistant generated a new timetable for you.')
            return redirect('edit-event-agenda', event_id=event.id)

        # Default: save manual edits
        for session in sessions:
            prefix = f"session-{session.id}-"
            title = request.POST.get(prefix + 'title')
            start_time = request.POST.get(prefix + 'start_time')
            end_time = request.POST.get(prefix + 'end_time')
            location = request.POST.get(prefix + 'location')
            speaker = request.POST.get(prefix + 'speaker')
            description = request.POST.get(prefix + 'description')

            if title:
                session.title = title
            if start_time:
                session.start_time = start_time
            if end_time:
                session.end_time = end_time
            session.location = location
            session.speaker = speaker
            session.description = description
            session.save()

        messages.success(request, 'Agenda updated successfully!')
        return redirect('event-dashboard')

    context = {
        'event': event,
        'sessions': sessions,
    }
    return render(request, 'events/event_agenda_edit.html', context)

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
    # Fetch planner's events with attendee count prefetched (avoids N+1)
    events = Event.objects.filter(planner=request.user).annotate(
        attendee_count=Count('attendees')
    ).order_by('-date')

    total_events = events.count()
    total_attendees = Attendee.objects.filter(event__planner=request.user).count()
    cancelled_events = events.filter(status='cancelled').count()

    # Calculate revenue in a single query instead of loop
    total_revenue = events.filter(ticket_price__isnull=False).aggregate(
        revenue=Coalesce(Sum(F('ticket_price') * F('attendee_count')), Value(Decimal('0')))
    )['revenue']

    context = {
        'events': events,
        'total_events': total_events,
        'total_attendees': total_attendees,
        'cancelled_events': cancelled_events,
        'total_revenue': total_revenue,
    }
    return render(request, 'events/eventdashboard.html', context)


@login_required
def attendee_list(request):
    attendees = Attendee.objects.all()
    return render(request, 'events/attendee_list.html', {'attendees': attendees})

@login_required
def profile_view(request):
    """Display and handle profile updates including image upload."""
    user = request.user
    
    if request.method == 'POST':
        # Handle profile update
        user.name = request.POST.get('name', user.name)
        user.phone = request.POST.get('phone', user.phone) or None
        user.bio = request.POST.get('bio', user.bio) or None
        
        # Handle profile image upload
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        
        # Handle image removal
        if request.POST.get('remove_image') == 'true':
            if user.profile_image:
                user.profile_image.delete(save=False)
                user.profile_image = None
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'events/profile.html', {'profile_user': user})

@login_required
def edit_profile_view(request):
    return redirect('profile')

@login_required
def change_password_view(request):
    """Handle password change."""
    if request.method == 'POST':
        from django.contrib.auth import update_session_auth_hash
        
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    
    return render(request, 'events/change_password.html')

@login_required
def settings_view(request):
    return render(request, 'users/settings.html')


@login_required
def manage_exhibitor_spaces(request, event_id):
    event = get_object_or_404(Event, id=event_id, planner=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        total_slots = request.POST.get('total_slots') or 1
        description = request.POST.get('description') or ''

        if not name or not price:
            messages.error(request, 'Name and price are required for an exhibitor space.')
        else:
            ExhibitorSpace.objects.create(
                event=event,
                name=name,
                price=price,
                total_slots=total_slots,
                description=description,
            )
            event.has_exhibitors = True
            event.save(update_fields=['has_exhibitors'])
            messages.success(request, 'Exhibitor space added successfully.')

        return redirect('manage-exhibitor-spaces', event_id=event.id)

    spaces = list(event.exhibitor_spaces.all())
    for s in spaces:
        used = s.bookings.exclude(status='cancelled').count()
        s.used_slots = used
        s.remaining_slots = max(s.total_slots - used, 0)

    return render(request, 'events/manage_exhibitors.html', {
        'event': event,
        'spaces': spaces,
    })


@login_required
def manage_exhibitor_bookings(request, event_id):
    event = get_object_or_404(Event, id=event_id, planner=request.user)

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        paid_amount = request.POST.get('paid_amount')

        booking = get_object_or_404(ExhibitorBooking, id=booking_id, space__event=event)

        if action == 'confirm':
            # Overbooking protection when confirming
            used = booking.space.bookings.exclude(status='cancelled').exclude(id=booking.id).count()
            if used >= booking.space.total_slots:
                messages.error(request, 'No remaining slots for this exhibitor space.')
            else:
                booking.status = 'confirmed'
        elif action == 'cancel':
            booking.status = 'cancelled'

        if paid_amount is not None and paid_amount != '':
            booking.paid_amount = paid_amount

        booking.save()
        messages.success(request, 'Booking updated successfully.')
        return redirect('manage-exhibitor-bookings', event_id=event.id)

    bookings = ExhibitorBooking.objects.filter(space__event=event).select_related('space').order_by('-created_at')

    return render(request, 'events/manage_exhibitor_bookings.html', {
        'event': event,
        'bookings': bookings,
    })


def exhibitor_book_space(request, space_id):
    space = get_object_or_404(ExhibitorSpace, id=space_id, event__has_exhibitors=True)
    event = space.event

    if request.method == 'POST':
        exhibitor_name = request.POST.get('exhibitor_name')
        business_name = request.POST.get('business_name')
        phone_number = request.POST.get('phone_number')

        if not exhibitor_name or not business_name or not phone_number:
            messages.error(request, 'All fields are required to book an exhibitor space.')
        else:
            current_count = space.bookings.exclude(status='cancelled').count()
            if current_count >= space.total_slots:
                messages.error(request, 'No slots available for this space.')
            else:
                ExhibitorBooking.objects.create(
                    space=space,
                    exhibitor_name=exhibitor_name,
                    business_name=business_name,
                    phone_number=phone_number,
                )
                messages.success(request, 'Your exhibitor booking has been submitted.')
                return redirect('event_detail', event_slug=event.slug)

    used = space.bookings.exclude(status='cancelled').count()
    available_slots = max(space.total_slots - used, 0)

    return render(request, 'events/exhibitor_book_space.html', {
        'event': event,
        'space': space,
        'available_slots': available_slots,
    })


@login_required
def event_match_services(request, event_id):
    """Match service providers with an event."""
    from django.http import JsonResponse
    
    event = get_object_or_404(Event, id=event_id, planner=request.user)
    
    # Get all service types
    service_types = ServiceProvider.SERVICE_TYPES
    
    # Get selected service type from query params
    selected_type = request.GET.get('service', '')
    is_ajax = request.GET.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Handle POST request to add a match
    if request.method == 'POST':
        provider_id = request.POST.get('provider_id')
        action = request.POST.get('action')
        
        if action == 'match' and provider_id:
            provider = get_object_or_404(ServiceProvider, id=provider_id)
            match, created = ServiceMatch.objects.get_or_create(
                event=event,
                provider=provider,
                defaults={'status': 'pending'}
            )
            if created:
                messages.success(request, f'{provider.name} has been added to your event services.')
            else:
                messages.info(request, f'{provider.name} is already in your services.')
            
            return redirect('event-match-services', event_id=event.id)
    
    # If AJAX request, return JSON
    if is_ajax and selected_type:
        providers = ServiceProvider.objects.filter(
            service_type=selected_type,
            is_available=True
        ).order_by('-rating', '-reviews_count')[:3]
        
        return JsonResponse({
            'providers': [
                {
                    'id': p.id,
                    'name': p.name,
                    'service_type': p.service_type,
                    'description': p.description[:100] if p.description else '',
                    'price_range_min': float(p.price_range_min) if p.price_range_min else None,
                    'price_range_max': float(p.price_range_max) if p.price_range_max else None,
                    'rating': float(p.rating),
                    'reviews_count': p.reviews_count,
                }
                for p in providers
            ]
        })
    
    # Get existing matches for this event
    matched_services = ServiceMatch.objects.filter(event=event).select_related('provider')
    
    context = {
        'event': event,
        'service_types': service_types,
        'matched_services': matched_services,
    }
    return render(request, 'events/event_match.html', context)


# =============================================================================
# TOUR ITINERARY GENERATION WITH AI
# =============================================================================

def _get_pricing_context(tour_request):
    """Gather all pricing data relevant to the tour request for AI context."""
    from datetime import datetime
    
    # Determine if high or low season
    start_month_day = tour_request.start_date.strftime('%m-%d')
    
    # Get destinations
    preferred_dests = list(tour_request.preferred_destinations.all())
    if not preferred_dests:
        preferred_dests = list(Destination.objects.filter(is_active=True)[:5])
    
    # Get hotels matching tour type
    tier_map = {
        'budget': ['budget'],
        'mid_range': ['mid_range', 'budget'],
        'semi_luxury': ['semi_luxury', 'mid_range'],
        'luxury': ['luxury', 'semi_luxury'],
    }
    tiers = tier_map.get(tour_request.tour_type, ['mid_range'])
    
    hotels_data = []
    for dest in preferred_dests:
        hotels = HotelRate.objects.filter(
            destination=dest,
            tier__in=tiers,
            is_active=True
        ).order_by('tier', 'rate_high_season')[:3]
        
        for hotel in hotels:
            # Determine season rate
            is_high_season = '06-01' <= start_month_day <= '10-31'
            rate = hotel.rate_high_season if is_high_season else hotel.rate_low_season
            
            hotels_data.append({
                'name': hotel.name,
                'destination': dest.name,
                'tier': hotel.get_tier_display(),
                'meal_plan': hotel.get_meal_plan_display(),
                'rate_per_night': float(rate),
            })
    
    # Get transport options
    num_travelers = tour_request.total_travelers
    vehicles = TransportRate.objects.filter(
        is_active=True,
        max_passengers__gte=num_travelers
    ).order_by('rate_per_day')[:3]
    
    transport_data = [
        {
            'type': v.get_vehicle_type_display(),
            'rate_per_day': float(v.rate_per_day),
            'max_passengers': v.max_passengers,
        }
        for v in vehicles
    ]
    
    # Get activities
    activities_data = []
    for dest in preferred_dests:
        activities = ActivityRate.objects.filter(
            destination=dest,
            is_active=True
        )[:5]
        
        for act in activities:
            activities_data.append({
                'name': act.name,
                'destination': dest.name,
                'type': act.get_activity_type_display(),
                'rate_adult': float(act.rate_adult),
                'rate_child': float(act.rate_child),
                'duration': act.duration,
            })
    
    # Get park fees (general activities without specific destination)
    park_fees = ActivityRate.objects.filter(
        activity_type='park_fee',
        is_active=True
    )
    
    for fee in park_fees:
        activities_data.append({
            'name': fee.name,
            'destination': fee.destination.name if fee.destination else 'General',
            'type': 'Park Entry Fee',
            'rate_adult': float(fee.rate_adult),
            'rate_child': float(fee.rate_child),
            'duration': 'Per day',
        })
    
    # Destination info
    destinations_info = [
        {
            'name': d.name,
            'region': d.region,
            'highlights': d.highlights,
            'best_time': d.best_time_to_visit,
            'recommended_days': d.avg_time_needed,
        }
        for d in preferred_dests
    ]
    
    # Get flight options
    flights_data = []
    flights = FlightRate.objects.filter(is_active=True)
    for flight in flights:
        flights_data.append({
            'airline': flight.get_airline_display(),
            'origin': flight.origin,
            'origin_code': flight.origin_code,
            'destination': flight.destination,
            'destination_code': flight.destination_code,
            'price_economy': float(flight.price_economy),
            'price_business': float(flight.price_business) if flight.price_business else None,
            'duration': flight.flight_duration,
            'baggage': flight.baggage_allowance,
            'frequency': flight.frequency,
        })
    
    return {
        'hotels': hotels_data,
        'transport': transport_data,
        'activities': activities_data,
        'destinations': destinations_info,
        'flights': flights_data,
    }


def _generate_tour_itinerary_with_ai(tour_request, markup_percentage=15):
    """Generate a detailed tour itinerary using OpenAI with real pricing data.
    
    Args:
        tour_request: TourRequest model instance
        markup_percentage: Operator profit margin (default 15%)
    """
    import openai
    import json
    from datetime import datetime
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🧠 AI ITINERARY GENERATION - THINKING PROCESS
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 80)
    print("🧠 AI ITINERARY GENERATOR - THINKING PROCESS")
    print("═" * 80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Request ID: {tour_request.pk}")
    print(f"👤 Client: {tour_request.client_name}")
    
    # Step 1: Analyze client requirements
    print("\n" + "─" * 40)
    print("📊 STEP 1: ANALYZING CLIENT REQUIREMENTS")
    print("─" * 40)
    print(f"   • Tour Type: {tour_request.get_tour_type_display()}")
    print(f"   • Group Type: {tour_request.get_group_type_display()}")
    print(f"   • Travelers: {tour_request.num_adults} adults + {tour_request.num_children} children")
    print(f"   • Duration: {tour_request.duration_days} days")
    print(f"   • Budget: ${tour_request.budget_per_person}/person")
    print(f"   • Total Budget Available: ${float(tour_request.budget_per_person) * tour_request.total_travelers}")
    print(f"   • Dates: {tour_request.start_date} to {tour_request.end_date}")
    if tour_request.special_requests:
        print(f"   • Special Requests: {tour_request.special_requests}")
    
    # Step 2: Gather pricing data
    print("\n" + "─" * 40)
    print("💰 STEP 2: GATHERING PRICING DATA")
    print("─" * 40)
    
    pricing_context = _get_pricing_context(tour_request)
    
    print(f"   ✓ Found {len(pricing_context['destinations'])} destinations")
    print(f"   ✓ Found {len(pricing_context['hotels'])} hotels matching criteria")
    print(f"   ✓ Found {len(pricing_context['transport'])} ground transport options")
    print(f"   ✓ Found {len(pricing_context.get('flights', []))} flight routes")
    print(f"   ✓ Found {len(pricing_context['activities'])} activities/park fees")
    
    if pricing_context['hotels']:
        hotel_prices = [h.get('rate_per_night', 0) for h in pricing_context['hotels']]
        print(f"   📍 Hotel price range: ${min(hotel_prices)} - ${max(hotel_prices)}/night")
        print(f"   📍 Hotels available: {', '.join([h['name'] for h in pricing_context['hotels'][:5]])}")
    
    if pricing_context.get('flights'):
        flight_prices = [fl.get('price_economy', 0) for fl in pricing_context['flights']]
        print(f"   ✈️  Flight price range: ${min(flight_prices)} - ${max(flight_prices)}/person")
        routes = [fl['origin_code'] + '→' + fl['destination_code'] for fl in pricing_context['flights'][:5]]
        print(f"   ✈️  Routes: {', '.join(routes)}")
    
    if pricing_context['destinations']:
        print(f"   📍 Destinations: {', '.join([d['name'] for d in pricing_context['destinations']])}")
    
    # Step 3: Calculate budget allocation
    print("\n" + "─" * 40)
    print("🧮 STEP 3: CALCULATING BUDGET ALLOCATION")
    print("─" * 40)
    duration = tour_request.duration_days
    total_budget = float(tour_request.budget_per_person)
    
    # Typical safari budget breakdown
    accommodation_pct = 0.45  # 45% for accommodation
    activities_pct = 0.25    # 25% for activities/park fees
    transport_pct = 0.20     # 20% for transport
    meals_misc_pct = 0.10    # 10% for extras
    
    print(f"   💡 AI Budget Strategy:")
    print(f"      • Accommodation (~45%): ${total_budget * accommodation_pct:.0f}/person")
    print(f"      • Activities/Parks (~25%): ${total_budget * activities_pct:.0f}/person")
    print(f"      • Transport (~20%): ${total_budget * transport_pct:.0f}/person")
    print(f"      • Meals/Misc (~10%): ${total_budget * meals_misc_pct:.0f}/person")
    print(f"   💡 Daily accommodation budget: ~${(total_budget * accommodation_pct) / duration:.0f}/night")
    
    # Step 4: Send to AI
    print("\n" + "─" * 40)
    print("🤖 STEP 4: SENDING TO AI FOR ITINERARY CREATION")
    print("─" * 40)
    print("   📤 Sending request to OpenAI GPT-4o-mini...")
    print("   ⏳ This may take 10-20 seconds...")
    
    system_prompt = """You are an expert Tanzania safari and tour planner. Generate detailed, realistic tour itineraries 
using ONLY the provided pricing data. You must use actual hotel names, activity prices, and transport costs from the data given.

IMPORTANT: Think step by step:
1. First, analyze the budget constraints
2. Select appropriate accommodations within budget
3. Plan logical route between destinations
4. Add activities and park fees
5. Calculate all costs accurately

Return your response as a JSON object with this structure:
{
    "summary": "Brief overview of the tour",
    "reasoning": "Explain why you chose this itinerary (budget considerations, route logic, etc.)",
    "days": [
        {
            "day": 1,
            "title": "Day title",
            "destination": "Location name",
            "activities": [
                {"name": "Activity name", "time": "08:00", "duration": "2 hours", "cost_per_person": 50}
            ],
            "accommodation": {"name": "Hotel name", "meal_plan": "Full Board", "cost_per_person": 150},
            "transport": {"description": "Drive from A to B", "distance_km": 100, "cost": 50},
            "meals_included": ["Breakfast", "Lunch", "Dinner"],
            "tips": "Day-specific tips"
        }
    ],
    "cost_breakdown": {
        "accommodation_total": 0,
        "activities_total": 0,
        "transport_total": 0,
        "park_fees_total": 0,
        "subtotal_per_person": 0,
        "subtotal_all_travelers": 0
    },
    "what_to_pack": ["item1", "item2"],
    "best_time_tips": "Seasonal advice"
}"""

    # Build location context
    pickup = tour_request.pickup_location or tour_request.arrival_location or 'Not specified'
    dropoff = tour_request.departure_location or tour_request.arrival_location or pickup
    
    user_prompt = f"""Create a {duration}-day tour itinerary for:

CLIENT REQUIREMENTS:
- Tour Type: {tour_request.get_tour_type_display()}
- Group Type: {tour_request.get_group_type_display()}
- Number of Adults: {tour_request.num_adults}
- Number of Children: {tour_request.num_children}
- Budget per Person: ${tour_request.budget_per_person} USD
- Start Date: {tour_request.start_date}
- End Date: {tour_request.end_date}
- Preferred Daily Start Time: {tour_request.get_preferred_start_time_display()}

GUEST LOCATION & TRAVEL:
- Arrival Method: {tour_request.get_arrival_method_display()}
- Arrival Location: {tour_request.arrival_location or 'Not specified'}
- Current Location: {tour_request.current_location or 'N/A - arriving from abroad'}
- Pickup Location: {pickup}
- Departure Location: {dropoff}

SPECIAL REQUIREMENTS:
- Special Requests: {tour_request.special_requests or 'None specified'}
- Dietary Requirements: {tour_request.dietary_requirements or 'None'}
- Mobility Requirements: {tour_request.mobility_requirements or 'None'}

AVAILABLE PRICING DATA (USE THESE EXACT PRICES):

DESTINATIONS:
{json.dumps(pricing_context['destinations'], indent=2)}

HOTELS (use these exact names and prices):
{json.dumps(pricing_context['hotels'], indent=2)}

TRANSPORT OPTIONS (Ground):
{json.dumps(pricing_context['transport'], indent=2)}

FLIGHT OPTIONS (Domestic/Regional):
{json.dumps(pricing_context.get('flights', []), indent=2)}

ACTIVITIES & PARK FEES:
{json.dumps(pricing_context['activities'], indent=2)}

IMPORTANT:
1. Stay within the budget of ${tour_request.budget_per_person} per person
2. Use ONLY hotels and prices from the provided data
3. Include all park fees in the cost calculation
4. Calculate accurate totals based on {tour_request.num_adults} adults and {tour_request.num_children} children
5. Make the itinerary realistic with proper travel times between destinations
6. If budget is tight, suggest {tour_request.get_tour_type_display()} options only
7. Include your reasoning for the choices made
8. If client requests flights, use the FLIGHT OPTIONS provided and include exact flight prices
9. Always specify which hotel the guest will stay at by name and price"""

    try:
        ai_start = datetime.now()
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=4000,
        )
        ai_end = datetime.now()
        ai_duration = (ai_end - ai_start).total_seconds()
        
        print(f"   ✅ AI Response received in {ai_duration:.1f} seconds")
        print(f"   📊 Tokens used: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
        
        content = response.choices[0].message.content
        itinerary_data = json.loads(content)
        
        # Step 5: Show AI reasoning
        print("\n" + "─" * 40)
        print("💭 STEP 5: AI REASONING")
        print("─" * 40)
        if itinerary_data.get('reasoning'):
            print(f"   {itinerary_data['reasoning']}")
        
        # Step 6: Apply operator markup
        print("\n" + "─" * 40)
        print(f"💼 STEP 6: APPLYING OPERATOR MARKUP ({markup_percentage}%)")
        print("─" * 40)
        
        if 'cost_breakdown' in itinerary_data:
            cb = itinerary_data['cost_breakdown']
            
            # Get subtotals (base costs)
            subtotal_pp = cb.get('subtotal_per_person') or cb.get('total_per_person', 0)
            subtotal_all = cb.get('subtotal_all_travelers') or cb.get('total_all_travelers', 0)
            
            # Calculate markup
            markup_pp = subtotal_pp * (markup_percentage / 100)
            markup_all = subtotal_all * (markup_percentage / 100)
            
            # Calculate final totals with markup
            total_pp = subtotal_pp + markup_pp
            total_all = subtotal_all + markup_all
            
            # Update cost breakdown with markup info
            cb['subtotal_per_person'] = round(subtotal_pp, 2)
            cb['subtotal_all_travelers'] = round(subtotal_all, 2)
            cb['operator_markup_percentage'] = markup_percentage
            cb['operator_markup_per_person'] = round(markup_pp, 2)
            cb['operator_markup_total'] = round(markup_all, 2)
            cb['total_per_person'] = round(total_pp, 2)
            cb['total_all_travelers'] = round(total_all, 2)
            
            print(f"   📋 Base Cost (per person): ${subtotal_pp:.2f}")
            print(f"   ➕ Operator Markup ({markup_percentage}%): ${markup_pp:.2f}")
            print(f"   💰 Final Price (per person): ${total_pp:.2f}")
            print(f"   ")
            print(f"   📋 Base Cost (all travelers): ${subtotal_all:.2f}")
            print(f"   ➕ Operator Markup ({markup_percentage}%): ${markup_all:.2f}")
            print(f"   💰 Final Price (all travelers): ${total_all:.2f}")
            print(f"   ")
            print(f"   🎯 OPERATOR PROFIT: ${markup_all:.2f}")
        
        # Step 7: Summary
        print("\n" + "─" * 40)
        print("✅ STEP 7: GENERATION COMPLETE")
        print("─" * 40)
        if itinerary_data.get('days'):
            print(f"   📅 Generated {len(itinerary_data['days'])} day itinerary")
            for day in itinerary_data['days']:
                activities = len(day.get('activities', []))
                print(f"      Day {day.get('day')}: {day.get('title')} ({activities} activities)")
        
        print("\n" + "═" * 80)
        print("🎉 AI ITINERARY GENERATION COMPLETE!")
        print("═" * 80 + "\n")
        
        return itinerary_data
        
    except Exception as e:
        print(f"\n   ❌ AI generation error: {e}")
        print("═" * 80 + "\n")
        return None


@login_required
def tour_request_list(request):
    """List all tour requests for the operator."""
    requests = TourRequest.objects.filter(operator=request.user).order_by('-created_at')
    
    # Calculate stats for dashboard cards
    total_count = requests.count()
    pending_count = requests.filter(status='pending').count()
    confirmed_count = requests.filter(status='confirmed').count()
    itinerary_count = requests.filter(status='itinerary_generated').count()
    
    context = {
        'tour_requests': requests,
        'total_count': total_count,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'itinerary_count': itinerary_count,
    }
    return render(request, 'tours/tour_request_list.html', context)


@login_required
def tour_request_create(request):
    """Create a new tour request with client requirements."""
    destinations = Destination.objects.filter(is_active=True).order_by('region', 'name')
    
    if request.method == 'POST':
        # Create the tour request
        tour_request = TourRequest.objects.create(
            operator=request.user,
            client_name=request.POST.get('client_name'),
            client_email=request.POST.get('client_email'),
            client_phone=request.POST.get('client_phone', ''),
            tour_type=request.POST.get('tour_type'),
            group_type=request.POST.get('group_type'),
            num_adults=int(request.POST.get('num_adults', 2)),
            num_children=int(request.POST.get('num_children', 0)),
            budget_per_person=request.POST.get('budget_per_person'),
            budget_flexible=request.POST.get('budget_flexible') == 'on',
            markup_percentage=float(request.POST.get('markup_percentage', 15)),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            dates_flexible=request.POST.get('dates_flexible') == 'on',
            preferred_start_time=request.POST.get('preferred_start_time', 'morning'),
            arrival_method=request.POST.get('arrival_method', 'flight_international'),
            arrival_location=request.POST.get('arrival_location', ''),
            current_location=request.POST.get('current_location', ''),
            pickup_location=request.POST.get('pickup_location', ''),
            departure_location=request.POST.get('departure_location', ''),
            special_requests=request.POST.get('special_requests', ''),
            dietary_requirements=request.POST.get('dietary_requirements', ''),
            mobility_requirements=request.POST.get('mobility_requirements', ''),
            status='draft',
        )
        
        # Add preferred destinations
        dest_ids = request.POST.getlist('preferred_destinations')
        if dest_ids:
            tour_request.preferred_destinations.set(dest_ids)
        
        messages.success(request, 'Tour request created! You can now generate an AI itinerary.')
        return redirect('tour_request_detail', pk=tour_request.pk)
    
    context = {
        'destinations': destinations,
        'tour_types': TourRequest.TOUR_TYPES,
        'group_types': TourRequest.GROUP_TYPES,
    }
    return render(request, 'tours/tour_request_create.html', context)


@login_required
def tour_request_detail(request, pk):
    """View and manage a tour request, generate AI itinerary."""
    import json
    
    tour_request = get_object_or_404(TourRequest, pk=pk, operator=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'generate_itinerary':
            # Generate AI itinerary with operator's markup percentage
            markup = float(tour_request.markup_percentage)
            itinerary_data = _generate_tour_itinerary_with_ai(tour_request, markup_percentage=markup)
            
            if itinerary_data:
                tour_request.generated_itinerary = json.dumps(itinerary_data)
                
                # Extract total cost if available
                if 'cost_breakdown' in itinerary_data:
                    total = itinerary_data['cost_breakdown'].get('total_all_travelers', 0)
                    tour_request.total_estimated_cost = total
                
                tour_request.status = 'itinerary_generated'
                tour_request.save()
                messages.success(request, 'AI itinerary generated successfully!')
            else:
                messages.error(request, 'Failed to generate itinerary. Please try again.')
        
        elif action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(TourRequest.STATUS_CHOICES):
                tour_request.status = new_status
                tour_request.save()
                messages.success(request, f'Status updated to {tour_request.get_status_display()}')
        
        return redirect('tour_request_detail', pk=pk)
    
    # Parse itinerary JSON if exists
    itinerary = None
    if tour_request.generated_itinerary:
        try:
            itinerary = json.loads(tour_request.generated_itinerary)
        except json.JSONDecodeError:
            itinerary = None
    
    context = {
        'tour_request': tour_request,
        'itinerary': itinerary,
        'status_choices': TourRequest.STATUS_CHOICES,
    }
    return render(request, 'tours/tour_request_detail.html', context)


@login_required
def tour_request_pdf(request, pk, pdf_type='client'):
    """Generate and download PDF itinerary.
    
    Args:
        pk: TourRequest primary key
        pdf_type: 'client' for client version, 'operator' for internal version with profit info
    """
    from .pdf_generator import generate_itinerary_pdf, generate_operator_pdf
    
    tour_request = get_object_or_404(TourRequest, pk=pk, operator=request.user)
    
    # Check if itinerary exists
    if not tour_request.generated_itinerary:
        messages.error(request, 'No itinerary generated yet. Please generate an itinerary first.')
        return redirect('tour_request_detail', pk=pk)
    
    try:
        itinerary_data = json.loads(tour_request.generated_itinerary)
    except json.JSONDecodeError:
        messages.error(request, 'Error parsing itinerary data.')
        return redirect('tour_request_detail', pk=pk)
    
    # Generate PDF based on type
    if pdf_type == 'operator':
        pdf_buffer = generate_operator_pdf(tour_request, itinerary_data)
        filename = f"OPERATOR_{tour_request.client_name.replace(' ', '_')}_{tour_request.start_date}.pdf"
    else:
        pdf_buffer = generate_itinerary_pdf(tour_request, itinerary_data)
        filename = f"Itinerary_{tour_request.client_name.replace(' ', '_')}_{tour_request.start_date}.pdf"
    
    # Return PDF response
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def tour_request_edit_itinerary(request, pk):
    """Edit the generated itinerary - allows modifying days, activities, prices."""
    tour_request = get_object_or_404(TourRequest, pk=pk, operator=request.user)
    
    # Check if itinerary exists
    if not tour_request.generated_itinerary:
        messages.error(request, 'No itinerary generated yet. Please generate an itinerary first.')
        return redirect('tour_request_detail', pk=pk)
    
    try:
        itinerary_data = json.loads(tour_request.generated_itinerary)
    except json.JSONDecodeError:
        messages.error(request, 'Error parsing itinerary data.')
        return redirect('tour_request_detail', pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'save_itinerary':
            # Update the itinerary from form data
            days = itinerary_data.get('days', [])
            
            for i, day in enumerate(days):
                day_prefix = f'day_{i}'
                
                # Update day title and description
                day['title'] = request.POST.get(f'{day_prefix}_title', day.get('title', ''))
                day['description'] = request.POST.get(f'{day_prefix}_description', day.get('description', ''))
                
                # Update accommodation
                day['accommodation'] = {
                    'name': request.POST.get(f'{day_prefix}_hotel_name', ''),
                    'type': request.POST.get(f'{day_prefix}_hotel_type', ''),
                    'meal_plan': request.POST.get(f'{day_prefix}_meal_plan', ''),
                    'price_per_night': float(request.POST.get(f'{day_prefix}_hotel_price', 0) or 0),
                }
                
                # Update transport
                day['transport'] = {
                    'type': request.POST.get(f'{day_prefix}_transport_type', ''),
                    'details': request.POST.get(f'{day_prefix}_transport_details', ''),
                    'cost': float(request.POST.get(f'{day_prefix}_transport_cost', 0) or 0),
                }
                
                # Update meals
                day['meals_included'] = request.POST.getlist(f'{day_prefix}_meals')
                
                # Update tips
                day['tips'] = request.POST.get(f'{day_prefix}_tips', '')
                
                # Update activities
                activities = []
                activity_count = int(request.POST.get(f'{day_prefix}_activity_count', 0))
                for j in range(activity_count):
                    act_prefix = f'{day_prefix}_activity_{j}'
                    activity = {
                        'time': request.POST.get(f'{act_prefix}_time', ''),
                        'name': request.POST.get(f'{act_prefix}_name', ''),
                        'description': request.POST.get(f'{act_prefix}_description', ''),
                        'duration': request.POST.get(f'{act_prefix}_duration', ''),
                        'cost': float(request.POST.get(f'{act_prefix}_cost', 0) or 0),
                    }
                    if activity['name']:  # Only add if has a name
                        activities.append(activity)
                
                day['activities'] = activities
            
            # Update cost breakdown
            cost_breakdown = itinerary_data.get('cost_breakdown', {})
            cost_breakdown['accommodation_total'] = float(request.POST.get('accommodation_total', 0) or 0)
            cost_breakdown['activities_total'] = float(request.POST.get('activities_total', 0) or 0)
            cost_breakdown['transport_total'] = float(request.POST.get('transport_total', 0) or 0)
            cost_breakdown['park_fees_total'] = float(request.POST.get('park_fees_total', 0) or 0)
            
            # Recalculate totals
            subtotal = (cost_breakdown['accommodation_total'] + 
                       cost_breakdown['activities_total'] + 
                       cost_breakdown['transport_total'] + 
                       cost_breakdown['park_fees_total'])
            
            markup_pct = float(tour_request.markup_percentage) / 100
            markup_amount = subtotal * markup_pct
            
            cost_breakdown['subtotal_per_person'] = subtotal
            cost_breakdown['markup_percentage'] = float(tour_request.markup_percentage)
            cost_breakdown['markup_amount'] = markup_amount
            cost_breakdown['total_per_person'] = subtotal + markup_amount
            cost_breakdown['subtotal_all_travelers'] = subtotal * tour_request.total_travelers
            cost_breakdown['total_all_travelers'] = (subtotal + markup_amount) * tour_request.total_travelers
            
            itinerary_data['cost_breakdown'] = cost_breakdown
            itinerary_data['days'] = days
            
            # Update summary if provided
            if request.POST.get('summary'):
                itinerary_data['summary'] = request.POST.get('summary')
            
            # Save
            tour_request.generated_itinerary = json.dumps(itinerary_data)
            tour_request.total_estimated_cost = cost_breakdown['total_all_travelers']
            tour_request.save()
            
            messages.success(request, 'Itinerary updated successfully!')
            return redirect('tour_request_detail', pk=pk)
        
        elif action == 'add_day':
            # Add a new day
            new_day_num = len(itinerary_data.get('days', [])) + 1
            new_day = {
                'day': new_day_num,
                'date': '',
                'title': f'Day {new_day_num}',
                'description': '',
                'activities': [],
                'accommodation': {'name': '', 'type': '', 'meal_plan': '', 'price_per_night': 0},
                'transport': {'type': '', 'details': '', 'cost': 0},
                'meals_included': [],
                'tips': ''
            }
            itinerary_data['days'].append(new_day)
            tour_request.generated_itinerary = json.dumps(itinerary_data)
            tour_request.save()
            messages.success(request, f'Day {new_day_num} added!')
            return redirect('tour_request_edit_itinerary', pk=pk)
        
        elif action == 'delete_day':
            day_index = int(request.POST.get('day_index', -1))
            if 0 <= day_index < len(itinerary_data.get('days', [])):
                del itinerary_data['days'][day_index]
                # Renumber days
                for i, day in enumerate(itinerary_data['days']):
                    day['day'] = i + 1
                tour_request.generated_itinerary = json.dumps(itinerary_data)
                tour_request.save()
                messages.success(request, 'Day removed!')
            return redirect('tour_request_edit_itinerary', pk=pk)
    
    context = {
        'tour_request': tour_request,
        'itinerary': itinerary_data,
        'days': itinerary_data.get('days', []),
        'cost_breakdown': itinerary_data.get('cost_breakdown', {}),
    }
    return render(request, 'tours/tour_request_edit_itinerary.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOADED PACKAGES - Upload ready-made packages with PDF and images
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def uploaded_packages_list(request):
    """List all uploaded packages for the current operator."""
    packages = UploadedPackage.objects.filter(operator=request.user)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        packages = packages.filter(status=status_filter)
    
    # Filter by type
    type_filter = request.GET.get('type', '')
    if type_filter:
        packages = packages.filter(package_type=type_filter)
    
    context = {
        'packages': packages,
        'package_types': UploadedPackage.PACKAGE_TYPES,
        'package_statuses': UploadedPackage.PACKAGE_STATUS,
        'current_status': status_filter,
        'current_type': type_filter,
    }
    return render(request, 'tours/uploaded_packages_list.html', context)


@login_required
def upload_package(request):
    """Upload a new package with PDF and images."""
    if request.method == 'POST':
        # Create the package
        package = UploadedPackage(
            operator=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            package_type=request.POST.get('package_type', 'safari'),
            duration_days=int(request.POST.get('duration_days', 1)),
            destinations=request.POST.get('destinations', ''),
            price_per_person=request.POST.get('price_per_person') or None,
            min_group_size=int(request.POST.get('min_group_size', 1)),
            max_group_size=int(request.POST.get('max_group_size', 20)),
            is_public=request.POST.get('is_public') == 'on',
            status=request.POST.get('status', 'draft'),
        )
        
        # Handle file uploads
        if 'pdf_itinerary' in request.FILES:
            package.pdf_itinerary = request.FILES['pdf_itinerary']
        if 'cover_image' in request.FILES:
            package.cover_image = request.FILES['cover_image']
        if 'image_2' in request.FILES:
            package.image_2 = request.FILES['image_2']
        if 'image_3' in request.FILES:
            package.image_3 = request.FILES['image_3']
        if 'image_4' in request.FILES:
            package.image_4 = request.FILES['image_4']
        
        package.save()
        
        # Extract text from PDF for AI training (async would be better for production)
        if package.pdf_itinerary:
            try:
                extracted = extract_pdf_text(package.pdf_itinerary.path)
                if extracted:
                    package.extracted_text = extracted
                    package.is_analyzed = True
                    package.save()
            except Exception as e:
                print(f"PDF extraction error: {e}")
        
        messages.success(request, f'Package "{package.title}" uploaded successfully!')
        return redirect('uploaded_packages_list')
    
    context = {
        'package_types': UploadedPackage.PACKAGE_TYPES,
        'package_statuses': UploadedPackage.PACKAGE_STATUS,
    }
    return render(request, 'tours/upload_package.html', context)


@login_required
def edit_uploaded_package(request, pk):
    """Edit an existing uploaded package."""
    package = get_object_or_404(UploadedPackage, pk=pk, operator=request.user)
    
    if request.method == 'POST':
        # Update fields
        package.title = request.POST.get('title', package.title)
        package.description = request.POST.get('description', package.description)
        package.package_type = request.POST.get('package_type', package.package_type)
        package.duration_days = int(request.POST.get('duration_days', package.duration_days))
        package.destinations = request.POST.get('destinations', package.destinations)
        package.price_per_person = request.POST.get('price_per_person') or None
        package.min_group_size = int(request.POST.get('min_group_size', package.min_group_size))
        package.max_group_size = int(request.POST.get('max_group_size', package.max_group_size))
        package.is_public = request.POST.get('is_public') == 'on'
        package.status = request.POST.get('status', package.status)
        
        # Handle file uploads
        if 'pdf_itinerary' in request.FILES:
            package.pdf_itinerary = request.FILES['pdf_itinerary']
            # Re-extract text
            try:
                extracted = extract_pdf_text(package.pdf_itinerary.path)
                if extracted:
                    package.extracted_text = extracted
                    package.is_analyzed = True
            except Exception as e:
                print(f"PDF extraction error: {e}")
        
        if 'cover_image' in request.FILES:
            package.cover_image = request.FILES['cover_image']
        if 'image_2' in request.FILES:
            package.image_2 = request.FILES['image_2']
        if 'image_3' in request.FILES:
            package.image_3 = request.FILES['image_3']
        if 'image_4' in request.FILES:
            package.image_4 = request.FILES['image_4']
        
        package.save()
        messages.success(request, 'Package updated successfully!')
        return redirect('uploaded_packages_list')
    
    context = {
        'package': package,
        'package_types': UploadedPackage.PACKAGE_TYPES,
        'package_statuses': UploadedPackage.PACKAGE_STATUS,
    }
    return render(request, 'tours/edit_uploaded_package.html', context)


@login_required
def delete_uploaded_package(request, pk):
    """Delete an uploaded package."""
    package = get_object_or_404(UploadedPackage, pk=pk, operator=request.user)
    
    if request.method == 'POST':
        title = package.title
        package.delete()
        messages.success(request, f'Package "{title}" deleted.')
        return redirect('uploaded_packages_list')
    
    return render(request, 'tours/delete_uploaded_package.html', {'package': package})


def share_package(request, token):
    """Public view for shared packages (accessible via share link)."""
    package = get_object_or_404(UploadedPackage, share_token=token)
    return render(request, 'tours/shared_package.html', {'package': package})


def extract_pdf_text(pdf_path):
    """Extract text from PDF for AI training."""
    try:
        import PyPDF2
        
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        return text.strip()
    except ImportError:
        print("PyPDF2 not installed. Run: pip install PyPDF2")
        return ""
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# AI TRAINING DASHBOARD - Human Review Control Room
# ═══════════════════════════════════════════════════════════════════════════════

def staff_required(view_func):
    """Decorator to require staff/admin access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
def ai_training_dashboard(request):
    """Main dashboard for AI training pipeline."""
    # Stats
    raw_pending = RawItinerary.objects.filter(is_processed=False).count()
    pending_review = ProcessedItinerary.objects.filter(status='pending_review').count()
    approved = ProcessedItinerary.objects.filter(status='approved').count()
    rejected = ProcessedItinerary.objects.filter(status='rejected').count()
    
    # Recent items
    recent_processed = ProcessedItinerary.objects.all()[:5]
    recent_raw = RawItinerary.objects.filter(is_processed=False)[:5]
    
    # Scraping stats
    scrape_sources = ScrapingSource.objects.filter(is_active=True).count()
    queue_pending = ScrapeQueue.objects.filter(status='pending').count()
    
    context = {
        'raw_pending': raw_pending,
        'pending_review': pending_review,
        'approved': approved,
        'rejected': rejected,
        'recent_processed': recent_processed,
        'recent_raw': recent_raw,
        'scrape_sources': scrape_sources,
        'queue_pending': queue_pending,
    }
    return render(request, 'tours/ai_training_dashboard.html', context)


@staff_required
def review_list(request):
    """List of items pending human review."""
    status_filter = request.GET.get('status', '')
    
    items = ProcessedItinerary.objects.all().order_by('-created_at')
    if status_filter:
        items = items.filter(status=status_filter)
    
    # Fix any records with wrong status (migration helper)
    ProcessedItinerary.objects.filter(status='pending').update(status='pending_review')
    
    context = {
        'items': items,
        'current_status': status_filter,
        'status_choices': ProcessedItinerary.STATUS_CHOICES,
    }
    return render(request, 'tours/review_list.html', context)


@staff_required
def review_item(request, pk):
    """Split-screen review of a single processed itinerary."""
    processed = get_object_or_404(ProcessedItinerary, pk=pk)
    raw = processed.raw_itinerary
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            processed.status = 'approved'
            processed.reviewer = request.user
            processed.reviewed_at = timezone.now()
            processed.reviewer_notes = request.POST.get('notes', '')
            processed.save()
            messages.success(request, 'Itinerary approved!')
            return redirect('review_list')
        
        elif action == 'reject':
            processed.status = 'rejected'
            processed.reviewer = request.user
            processed.reviewed_at = timezone.now()
            processed.reviewer_notes = request.POST.get('notes', '')
            processed.save()
            messages.success(request, 'Itinerary rejected.')
            return redirect('review_list')
        
        elif action == 'needs_revision':
            processed.status = 'needs_revision'
            processed.reviewer = request.user
            processed.reviewer_notes = request.POST.get('notes', '')
            processed.save()
            messages.info(request, 'Marked for revision.')
            return redirect('review_list')
        
        elif action == 'save':
            # Update editable fields
            processed.title = request.POST.get('title', processed.title)
            processed.destination_country = request.POST.get('destination_country', '')
            processed.duration_days = request.POST.get('duration_days') or None
            processed.budget_level = request.POST.get('budget_level', '')
            processed.trip_type = request.POST.get('trip_type', '')
            processed.group_type = request.POST.get('group_type', '')
            processed.reviewer_notes = request.POST.get('notes', '')
            
            # Update price
            price_str = request.POST.get('estimated_price_usd', '')
            if price_str:
                try:
                    processed.estimated_price_usd = float(price_str)
                except ValueError:
                    pass
            
            # Update derived questions in training_json
            questions = [
                request.POST.get('question_1', ''),
                request.POST.get('question_2', ''),
                request.POST.get('question_3', ''),
            ]
            questions = [q for q in questions if q]  # Remove empty
            
            training_json = processed.training_json or {}
            training_json['derived_user_questions'] = questions
            processed.training_json = training_json
            processed.generated_instruction = questions[0] if questions else ''
            
            processed.save()
            messages.success(request, 'Changes saved.')
    
    # Extract questions for display
    training_json = processed.training_json or {}
    questions = training_json.get('derived_user_questions', [])
    
    context = {
        'processed': processed,
        'raw': raw,
        'budget_levels': ProcessedItinerary.BUDGET_LEVELS,
        'trip_types': ProcessedItinerary.TRIP_TYPES,
        'question_1': questions[0] if len(questions) > 0 else '',
        'question_2': questions[1] if len(questions) > 1 else '',
        'question_3': questions[2] if len(questions) > 2 else '',
    }
    return render(request, 'tours/review_item.html', context)


@staff_required
def scraping_sources(request):
    """Manage scraping sources."""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_source':
            ScrapingSource.objects.create(
                name=request.POST.get('name'),
                base_url=request.POST.get('base_url'),
                requires_javascript=request.POST.get('requires_javascript') == 'on',
                rate_limit_seconds=int(request.POST.get('rate_limit_seconds', 5)),
            )
            messages.success(request, 'Source added!')
        
        elif action == 'add_urls':
            source_id = request.POST.get('source_id')
            urls_text = request.POST.get('urls', '')
            source = get_object_or_404(ScrapingSource, pk=source_id)
            
            urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
            for url in urls:
                ScrapeQueue.objects.get_or_create(source=source, url=url)
            messages.success(request, f'{len(urls)} URLs added to queue!')
        
        elif action == 'delete_source':
            source_id = request.POST.get('source_id')
            ScrapingSource.objects.filter(pk=source_id).delete()
            messages.success(request, 'Source deleted.')
        
        elif action == 'rescrape':
            queue_id = request.POST.get('queue_id')
            queue_item = get_object_or_404(ScrapeQueue, pk=queue_id)
            queue_item.status = 'pending'
            queue_item.error_message = ''
            queue_item.save()
            messages.success(request, f'URL queued for re-scraping: {queue_item.url[:50]}...')
        
        elif action == 'delete_queue':
            queue_id = request.POST.get('queue_id')
            ScrapeQueue.objects.filter(pk=queue_id).delete()
            messages.success(request, 'URL removed from queue.')
        
        return redirect('scraping_sources')
    
    sources = ScrapingSource.objects.all()
    queue_items = ScrapeQueue.objects.select_related('source').order_by('-processed_at', '-created_at')[:50]
    queue_stats = {
        'pending': ScrapeQueue.objects.filter(status='pending').count(),
        'completed': ScrapeQueue.objects.filter(status='completed').count(),
        'failed': ScrapeQueue.objects.filter(status='failed').count(),
    }
    
    context = {
        'sources': sources,
        'queue_items': queue_items,
        'queue_stats': queue_stats,
    }
    return render(request, 'tours/scraping_sources.html', context)


@staff_required
def run_scraper(request):
    """Run the scraper on pending queue items."""
    if request.method == 'POST':
        max_items = int(request.POST.get('max_items', 10))
        
        try:
            from .services.scraper import ItineraryScraper
            scraper = ItineraryScraper()
            stats = scraper.process_pending_queue(max_items=max_items)
            messages.success(request, f"Scraped {stats['succeeded']}/{stats['processed']} items successfully.")
        except Exception as e:
            messages.error(request, f'Scraping error: {str(e)}')
        
        return redirect('ai_training_dashboard')
    
    return redirect('ai_training_dashboard')


@staff_required
def run_gpt_processor(request):
    """Run GPT processing on pending raw itineraries."""
    if request.method == 'POST':
        max_items = int(request.POST.get('max_items', 5))
        
        try:
            from .services.gpt_processor import GPTProcessor
            processor = GPTProcessor()
            stats = processor.process_pending_raw_itineraries(max_items=max_items)
            messages.success(request, f"Processed {stats['succeeded']}/{stats['processed']} items successfully.")
        except Exception as e:
            messages.error(request, f'Processing error: {str(e)}')
        
        return redirect('ai_training_dashboard')
    
    return redirect('ai_training_dashboard')


@staff_required
def export_training_data(request):
    """Preview and export training data as JSONL."""
    from .services.gpt_processor import export_approved_training_data, DecimalEncoder
    import json
    
    action = request.GET.get('action', 'preview')
    
    # Download action
    if action == 'download':
        try:
            content, count, filename = export_approved_training_data(request.user)
            
            if count == 0:
                messages.warning(request, 'No approved records to export.')
                return redirect('export_training_data')
            
            # Return file download
            response = HttpResponse(content, content_type='application/jsonl')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            messages.error(request, f'Export error: {str(e)}')
            return redirect('export_training_data')
    
    # Preview action (default)
    approved = ProcessedItinerary.objects.filter(status='approved')
    
    preview_data = []
    for item in approved[:10]:  # Limit preview to 10 items
        data = item.training_json or {}
        preview_data.append({
            'id': item.id,
            'title': item.title,
            'json_preview': json.dumps(data, indent=2, ensure_ascii=False, cls=DecimalEncoder)[:2000],  # Truncate for display
            'full_json': data
        })
    
    context = {
        'preview_data': preview_data,
        'total_count': approved.count(),
        'preview_count': len(preview_data),
    }
    return render(request, 'tours/export_preview.html', context)


@staff_required
def export_sterilized_data(request):
    """Export sterilized training data for LLM training."""
    if request.method == 'POST':
        try:
            from .services.gpt_processor import export_sterilized_training_data
            content, count, filename = export_sterilized_training_data(request.user)
            
            if count == 0:
                messages.warning(request, 'No approved records to export.')
                return redirect('export_sterilized_data')
            
            # Return file download
            response = HttpResponse(content, content_type='application/jsonl')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            messages.error(request, f'Sterilized export error: {str(e)}')
    
    # Preview page
    from .services.gpt_processor import DataSterilizer
    from tour.models import ProcessedItinerary
    
    approved = ProcessedItinerary.objects.filter(status='approved')
    
    preview_data = []
    for item in approved[:3]:  # Show preview of first 3
        if item.training_json:
            sterilized = DataSterilizer.sterilize_for_training(item.training_json)
            preview_data.append({
                'title': item.title,
                'instruction': sterilized['instruction'],
                'response_preview': sterilized['response'][:1000] + '...' if len(sterilized['response']) > 1000 else sterilized['response'],
                'full_response': sterilized['response']
            })
    
    context = {
        'preview_data': preview_data,
        'total_count': approved.count(),
        'preview_count': len(preview_data),
    }
    return render(request, 'tours/sterilized_export_preview.html', context)


@staff_required
def raw_itineraries_list(request):
    """List raw itineraries."""
    status_filter = request.GET.get('status', '')
    
    items = RawItinerary.objects.all()
    if status_filter == 'pending':
        items = items.filter(is_processed=False)
    elif status_filter == 'processed':
        items = items.filter(is_processed=True)
    
    context = {
        'items': items,
        'current_status': status_filter,
    }
    return render(request, 'tours/raw_itineraries_list.html', context)


@staff_required
def process_single_raw(request, pk):
    """Process a single raw itinerary with GPT."""
    raw = get_object_or_404(RawItinerary, pk=pk)
    force_reprocess = request.GET.get('force', '0') == '1'
    
    try:
        from .services.gpt_processor import GPTProcessor
        processor = GPTProcessor()
        processed = processor.process_raw_itinerary(raw, force_reprocess=True)
        
        if processed:
            messages.success(request, 'Successfully processed!')
            return redirect('review_item', pk=processed.pk)
        else:
            messages.error(request, f'Processing failed: {raw.processing_error}')
    except Exception as e:
        messages.error(request, f'Processing failed: {str(e)}')
    
    return redirect('raw_itineraries_list')


@staff_required
def delete_raw_itinerary(request, pk):
    """Delete a raw itinerary and its associated processed data."""
    if request.method == 'POST':
        raw = get_object_or_404(RawItinerary, pk=pk)
        title = raw.page_title or raw.source_url[:50]
        raw.delete()  # This will cascade delete ProcessedItinerary if exists
        messages.success(request, f'Deleted: {title}')
    return redirect('raw_itineraries_list')


@staff_required
def delete_processed_itinerary(request, pk):
    """Delete a processed itinerary."""
    if request.method == 'POST':
        processed = get_object_or_404(ProcessedItinerary, pk=pk)
        title = processed.title
        # Also reset raw itinerary status
        if processed.raw_itinerary:
            processed.raw_itinerary.is_processed = False
            processed.raw_itinerary.save()
        processed.delete()
        messages.success(request, f'Deleted: {title}')
    return redirect('review_list')
