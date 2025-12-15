"""
Utility for generating unique and specific questions about Kilimanjaro routes.
"""
import random
from typing import List, Dict, Optional

class KilimanjaroQuestionGenerator:
    """Generates unique questions about Kilimanjaro routes."""
    
    ROUTE_SPECIFICS = {
        'lemosho': {
            'days': [7, 8],
            'highlights': [
                'Shira Plateau',
                'Barranco Wall',
                'Lava Tower',
                'Western Breach',
                'Mweka descent'
            ],
            'unique_aspects': [
                'best for wildlife spotting',
                'most scenic approach',
                'gradual ascent profile',
                'best for photography',
                'most diverse ecosystems'
            ]
        },
        'machame': {
            'days': [6, 7],
            'highlights': [
                'Shira Plateau',
                'Barranco Wall',
                'Lava Tower',
                'Arrow Glacier',
                'Southern Circuit'
            ],
            'unique_aspects': [
                'most popular route',
                '"Whiskey Route" nickname',
                'steeper ascent',
                'better for experienced hikers',
                'more challenging terrain'
            ]
        },
        'northern': {
            'days': [9, 10],
            'highlights': [
                'Shira Plateau',
                'Moir Hut',
                'Northern Circuit',
                'Pofu Camp',
                'Rongai Route'
            ],
            'unique_aspects': [
                'longest route',
                'best acclimatization',
                'most remote experience',
                'least crowded',
                'best summit success rate'
            ]
        },
        'rongai': {
            'days': [6, 7],
            'highlights': [
                'First Cave',
                'Kikelewa Caves',
                'Mawenzi Tarn',
                'School Hut',
                'Gillman\'s Point'
            ],
            'unique_aspects': [
                'only northern approach',
                'drier climate',
                'gentler gradient',
                'better for rainy season',
                'less crowded'
            ]
        },
        'marangu': {
            'days': [5, 6],
            'highlights': [
                'Mandara Hut',
                'Horombo Hut',
                'Kibo Hut',
                'Zebra Rocks',
                'Mawenzi Hut'
            ],
            'unique_aspects': [
                'only route with hut accommodation',
                'shortest duration',
                '"Coca-Cola" route',
                'easiest technical difficulty',
                'most direct route'
            ]
        },
        'umbwe': {
            'days': [5, 6],
            'highlights': [
                'Umbwe Caves',
                'Barranco Camp',
                'Arrow Glacier',
                'Western Breach',
                'Lava Tower'
            ],
            'unique_aspects': [
                'most challenging route',
                'steepest ascent',
                'least crowded',
                'most technical',
                'for experienced climbers only'
            ]
        }
    }
    
    @classmethod
    def generate_route_questions(cls, route_name: str, count: int = 3) -> List[str]:
        """Generate unique questions about a specific route."""
        route = cls.ROUTE_SPECIFICS.get(route_name.lower())
        if not route:
            return []
            
        questions = []
        used_templates = set()
        
        templates = [
            "What makes the {route} Route's {highlight} particularly special compared to other routes?",
            "How does the {route} Route's {aspect} affect the overall climbing experience?",
            "For someone considering the {route} Route, what should they know about the {highlight} section?",
            "What training would you recommend specifically for the {route} Route's {aspect}?",
            "How does the {route} Route's {day}-day itinerary optimize for altitude acclimatization?",
            "What wildlife might I expect to see on the {route} Route near {highlight}?",
            "How does the {route} Route's {aspect} impact packing requirements?",
            "What's the most challenging part of the {route} Route's {highlight} section?",
            "How does the {route} Route's {aspect} compare to other routes in terms of difficulty?",
            "What photography opportunities does the {route} Route offer at {highlight}?"
        ]
        
        while len(questions) < count and templates:
            # Select a random template that hasn't been used yet
            template = random.choice([t for t in templates if t not in used_templates])
            used_templates.add(template)
            
            # Fill in the placeholders
            if '{highlight}' in template:
                highlight = random.choice(route['highlights'])
                question = template.format(
                    route=route_name.title(),
                    highlight=highlight
                )
            elif '{aspect}' in template:
                aspect = random.choice(route['unique_aspects'])
                question = template.format(
                    route=route_name.title(),
                    aspect=aspect
                )
            elif '{day}' in template:
                day = random.choice(route['days'])
                question = template.format(
                    route=route_name.title(),
                    day=day
                )
            else:
                continue
                
            questions.append(question)
        
        return questions
    
    @classmethod
    def generate_comparison_questions(cls, route1: str, route2: str, count: int = 3) -> List[str]:
        """Generate comparison questions between two routes."""
        questions = []
        
        templates = [
            "How does the acclimatization profile compare between the {route1} and {route2} routes?",
            "What are the key differences in scenery between the {route1} and {route2} routes?",
            "For someone with {fitness} fitness level, which would be better between {route1} and {route2} and why?",
            "How do the success rates compare between the {route1} and {route2} routes, and what factors contribute to this?",
            "What type of hiker would prefer the {route1} route over the {route2} route?",
            "How do the camping conditions differ between {route1} and {route2}?",
            "Which route offers better opportunities for {interest}, {route1} or {route2}?",
            "How does the crowd level compare between the {route1} and {route2} routes during {season}?",
            "What are the main advantages of choosing {route1} over {route2} for someone with {experience}?",
            "How do the physical demands differ between the {route1} and {route2} routes?"
        ]
        
        fitness_levels = ["average", "above average", "excellent", "beginner"]
        interests = ["wildlife photography", "landscape photography", "bird watching", "stargazing"]
        seasons = ["peak season (July-October)", "shoulder season (January-March)", "rainy season (April-June)"]
        experience_levels = ["no high-altitude experience", "some hiking experience", "extensive trekking experience"]
        
        used_templates = set()
        
        while len(questions) < count and templates:
            template = random.choice([t for t in templates if t not in used_templates])
            used_templates.add(template)
            
            if '{fitness}' in template:
                question = template.format(
                    route1=route1.title(),
                    route2=route2.title(),
                    fitness=random.choice(fitness_levels)
                )
            elif '{interest}' in template:
                question = template.format(
                    route1=route1.title(),
                    route2=route2.title(),
                    interest=random.choice(interests)
                )
            elif '{season}' in template:
                question = template.format(
                    route1=route1.title(),
                    route2=route2.title(),
                    season=random.choice(seasons)
                )
            elif '{experience}' in template:
                question = template.format(
                    route1=route1.title(),
                    route2=route2.title(),
                    experience=random.choice(experience_levels)
                )
            else:
                question = template.format(
                    route1=route1.title(),
                    route2=route2.title()
                )
                
            questions.append(question)
        
        return questions

# Example usage:
if __name__ == "__main__":
    # Generate questions about a specific route
    print("\nLemosho Route Questions:")
    for q in KilimanjaroQuestionGenerator.generate_route_questions('lemosho', 5):
        print(f"- {q}")
    
    # Generate comparison questions
    print("\nComparison Questions (Lemosho vs Machame):")
    for q in KilimanjaroQuestionGenerator.generate_comparison_questions('lemosho', 'machame', 5):
        print(f"- {q}")
