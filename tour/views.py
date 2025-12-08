from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404
from django.views import View
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import CreateView
from django.conf import settings
from .forms import ItineraryForm, TourPackageForm
from .models import Attendee, Booking, Event, EventSession, ExhibitorBooking, ExhibitorSpace, Itinerary, TourPackage, Trip, Vendor
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
    events = Event.objects.filter(planner=request.user).order_by('-date')
    return render(request, 'events/my_events_dashboard.html', {'events': events})


@login_required
def exhibitors_overview(request):
    """Overview page listing the planner's events with exhibitor management links."""
    events = Event.objects.filter(planner=request.user).order_by('-date')
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

    exhibitor_spaces = []
    if event.has_exhibitors:
        spaces = list(event.exhibitor_spaces.all())
        for s in spaces:
            used = s.bookings.exclude(status='cancelled').count()
            s.available_slots = max(s.total_slots - used, 0)
        exhibitor_spaces = spaces

    return render(request, 'pages/eventdetails.html', {
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

        messages.success(request, 'Event created and agenda generated successfully!')
        print(f"[EVENT] Created {len(sessions)} EventSession rows for event {event.id}")  # debug
        return redirect('edit-event-agenda', event_id=event.id)

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
    # Fetch planner's events and basic stats for the dashboard
    events = Event.objects.filter(planner=request.user).order_by('-date')

    total_events = events.count()
    total_attendees = Attendee.objects.filter(event__planner=request.user).count()
    cancelled_events = events.filter(status='cancelled').count()

    total_revenue = Decimal('0')
    for e in events:
        if e.ticket_price:
            total_revenue += e.ticket_price * e.attendees.count()

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
