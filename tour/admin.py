from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
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
    # Pricing models
    Destination,
    HotelRate,
    TransportRate,
    ActivityRate,
    FuelPrice,
    FlightRate,
    TourRequest,
    # AI Training Pipeline
    ScrapingSource,
    ScrapeQueue,
    RawItinerary,
    ProcessedItinerary,
    TrainingExport,
    UploadedPackage,
)

class ItineraryInline(admin.TabularInline):
    model = Itinerary
    extra = 1

class TourPackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'price', 'availability', 'start_date', 'end_date', 'operator')
    list_filter = ('location', 'start_date', 'price')
    search_fields = ('title', 'location', 'operator__username')
    inlines = [ItineraryInline]


# =============================================================================
# PRICING ADMIN CLASSES
# =============================================================================

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'country', 'avg_time_needed', 'is_active')
    list_filter = ('region', 'country', 'is_active')
    search_fields = ('name', 'region', 'highlights')
    list_editable = ('is_active',)


class HotelRateInline(admin.TabularInline):
    model = HotelRate
    extra = 0
    fields = ('name', 'tier', 'room_type', 'meal_plan', 'rate_low_season', 'rate_high_season', 'is_active')


class ActivityRateInline(admin.TabularInline):
    model = ActivityRate
    extra = 0
    fields = ('name', 'activity_type', 'rate_adult', 'rate_child', 'duration', 'is_active')


@admin.register(HotelRate)
class HotelRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination', 'tier', 'room_type', 'meal_plan', 'rate_low_season', 'rate_high_season', 'is_active', 'updated_at')
    list_filter = ('tier', 'destination', 'meal_plan', 'is_active')
    search_fields = ('name', 'destination__name')
    list_editable = ('rate_low_season', 'rate_high_season', 'is_active')
    ordering = ('destination', 'tier', 'name')


@admin.register(TransportRate)
class TransportRateAdmin(admin.ModelAdmin):
    list_display = ('vehicle_type', 'rate_per_day', 'max_passengers', 'fuel_consumption', 'is_active', 'updated_at')
    list_filter = ('vehicle_type', 'is_active')
    list_editable = ('rate_per_day', 'is_active')


@admin.register(ActivityRate)
class ActivityRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'activity_type', 'destination', 'rate_adult', 'rate_child', 'duration', 'is_active', 'updated_at')
    list_filter = ('activity_type', 'destination', 'is_active')
    search_fields = ('name', 'destination__name')
    list_editable = ('rate_adult', 'rate_child', 'is_active')


@admin.register(FuelPrice)
class FuelPriceAdmin(admin.ModelAdmin):
    list_display = ('fuel_type', 'price_per_liter', 'price_per_liter_usd', 'updated_at')
    list_editable = ('price_per_liter', 'price_per_liter_usd')


@admin.register(FlightRate)
class FlightRateAdmin(admin.ModelAdmin):
    list_display = ('airline', 'origin_code', 'destination_code', 'price_economy', 'flight_duration', 'frequency', 'is_active', 'updated_at')
    list_filter = ('airline', 'is_active')
    search_fields = ('origin', 'destination', 'origin_code', 'destination_code')
    list_editable = ('price_economy', 'is_active')
    ordering = ('origin_code', 'destination_code')
    fieldsets = (
        ('Route', {
            'fields': ('airline', ('origin', 'origin_code'), ('destination', 'destination_code'))
        }),
        ('Pricing', {
            'fields': ('price_economy', 'price_business', 'baggage_allowance')
        }),
        ('Details', {
            'fields': ('flight_duration', 'frequency', 'notes', 'is_active')
        }),
    )


