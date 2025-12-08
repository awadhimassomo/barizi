from rest_framework import serializers
from .models import TourPackage, Itinerary, Review, Vendor, Event, ExhibitorSpace, ExhibitorBooking
from django.contrib.auth import get_user_model

User = get_user_model()

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'contact_info', 'service_type']  # Update fields as needed


class ItinerarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Itinerary
        fields = ['id', 'day_number', 'title', 'description', 'accommodation']


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']


class TourPackageSerializer(serializers.ModelSerializer):
    itineraries = ItinerarySerializer(many=True, read_only=True)
    tour_reviews = ReviewSerializer(many=True, read_only=True)
    vendors = VendorSerializer(many=True, read_only=True)
    operator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TourPackage
        fields = [
            'id', 'operator', 'title', 'company_name', 'image', 'rating', 'reviews_count',
            'description', 'duration', 'includes', 'excludes', 'cancellation_policy',
            'special_offer', 'price', 'min_people', 'max_people', 'availability',
            'start_date', 'end_date', 'location', 'coordinates', 'vendors',
            'itineraries', 'tour_reviews', 'created_at', 'updated_at'
        ]


class EventSerializer(serializers.ModelSerializer):
    # For displaying the category name (e.g., "Festival" instead of "festival")
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            # location is represented using venue/city fields
            'is_online',
            'online_link',
            'date',
            'time',
            'duration',
            'category',
            'category_display',
            'image',
            'slug',
            'latitude',
            'longitude',
            'has_exhibitors',
            'extra_details',  # For storing marathon-specific or festival-specific data
        ]

    # Validate online events to ensure an online_link is provided
    def validate(self, data):
        if data.get('is_online') and not data.get('online_link'):
            raise serializers.ValidationError("Online events must include an online link.")
        return data


class ExhibitorSpaceSerializer(serializers.ModelSerializer):
    available_slots = serializers.SerializerMethodField()

    class Meta:
        model = ExhibitorSpace
        fields = ['id', 'event', 'name', 'price', 'total_slots', 'description', 'available_slots']

    def get_available_slots(self, obj):
        # Count all non-cancelled bookings against this space
        used = obj.bookings.exclude(status='cancelled').count()
        return max(obj.total_slots - used, 0)


class ExhibitorBookingSerializer(serializers.ModelSerializer):
    space = serializers.PrimaryKeyRelatedField(queryset=ExhibitorSpace.objects.all())

    class Meta:
        model = ExhibitorBooking
        fields = [
            'id',
            'space',
            'exhibitor_name',
            'business_name',
            'phone_number',
            'status',
            'paid_amount',
            'created_at',
        ]

