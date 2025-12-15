"""
GPT Processing Service - The "Intelligence Layer"
Uses GPT-4 to organize raw itinerary text into structured data.
Implements "Reverse Prompting" to generate user instructions.
"""

import json
import time
import logging
from decimal import Decimal
from typing import Optional
from django.conf import settings
from django.utils import timezone
from openai import OpenAI

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class DataSterilizer:
    """Converts structured itinerary JSON into human-readable markdown for LLM training."""
    
    @staticmethod
    def serialize_itinerary(itinerary):
        """
        Convert a structured itinerary dictionary into a human-readable text format.
        Handles duration calculation from actual days and anonymizes pricing.
        
        Args:
            itinerary (dict): The structured itinerary data
            
        Returns:
            str: Formatted text representation of the itinerary
        """
        if isinstance(itinerary, str):
            try:
                itinerary = json.loads(itinerary)
            except json.JSONDecodeError:
                return "Invalid JSON data"
        
        if not isinstance(itinerary, dict):
            return "Invalid itinerary format"
            
        output = []
        output.append(f"Tour: {itinerary.get('title', 'Untitled Tour')}\n")
        
        # Calculate real duration from actual days
        days = itinerary.get('itinerary_structure', {}).get('days', [])
        if not days and 'days' in itinerary:
            days = itinerary['days']
        
        # Count actual activity days (excluding arrival/departure if marked as such)
        activity_days = 0
        for day in days:
            if isinstance(day, dict):
                day_type = day.get('day_type', 'activity')
                if day_type in ['activity', 'summit', 'hiking']:
                    activity_days += 1
        
        # Get total program days (all days including travel)
        total_days = len([d for d in days if isinstance(d, dict)])
        
        # Add duration info
        duration_info = []
        if activity_days > 0:
            duration_info.append(f"{activity_days} days of activities")
        if total_days > 0:
            duration_info.append(f"{total_days} days total program")
        if duration_info:
            output.append("Duration: " + " | ".join(duration_info) + "\n")
        
        # Process each day
        total_cost = 0
        has_pricing = False
        
        for day in days:
            if not isinstance(day, dict):
                continue
                
            day_num = day.get('day', '?')
            day_title = day.get('title', 'No Title')
            output.append(f"Day {day_num}: {day_title}")
            
            # Add day type if available
            day_type = day.get('day_type')
            if day_type and day_type != 'activity':
                output.append(f"  Type: {day_type.replace('_', ' ').title()}")
            
            # Add activities if available
            activities = day.get('activities', [])
            if activities and isinstance(activities, list):
                output.append("  Activities: " + ", ".join(str(a) for a in activities if a))
            
            # Add transport if available
            transport = day.get('transport')
            if transport:
                output.append(f"  Transport: {transport}")
            
            # Add accommodation if available
            acc_name = day.get('accommodation_name')
            acc_type = day.get('accommodation_type', '').replace('_', ' ').title()
            if acc_name:
                acc_display = f"{acc_name} ({acc_type})" if acc_type else acc_name
                output.append(f"  Accommodation: {acc_display}")
            
            # Add meals if available
            meals = day.get('meals', [])
            if meals and isinstance(meals, list):
                output.append("  Meals: " + ", ".join(str(m) for m in meals if m))
            
            # Anonymize and aggregate cost
            cost = day.get('cost')
            if cost is not None:
                try:
                    cost = float(cost)
                    total_cost += cost
                    has_pricing = True
                except (ValueError, TypeError):
                    pass
            
            output.append("")  # Blank line between days
        
        # Add estimated budget range if we have pricing data
        if has_pricing:
            # Calculate budget range (±15% of total)
            lower_bound = int(total_cost * 0.85)
            upper_bound = int(total_cost * 1.15)
            output.append(f"\nEstimated Budget Range: ${lower_bound:,} - ${upper_bound:,} per person")
            output.append("Note: Prices are approximate and can vary based on group size, season, and availability.")
        
        # Add inclusions/exclusions if available
        if 'inclusions' in itinerary and isinstance(itinerary['inclusions'], list) and itinerary['inclusions']:
            output.append("\nIncluded:" + "\n- " + "\n- ".join(str(i) for i in itinerary['inclusions'] if i))
            
        if 'exclusions' in itinerary and isinstance(itinerary['exclusions'], list) and itinerary['exclusions']:
            output.append("\nNot Included:" + "\n- " + "\n- ".join(str(e) for e in itinerary['exclusions'] if e))
        
        return "\n".join(output)
    
    @staticmethod
    def sterilize_itinerary(data: dict) -> str:
        """Convert structured JSON to human-readable markdown format."""
        lines = []
        
        # Header
        tour_identity = data.get('tour_identity', {})
        lines.append(f"# {tour_identity.get('tour_title', 'Tour Itinerary')}")
        lines.append("")
        
        # Duration
        duration = data.get('duration', {})
        if duration:
            total_days = duration.get('total_program_days', duration.get('activity_days', 0))
            activity_days = duration.get('activity_days', total_days)
            lines.append(f"**Duration:** {activity_days} days of activities in a {total_days}-day program")
            lines.append("")
        
        # Overview
        itinerary_structure = data.get('itinerary_structure', {})
        overview = itinerary_structure.get('overview')
        if overview:
            lines.append(f"**Overview:** {overview}")
            lines.append("")
        
        # Route
        route_name = itinerary_structure.get('route_name')
        if route_name:
            lines.append(f"**Route:** {route_name}")
            lines.append("")
        
        # Day by day itinerary
        days = itinerary_structure.get('days', [])
        if days:
            lines.append("## Day-by-Day Itinerary")
            lines.append("")
            
            for day in days:
                day_num = day.get('day')
                title = day.get('title', f'Day {day_num}')
                day_type = day.get('day_type', 'activity')
                
                lines.append(f"### Day {day_num}: {title}")
                
                # Location
                location = day.get('location')
                if location:
                    lines.append(f"**Location:** {location}")
                
                # Altitude
                altitude = day.get('altitude_meters')
                if altitude:
                    lines.append(f"**Altitude:** {altitude}m")
                
                # Distance
                distance = day.get('distance_km')
                if distance:
                    lines.append(f"**Distance:** {distance}km")
                
                # Hiking hours
                hiking_hours = day.get('hiking_hours')
                if hiking_hours:
                    lines.append(f"**Hiking Time:** {hiking_hours} hours")
                
                # Activities
                activities = day.get('activities', [])
                if activities:
                    lines.append(f"**Activities:** {', '.join(activities)}")
                
                # Accommodation
                accommodation = day.get('accommodation_name')
                acc_type = day.get('accommodation_type')
                if accommodation:
                    acc_desc = accommodation
                    if acc_type and acc_type != 'null':
                        acc_desc += f" ({acc_type})"
                    lines.append(f"**Accommodation:** {acc_desc}")
                
                # Meals
                meals = day.get('meals', [])
                if meals:
                    lines.append(f"**Meals:** {', '.join(meals)}")
                
                lines.append("")  # Empty line between days
        
        # Inclusions
        inclusions = data.get('inclusions', [])
        if inclusions:
            lines.append("## What's Included")
            lines.append("")
            for item in inclusions:
                lines.append(f"- {item}")
            lines.append("")
        
        # Exclusions
        exclusions = data.get('exclusions', [])
        if exclusions:
            lines.append("## What's Not Included")
            lines.append("")
            for item in exclusions:
                lines.append(f"- {item}")
            lines.append("")
        
        # Pricing
        pricing = data.get('pricing', {})
        if pricing.get('price_displayed', False):
            price = pricing.get('price_per_person_usd')
            currency = pricing.get('currency', 'USD')
            if price:
                # Convert to tier instead of exact price
                if price < 2000:
                    price_tier = "Budget"
                elif price < 3500:
                    price_tier = "Mid-range"
                elif price < 5000:
                    price_tier = "Premium"
                else:
                    price_tier = "Luxury"
                
                lines.append(f"**Price Range:** {price_tier} (${price} per person in {currency})")
                
                notes = pricing.get('price_notes')
                if notes:
                    lines.append(f"**Pricing Notes:** {notes}")
                lines.append("")
        
        # Operator reasoning (for internal reference)
        operator_reasoning = data.get('operator_reasoning', {})
        if operator_reasoning:
            lines.append("## Why This Itinerary Works")
            lines.append("")
            for key, value in operator_reasoning.items():
                if value:
                    key_name = key.replace('_', ' ').title()
                    lines.append(f"**{key_name}:** {value}")
            lines.append("")
        
        return '\n'.join(lines).strip()
    
    @staticmethod
    def sterilize_for_training(data: dict) -> dict:
        """Create sterilized training record with human-readable response."""
        sterilized_response = DataSterilizer.sterilize_itinerary(data)
        
        # Get the first question as instruction
        derived_questions = data.get('derived_user_questions', [])
        instruction = derived_questions[0] if derived_questions else data.get('generated_instruction', '')
        
        # Create training record
        training_record = {
            "instruction": instruction,
            "response": sterilized_response,
            "metadata": {
                "source_type": data.get('source_type'),
                "operator_name": data.get('operator_name'),
                "country": data.get('country'),
                "destination": data.get('destination'),
                "tour_category": data.get('tour_identity', {}).get('tour_category'),
                "duration_days": data.get('duration', {}).get('activity_days'),
                "data_quality": data.get('data_quality_tags', {})
            }
        }
        
        return training_record