@admin.register(TourRequest)
class TourRequestAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'tour_type', 'group_type', 'start_date', 'end_date', 'budget_per_person', 'status', 'operator')
    list_filter = ('status', 'tour_type', 'group_type', 'operator')
    search_fields = ('client_name', 'client_email', 'special_requests')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('preferred_destinations',)
    fieldsets = (
        ('Client Information', {
            'fields': ('client_name', 'client_email', 'client_phone')
        }),
        ('Tour Requirements', {
            'fields': ('tour_type', 'group_type', 'num_adults', 'num_children')
        }),
        ('Budget & Dates', {
            'fields': ('budget_per_person', 'budget_flexible', 'start_date', 'end_date', 'dates_flexible')
        }),
        ('Preferences', {
            'fields': ('preferred_destinations', 'special_requests', 'dietary_requirements', 'mobility_requirements')
        }),
        ('Generated Content', {
            'fields': ('generated_itinerary', 'total_estimated_cost'),
            'classes': ('collapse',)
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes', 'operator')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(Vendor)
admin.site.register(TourPackage, TourPackageAdmin)
admin.site.register(Itinerary)
admin.site.register(Review)
admin.site.register(Booking)
admin.site.register(Trip)
admin.site.register(Event)
admin.site.register(Attendee)
admin.site.register(EventSession)


# =============================================================================
# AI TRAINING PIPELINE ADMIN
# =============================================================================

@admin.register(ScrapingSource)
class ScrapingSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url', 'is_active', 'requires_javascript', 'rate_limit_seconds', 'total_scraped', 'last_scraped_at')
    list_filter = ('is_active', 'requires_javascript')
    search_fields = ('name', 'base_url')
    list_editable = ('is_active', 'rate_limit_seconds')
    readonly_fields = ('total_scraped', 'last_scraped_at', 'created_at')


@admin.register(ScrapeQueue)
class ScrapeQueueAdmin(admin.ModelAdmin):
    list_display = ('url_short', 'source', 'status', 'priority', 'retry_count', 'created_at', 'processed_at')
    list_filter = ('status', 'source')
    search_fields = ('url',)
    list_editable = ('priority',)
    readonly_fields = ('processed_at', 'created_at')
    actions = ['mark_pending', 'mark_failed']
    
    def url_short(self, obj):
        return obj.url[:60] + '...' if len(obj.url) > 60 else obj.url
    url_short.short_description = 'URL'
    
    @admin.action(description='Mark selected as Pending')
    def mark_pending(self, request, queryset):
        queryset.update(status='pending', retry_count=0)
    
    @admin.action(description='Mark selected as Failed')
    def mark_failed(self, request, queryset):
        queryset.update(status='failed')


@admin.register(RawItinerary)
class RawItineraryAdmin(admin.ModelAdmin):
    list_display = ('title_short', 'source_type', 'source', 'is_processed', 'text_length', 'scraped_at')
    list_filter = ('source_type', 'is_processed', 'source')
    search_fields = ('page_title', 'source_url', 'raw_text')
    readonly_fields = ('scraped_at',)
    actions = ['process_with_gpt']
    
    def title_short(self, obj):
        title = obj.page_title or obj.source_url or 'No title'
        return title[:50] + '...' if len(title) > 50 else title
    title_short.short_description = 'Title'
    
    def text_length(self, obj):
        return f'{len(obj.raw_text):,} chars'
    text_length.short_description = 'Text Length'
    
    @admin.action(description='Process selected with GPT')
    def process_with_gpt(self, request, queryset):
        from .services.gpt_processor import GPTProcessor
        processor = GPTProcessor()
        processed = 0
        for raw in queryset.filter(is_processed=False):
            result = processor.process_raw_itinerary(raw)
            if result:
                processed += 1
        self.message_user(request, f'Processed {processed} items')


@admin.register(ProcessedItinerary)
class ProcessedItineraryAdmin(admin.ModelAdmin):
    list_display = ('title', 'destination_country', 'duration_days', 'budget_level', 'trip_type', 'status', 'status_badge', 'reviewed_at')
    list_filter = ('status', 'budget_level', 'trip_type', 'destination_country')
    search_fields = ('title', 'generated_instruction', 'destination_country')
    list_editable = ('status',)
    readonly_fields = ('raw_itinerary', 'gpt_model_used', 'gpt_processing_time', 'gpt_tokens_used', 'created_at', 'updated_at')
    actions = ['approve_selected', 'reject_selected', 'export_as_jsonl']
    
    fieldsets = (
        ('Generated Instruction', {
            'fields': ('generated_instruction',),
            'description': 'The reverse prompt - what a user would type to get this itinerary'
        }),
        ('Basic Info', {
            'fields': ('title', 'destination_country', 'destinations', 'duration_days')
        }),
        ('Classification', {
            'fields': ('budget_level', 'trip_type', 'group_type', 'estimated_price_usd')
        }),
        ('Itinerary Data', {
            'fields': ('itinerary_json', 'inclusions', 'exclusions', 'accommodations', 'activities'),
            'classes': ('collapse',)
        }),
        ('Training Data', {
            'fields': ('training_json',),
            'classes': ('collapse',)
        }),
        ('Review Status', {
            'fields': ('status', 'reviewer', 'reviewer_notes', 'reviewed_at')
        }),
        ('Processing Info', {
            'fields': ('raw_itinerary', 'gpt_model_used', 'gpt_processing_time', 'gpt_tokens_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending_review': '#3b82f6',
            'approved': '#22c55e',
            'rejected': '#ef4444',
            'needs_revision': '#f59e0b',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:4px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    @admin.action(description='Approve selected')
    def approve_selected(self, request, queryset):
        queryset.update(status='approved', reviewer=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} items approved')
    
    @admin.action(description='Reject selected')
    def reject_selected(self, request, queryset):
        queryset.update(status='rejected', reviewer=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} items rejected')
    
    @admin.action(description='Export approved as JSONL')
    def export_as_jsonl(self, request, queryset):
        from django.http import HttpResponse
        import json
        
        approved = queryset.filter(status='approved')
        records = []
        for item in approved:
            records.append({
                'instruction': item.generated_instruction,
                'output': item.training_json or {
                    'title': item.title,
                    'destinations': item.destinations,
                    'itinerary': item.itinerary_json,
                }
            })
        
        content = '\n'.join(json.dumps(r, ensure_ascii=False) for r in records)
        response = HttpResponse(content, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="training_data_{timezone.now().strftime("%Y%m%d")}.jsonl"'
        return response


@admin.register(TrainingExport)
class TrainingExportAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'record_count', 'export_format', 'exported_by', 'created_at')
    list_filter = ('export_format', 'created_at')
    readonly_fields = ('file_name', 'file_path', 'record_count', 'export_format', 'exported_by', 'created_at')


@admin.register(UploadedPackage)
class UploadedPackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'package_type', 'duration_days', 'status', 'is_analyzed', 'operator', 'created_at')
    list_filter = ('status', 'package_type', 'is_analyzed', 'is_public')
    search_fields = ('title', 'description', 'destinations')
    list_editable = ('status',)
    readonly_fields = ('extracted_text', 'is_analyzed', 'share_token', 'created_at', 'updated_at')
    actions = ['create_raw_itinerary']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('operator', 'title', 'description', 'package_type', 'duration_days', 'destinations')
        }),
        ('Pricing', {
            'fields': ('price_per_person', 'min_group_size', 'max_group_size')
        }),
        ('Files', {
            'fields': ('pdf_itinerary', 'cover_image', 'image_2', 'image_3', 'image_4')
        }),
        ('AI Processing (Internal)', {
            'fields': ('extracted_text', 'is_analyzed'),
            'classes': ('collapse',)
        }),
        ('Sharing', {
            'fields': ('share_token', 'is_public', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.action(description='Create Raw Itinerary for AI Processing')
    def create_raw_itinerary(self, request, queryset):
        from .services.scraper import create_raw_from_uploaded_package
        created = 0
        for pkg in queryset.filter(is_analyzed=True):
            raw = create_raw_from_uploaded_package(pkg)
            if raw:
                created += 1
        self.message_user(request, f'Created {created} raw itineraries for processing')
