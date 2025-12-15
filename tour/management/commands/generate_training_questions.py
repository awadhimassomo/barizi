from django.core.management.base import BaseCommand
from tour.utils.question_generator import KilimanjaroQuestionGenerator
from tour.models import ProcessedItinerary
import json
from pathlib import Path
from django.conf import settings
from django.utils import timezone

class Command(BaseCommand):
    help = 'Generate unique training questions for Kilimanjaro routes'

    def handle(self, *args, **options):
        # Get or create a sample itinerary for each route
        routes = ['lemosho', 'machame', 'northern', 'rongai', 'marangu', 'umbwe']
        
        training_data = []
        
        # Generate questions for each route
        for route in routes:
            # Get a sample itinerary for this route
            itinerary = ProcessedItinerary.objects.filter(
                status='approved',
                training_json__icontains=f'"route": "{route}"'
            ).first()
            
            if not itinerary:
                self.stdout.write(self.style.WARNING(f'No approved itinerary found for {route} route'))
                continue
                
            try:
                # Generate unique questions
                questions = KilimanjaroQuestionGenerator.generate_route_questions(route, count=5)
                
                for question in questions:
                    training_data.append({
                        'instruction': question,
                        'response': self._generate_response(route, question, itinerary.training_json),
                        'metadata': {
                            'route': route,
                            'question_type': 'route_specific',
                            'generated_at': timezone.now().isoformat()
                        }
                    })
                    
                # Generate comparison questions
                other_routes = [r for r in routes if r != route]
                for other_route in other_routes[:2]:  # Compare with 2 other routes
                    comp_questions = KilimanjaroQuestionGenerator.generate_comparison_questions(
                        route, other_route, count=3
                    )
                    for question in comp_questions:
                        training_data.append({
                            'instruction': question,
                            'response': self._generate_comparison_response(route, other_route, question),
                            'metadata': {
                                'route': f'{route}_vs_{other_route}',
                                'question_type': 'comparison',
                                'generated_at': timezone.now().isoformat()
                            }
                        })
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {route}: {str(e)}'))
                continue
                
        # Save to file
        if training_data:
            output_dir = Path(settings.MEDIA_ROOT) / 'training_questions'
            output_dir.mkdir(exist_ok=True)
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_dir / f'unique_questions_{timestamp}.jsonl'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in training_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully generated {len(training_data)} unique questions in {output_file}')
            )
        else:
            self.stdout.write(self.style.WARNING('No training data was generated'))
    
    def _generate_response(self, route: str, question: str, itinerary_data: dict) -> str:
        """Generate a response for a route-specific question."""
        # In a real implementation, you would use your AI model to generate a response
        # For now, we'll return a placeholder
        return f"This is a detailed response about the {route.title()} Route in relation to: {question}"
    
    def _generate_comparison_response(self, route1: str, route2: str, question: str) -> str:
        """Generate a response for a comparison question."""
        # In a real implementation, you would use your AI model to generate a response
        return f"This is a detailed comparison between {route1.title()} and {route2.title()} routes regarding: {question}"