def export_sterilized_training_data(user) -> tuple[str, int, str]:
    """Export approved training data as sterilized JSONL for LLM training."""
    from tour.models import ProcessedItinerary, TrainingExport
    from django.core.files.base import ContentFile
    
    approved = ProcessedItinerary.objects.filter(status='approved')
    
    records = []
    for item in approved:
        if item.training_json:
            sterilized_record = DataSterilizer.sterilize_for_training(item.training_json)
            records.append(sterilized_record)
    
    # Generate file content
    content = '\n'.join(json.dumps(r, ensure_ascii=False, cls=DecimalEncoder) for r in records)
    file_name = f"sterilized_training_data_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    # Create export record
    export = TrainingExport.objects.create(
        exported_by=user,
        file_name=file_name,
        record_count=len(records),
        export_format='sterilized_jsonl',
    )
    export.file_path.save(file_name, ContentFile(content.encode('utf-8')))
    
    return content, len(records), file_name


class GPTProcessor:
    """Processes raw itinerary text using GPT to extract structured data."""
    
    EXTRACTION_PROMPT = """You are an expert travel data analyst creating AI training data. Extract structured tour data from this raw itinerary.

SOURCE URL: {source_url}
OPERATOR NAME: {operator_name}

RAW ITINERARY TEXT:
{raw_text}

---

Extract and return a JSON object with this EXACT structure:

{{
    "source_type": "operator_website",
    "operator_name": "{operator_name}",
    "country": "Tanzania or Kenya or relevant country",
    "destination": "Main destination (e.g., Zanzibar, Serengeti, Kilimanjaro)",
    "url": "{source_url}",
    "content_type": "published_itinerary",

    "tour_identity": {{
        "tour_title": "Exact tour title from the page",
        "tour_category": "safari|beach|trekking|city_tour|honeymoon|adventure|cultural|combined",
        "location_focus": "Main area or route (e.g., Northern Circuit, Stone Town, Lemosho Route)"
    }},

    "duration": {{
        "total_program_days": 9,
        "activity_days": 7,
        "activity_nights": 6,
        "logistics_days": 2,
        "duration_notes": "7 days trekking plus arrival and departure days"
    }},

    "itinerary_structure": {{
        "overview": "Brief 1-2 sentence summary of the tour",
        "route_name": "Route name if applicable (e.g., Lemosho Route, Northern Circuit)",
        "days": [
            {{
                "day": 1,
                "day_type": "arrival|activity|summit|departure|rest",
                "title": "Day title (e.g., Arrival in Arusha)",
                "location": "Location name",
                "altitude_meters": null,
                "distance_km": null,
                "hiking_hours": null,
                "activities": ["Activity 1", "Activity 2", "Activity 3"],
                "accommodation_name": "Hotel/Lodge/Camp name or null",
                "accommodation_type": "hotel|lodge|tented_camp|camping|null",
                "meals": ["Breakfast", "Lunch", "Dinner"]
            }}
        ]
    }},

    "inclusions": ["Park fees", "Accommodation", "Meals as specified", "Professional guide", "Transport"],
    "exclusions": ["International flights", "Visa fees", "Travel insurance", "Tips and gratuities"],

    "pricing": {{
        "price_displayed": true,
        "price_per_person_usd": 3500,
        "currency": "USD",
        "price_includes_flights": false,
        "group_size_affects_price": true,
        "season_affects_price": true,
        "price_notes": "Price varies by group size and season"
    }},

    "user_flexibility": {{
        "dates_flexible": true,
        "accommodation_preferences_accepted": true,
        "can_request_modifications": true
    }},

    "operator_constraints": {{
        "route_fixed": false,
        "safety_critical_elements": ["Acclimatization schedule", "Guide ratio"],
        "minimum_group_size": 1,
        "maximum_group_size": null
    }},

    "operator_reasoning": {{
        "route_selection": "Why this route was chosen (e.g., Lemosho chosen for better acclimatization and scenic variety)",
        "duration_reasoning": "Why this duration (e.g., 7 trek days increases summit success rate to 90%)",
        "difficulty_assessment": "Who this is suitable for (e.g., Suitable for average fitness with prior preparation)",
        "value_proposition": "Why this itinerary is good value (e.g., Includes pre/post accommodation unlike budget options)"
    }},

    "derived_user_questions": [
        "Question that logically leads to THIS specific itinerary",
        "Question about preferences that match this route/tour",
        "Question with constraints that this itinerary satisfies"
    ],

    "user_intent": {{
        "primary_goal": "climb_kilimanjaro|safari|beach_holiday|cultural_tour|honeymoon|adventure",
        "fitness_level": "unknown|beginner|average|athletic|professional",
        "time_available": "about X days or flexible",
        "preferences": ["scenic", "good acclimatization", "wildlife", "relaxation"],
        "constraints": ["budget", "time", "fitness", "none specified"]
    }},

    "data_quality_tags": {{
        "structured": true,
        "marketing_language": "low|medium|high",
        "operational_detail_level": "low|medium|high",
        "source_reliability": "high"
    }}
}}

CRITICAL RULES:

1. DURATION: Count ALL days including arrival/departure. Label each day with day_type.
   - If title says "7 Days" but there are 9 actual days, set activity_days=7, total_program_days=9

2. DERIVED QUESTIONS must logically lead to THIS itinerary:
   - BAD: "I'm interested in a trek in Tanzania, can you tell me more?"
   - GOOD: "I want to climb Kilimanjaro and prefer a scenic route with good acclimatization. What would you recommend?"
   - GOOD: "I have about a week for Kilimanjaro and I'm reasonably fit. Which route has the best success rate?"
   - GOOD: "I want a guided Kilimanjaro climb that includes hotel stays before and after. What's available?"

3. OPERATOR REASONING is critical - explain WHY this itinerary exists:
   - Why this route? Why this duration? Why these accommodations?
   - This teaches the AI to THINK like an operator

4. SEPARATE user flexibility from operator constraints:
   - User can ask for changes (user_flexibility)
   - Operator decides what's possible (operator_constraints)

5. USER INTENT should be what a typical customer would express BEFORE seeing this itinerary

6. PRICING: Look for $, USD, per person, pp, pax. If not found, set price_displayed: false

Return ONLY valid JSON, no other text."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
    
    def process_raw_itinerary(self, raw_itinerary, force_reprocess=False) -> Optional['ProcessedItinerary']:
        """
        Process a RawItinerary and create/update a ProcessedItinerary.
        
        Args:
            raw_itinerary: The RawItinerary to process
            force_reprocess: If True, reprocess even if already processed
        
        Returns the ProcessedItinerary if successful, None if failed.
        """
        from tour.models import ProcessedItinerary
        
        if raw_itinerary.is_processed and not force_reprocess:
            logger.warning(f"RawItinerary {raw_itinerary.id} already processed. Use force_reprocess=True to reprocess.")
            return None
        
        try:
            start_time = time.time()
            
            # Get operator name from scraping source if available
            operator_name = "Unknown Operator"
            source_url = raw_itinerary.source_url or ""
            if hasattr(raw_itinerary, 'scrape_queue') and raw_itinerary.scrape_queue:
                operator_name = raw_itinerary.scrape_queue.source.name
            elif raw_itinerary.source_url:
                # Extract from URL domain
                from urllib.parse import urlparse
                domain = urlparse(raw_itinerary.source_url).netloc
                operator_name = domain.replace('www.', '').replace('.com', '').replace('.co.tz', '').title()
            
            # Call GPT
            prompt = self.EXTRACTION_PROMPT.format(
                raw_text=raw_itinerary.raw_text[:15000],
                source_url=source_url,
                operator_name=operator_name
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a travel data extraction expert. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            processing_time = time.time() - start_time
            tokens_used = response.usage.total_tokens if response.usage else None
            
            # Parse response
            result_text = response.choices[0].message.content
            data = json.loads(result_text)
            
            # Extract from new nested structure
            tour_identity = data.get('tour_identity', {})
            duration = data.get('duration', {})
            itinerary_structure = data.get('itinerary_structure', {})
            pricing = data.get('pricing', {})
            
            # Extract accommodations from days
            accommodations = []
            activities = []
            for day in itinerary_structure.get('days', []):
                if day.get('accommodation_name'):
                    accommodations.append({
                        'name': day.get('accommodation_name'),
                        'type': day.get('accommodation_type'),
                        'location': day.get('location')
                    })
                activities.extend(day.get('activities', []))
            
            # Remove duplicate activities
            activities = list(set(activities))
            
            # Get first question from derived_user_questions for backward compatibility
            derived_questions = data.get('derived_user_questions', [])
            first_question = derived_questions[0] if derived_questions else ''
            
            # Get duration - prefer activity_days, fallback to total
            duration_days = duration.get('activity_days') or duration.get('total_program_days')
            
            # Create or update ProcessedItinerary
            processed, created = ProcessedItinerary.objects.update_or_create(
                raw_itinerary=raw_itinerary,
                defaults={
                    'generated_instruction': first_question,
                    'title': tour_identity.get('tour_title', raw_itinerary.page_title or 'Untitled'),
                    'destination_country': data.get('country', ''),
                    'destinations': [data.get('destination', '')] if data.get('destination') else [],
                    'duration_days': duration_days,
                    'budget_level': 'mid_range',  # Default, can be inferred from price
                    'estimated_price_usd': pricing.get('price_per_person_usd'),
                    'trip_type': tour_identity.get('tour_category', ''),
                    'group_type': 'Group' if data.get('assumptions_and_flexibility', {}).get('group_tour_available') else 'Private',
                    'itinerary_json': itinerary_structure,
                    'inclusions': data.get('inclusions', []),
                    'exclusions': data.get('exclusions', []),
                    'accommodations': accommodations,
                    'activities': activities,
                    'training_json': data,  # Store the FULL structured data
                    'gpt_model_used': self.model,
                    'gpt_processing_time': processing_time,
                    'gpt_tokens_used': tokens_used,
                    'status': 'pending_review',  # Reset status for re-review
                }
            )
            
            action = "Created" if created else "Updated"
            logger.info(f"{action} ProcessedItinerary {processed.id}")
            
            # Mark raw as processed
            raw_itinerary.is_processed = True
            raw_itinerary.save()
            
            logger.info(f"Successfully processed RawItinerary {raw_itinerary.id} -> ProcessedItinerary {processed.id}")
            return processed
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {str(e)}"
            logger.error(f"Failed to process RawItinerary {raw_itinerary.id}: {error_msg}")
            raw_itinerary.processing_error = error_msg
            raw_itinerary.save()
            return None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to process RawItinerary {raw_itinerary.id}: {error_msg}")
            raw_itinerary.processing_error = error_msg
            raw_itinerary.save()
            return None
    
    def process_pending_raw_itineraries(self, max_items: int = 5) -> dict:
        """
        Process pending raw itineraries.
        
        Returns stats dict with counts.
        """
        from tour.models import RawItinerary
        
        pending = RawItinerary.objects.filter(
            is_processed=False,
            processing_error=''
        )[:max_items]
        
        stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
        }
        
        for raw in pending:
            stats['processed'] += 1
            result = self.process_raw_itinerary(raw)
            if result:
                stats['succeeded'] += 1
            else:
                stats['failed'] += 1
        
        return stats


def export_approved_training_data(user, format='jsonl') -> tuple:
    """
    Export all approved ProcessedItineraries in the structured training format.
    
    Returns (file_content, record_count, file_name)
    """
    from tour.models import ProcessedItinerary, TrainingExport
    from django.core.files.base import ContentFile
    
    approved = ProcessedItinerary.objects.filter(status='approved')
    
    records = []
    for item in approved:
        # Use the full training_json which contains the structured data
        training_data = item.training_json or {}
        
        # If we have the new format, use it directly
        if 'tour_identity' in training_data:
            records.append(training_data)
        else:
            # Build from ProcessedItinerary fields (legacy support)
            training_record = {
                "source_type": "operator_website",
                "operator_name": training_data.get('operator_name', 'Unknown'),
                "country": item.destination_country,
                "destination": item.destinations[0] if item.destinations else item.destination_country,
                "url": item.raw_itinerary.source_url if item.raw_itinerary else "",
                "content_type": "published_itinerary",
                
                "tour_identity": {
                    "tour_title": item.title,
                    "tour_category": item.trip_type,
                    "duration_days": item.duration_days,
                    "duration_nights": (item.duration_days - 1) if item.duration_days else None,
                    "location_focus": item.destinations[0] if item.destinations else ""
                },
                
                "itinerary_structure": item.itinerary_json or {
                    "overview": "",
                    "days": []
                },
                
                "inclusions": item.inclusions or [],
                "exclusions": item.exclusions or [],
                
                "pricing": {
                    "price_displayed": item.estimated_price_usd is not None,
                    "price_per_person_usd": item.estimated_price_usd,
                    "currency": "USD" if item.estimated_price_usd else None,
                    "price_notes": ""
                },
                
                "assumptions_and_flexibility": {
                    "dates_flexible": True,
                    "accommodation_changeable": True,
                    "activities_changeable": True,
                    "private_tour": item.group_type == 'Private'
                },
                
                "realistic_customer_question": item.generated_instruction,
                
                "data_quality_tags": {
                    "structured": True,
                    "marketing_language": "medium",
                    "operational_detail_level": "medium",
                    "source_reliability": "high"
                }
            }
            records.append(training_record)
    
    # Generate file content
    if format == 'jsonl':
        content = '\n'.join(json.dumps(r, ensure_ascii=False, cls=DecimalEncoder) for r in records)
        file_name = f"training_data_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    else:
        content = json.dumps(records, indent=2, ensure_ascii=False, cls=DecimalEncoder)
        file_name = f"training_data_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Create export record
    export = TrainingExport.objects.create(
        exported_by=user,
        file_name=file_name,
        record_count=len(records),
        export_format=format,
    )
    export.file_path.save(file_name, ContentFile(content.encode('utf-8')))
    
    return content, len(records), file_name
