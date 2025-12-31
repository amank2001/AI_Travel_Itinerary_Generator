from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.output_parsers import JsonOutputParser
from django.conf import settings
from .rag_integration import get_rag_enhanced_prompt
import json, logging, re

from .prompts import DESTINATION_ANALYSIS_PROMPT, ITINERARY_GENERATION_PROMPT, LOCAL_EXPERIENCES_PROMPT, BUDGET_OPTIMIZATION_PROMPT,CHAT_REFINEMENT_PROMPT, WEATHER_ADJUSTMENT_PROMPT

logger = logging.getLogger(__name__)

class TravelPlannerChains:
    """Main class for managing LangChain workflows for travel planning"""
    
    def __init__(self, model_name="gpt-4o-mini", temperature=0.7):
        """
        Initialize the chains with specified model
        
        Args:
            model_name: OpenAI model to use
            temperature: Temperature for generation (0.0-1.0)
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.llm_factual = ChatOpenAI(
            model=model_name,
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.json_parser = JsonOutputParser()
        
    
    def analyze_destination(self, destination, travel_style, duration, season):
        """
        Analyze destination to gather context for planning
        
        Args:
            destination: Destination name
            travel_style: Type of travel
            duration: Number of days
            season: Season/month of travel
            
        Returns:
            dict: Destination analysis
        """
        try:
            chain = LLMChain(
                llm=self.llm_factual,
                prompt=DESTINATION_ANALYSIS_PROMPT,
                output_parser=self.json_parser
            )
            
            result = chain.run(
                destination=destination,
                travel_style=travel_style,
                duration=duration,
                season=season
            )
            
            return self._parse_json_output(result)
            
        except Exception as e:
            logger.error(f"Destination analysis failed: {str(e)}")
            return self._get_default_destination_analysis()
        
        
    def generate_itinerary(self, trip_data):
        """
        Generate complete itinerary based on trip requirements
        
        Args:
            trip_data: Dictionary containing all trip parameters
            
        Returns:
            dict: Complete itinerary
        """
        try:
            # Prepare inputs
            interests_str = ", ".join(trip_data.get('interests', ['general sightseeing']))
            dietary_str = ", ".join(trip_data.get('dietary_restrictions', ['none']))
            
            weather_summary = self._format_weather_summary(trip_data.get('weather_data', {}))
            
            attractions = self._format_attractions(trip_data.get('attractions', []))
           
            #modified
            total_budget = float(trip_data['budget'])
            duration = int(trip_data['duration'])
            daily_budget = total_budget / duration
            
            #modified
            rag_context = ""
            try:
                rag_context = get_rag_enhanced_prompt(
                    destination=trip_data['destination'],
                    travel_style=trip_data['travel_style'],
                    interests=trip_data.get('interests', []),
                    budget='medium',  # Map from actual budget
                    duration=duration
                )
            except Exception as e:
                logger.warning(f"RAG context not available: {str(e)}")
            
            chain = LLMChain(
                llm=self.llm,
                prompt=ITINERARY_GENERATION_PROMPT,
                output_parser=self.json_parser
            )
            
            result = chain.run(
                destination=trip_data['destination'],
                duration=trip_data['duration'],
                budget=trip_data['budget'],
                currency=trip_data['currency'],
                travel_style=trip_data['travel_style'],
                group_size=trip_data['group_size'],
                interests=interests_str,
                dietary_restrictions=dietary_str,
                weather_summary=weather_summary,
                attractions=attractions,
                accommodation_preference=trip_data.get('accommodation_preference', 'hotel'),
                daily_budget=float(trip_data['budget']) / trip_data['duration'],
                rag_context=rag_context
            )
            
            #modified
            parsed = self._parse_json_output(result)
            parsed = self._validate_budget_realism(parsed, total_budget, duration, trip_data['currency'])
            return parsed
            
        except Exception as e:
            logger.error(f"Itinerary generation failed: {str(e)}")
            raise
        
    
    def curate_local_experiences(self, destination, travel_style, interests, duration):
        """
        Generate local experiences and hidden gems
        
        Args:
            destination: Destination name
            travel_style: Travel style preference
            interests: List of interests
            duration: Trip duration
            
        Returns:
            list: Local experiences
        """
        try:
            interests_str = ", ".join(interests) if interests else "varied experiences"
            
            chain = LLMChain(
                llm=self.llm,
                prompt=LOCAL_EXPERIENCES_PROMPT
            )
            
            result = chain.run(
                destination=destination,
                travel_style=travel_style,
                interests=interests_str,
                duration=duration
            )
            
            logger.info(f"Raw local experiences response type: {type(result)}")
            logger.debug(f"Raw response (first 300 chars): {str(result)[:300]}")
            
            experiences = self._parse_json_output_robust(result)
            
            logger.info(f"Parsed experiences type: {type(experiences)}")
            
            if isinstance(experiences, dict):
                # Try different possible keys
                possible_keys = [
                    'experiences', 
                    'local_experiences', 
                    'hidden_gems',
                    'recommendations',
                    'items',
                    'results'
                ]
                
                for key in possible_keys:
                    if key in experiences:
                        logger.info(f"Found experiences under key: {key}")
                        experiences = experiences[key]
                        break
                
                # If still a dict, try to extract any list value
                if isinstance(experiences, dict):
                    # Look for the first list value in the dict
                    for key, value in experiences.items():
                        if isinstance(value, list):
                            logger.info(f"Found list under key: {key}")
                            experiences = value
                            break
                
                # If still a dict after all attempts, log structure and return empty
                if isinstance(experiences, dict):
                    logger.warning(f"Response is dict with keys: {experiences.keys()}")
                    logger.warning(f"Dict structure: {json.dumps(experiences, indent=2)[:500]}")
                    return []
            
            if not isinstance(experiences, list):
                logger.warning(f"Local experiences not a list after processing: {type(experiences)}")
                return []
            
            logger.info(f"Successfully curated {len(experiences)} local experiences")
            return experiences
            
        except Exception as e:
            logger.error(f"Local experiences curation failed: {str(e)}")
            return []
        
        
    def optimize_budget(self, itinerary, budget, currency, current_cost):
        """
        Optimize itinerary to fit budget constraints
        
        Args:
            itinerary: Current itinerary
            budget: Target budget
            currency: Currency code
            current_cost: Current total cost
            
        Returns:
            dict: Budget optimization recommendations
        """
        try:
            #modified
            variance_percentage = ((current_cost - budget) / budget) * 100
            
            chain = LLMChain(
                llm=self.llm,
                prompt=BUDGET_OPTIMIZATION_PROMPT,
                # output_parser=self.json_parser
            )
            
            result = chain.run(
                itinerary=json.dumps(itinerary, indent=2),
                budget=budget,
                currency=currency,
                current_cost=current_cost,
                variance_percentage=variance_percentage #modified
            )
            
            return self._parse_json_output_robust(result)
            
        except Exception as e:
            logger.error(f"Budget optimization failed: {str(e)}")
            return {
                'status': 'error',
                'adjustments': [],
                'alternative_activities': [],
                'budget_tips': []
            }
            
    
    def refine_with_chat(self, itinerary_summary, user_message):
        """
        Process conversational refinement requests
        
        Args:
            itinerary_summary: Summary of current itinerary
            user_message: User's modification request
            
        Returns:
            dict: Refinement response
        """
        try:
        # Ensure itinerary_summary is a string for the prompt
            if isinstance(itinerary_summary, dict):
                itinerary_str = json.dumps(itinerary_summary, indent=2)
            else:
                itinerary_str = str(itinerary_summary)
            
            chain = LLMChain(
                llm=self.llm,
                prompt=CHAT_REFINEMENT_PROMPT
            )
            
            result = chain.run(
                itinerary_summary=itinerary_str,
                user_message=user_message
            )
            
            parsed_result = self._parse_json_output_robust(result)
            
            if parsed_result and isinstance(parsed_result, dict):
                # Ensure all required fields exist
                structured_result = {
                    'understanding': parsed_result.get('understanding', 'Processing your request...'),
                    'changes': parsed_result.get('changes', []),
                    'updated_sections': parsed_result.get('updated_sections', {}),
                    'budget_impact': parsed_result.get('budget_impact', 'No significant budget impact'),
                    'response_message': parsed_result.get('response_message', 'I understand your request and will make the changes.')
                }
                
                logger.info(f"Refinement understanding: {structured_result['understanding']}")
                logger.info(f"Changes to apply: {structured_result['changes']}")
                logger.info(f"Updated sections keys: {list(structured_result['updated_sections'].keys())}")
                
                return structured_result
            else:
                logger.warning("AI returned non-dict result, using fallback")
                return self._create_fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"Chat refinement failed: {str(e)}", exc_info=True)
            return self._create_fallback_response(user_message, error=str(e))
        
        
    def _create_fallback_response(self, user_message, error=None):
        """Create a fallback response when AI processing fails"""
        return {
            'understanding': f'Unable to process request: {user_message[:100]}...',
            'changes': [],
            'updated_sections': {},
            'budget_impact': 'Unable to determine',
            'response_message': f'Sorry, I had trouble understanding that request. {"Error: " + error if error else "Could you rephrase?"}'
        }

    
    def adjust_for_weather(self, itinerary_summary, weather_forecast):
        """
        Adjust itinerary based on weather conditions
        
        Args:
            itinerary_summary: Summary of itinerary
            weather_forecast: Weather data
            
        Returns:
            dict: Weather-adjusted recommendations
        """
        try:
            chain = LLMChain(
                llm=self.llm,
                prompt=WEATHER_ADJUSTMENT_PROMPT,
                # output_parser=self.json_parser
            )
            
            result = chain.run(
                itinerary_summary=itinerary_summary,
                weather_forecast=json.dumps(weather_forecast)
            )
            
            return self._parse_json_output_robust(result)
            
        except Exception as e:
            logger.error(f"Weather adjustment failed: {str(e)}")
            return {}
        
    # Helper methods
    
    def _parse_json_output(self, output):
        """Parse JSON output, handling various formats"""
        if isinstance(output, dict):
            return output
        
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            try:
                if '```json' in output:
                    json_str = output.split('```json')[1].split('```')[0].strip()
                    return json.loads(json_str)
                elif '```' in output:
                    json_str = output.split('```')[1].split('```')[0].strip()
                    return json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass
        
        logger.error(f"Failed to parse JSON output: {output[:200]}")
        return {}
    
    def _parse_json_output_robust(self, output):
        """
        Method 1: Robust JSON parsing that handles multiple formats
        """
        if isinstance(output, dict):
            return output
        
        if not isinstance(output, str):
            logger.error(f"Output is not string or dict: {type(output)}")
            return {}
        
        # Method 1: Try direct JSON parse
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract from markdown code blocks
        patterns = [
            r'```json\s*\n(.*?)\n```',  # ```json ... ```
            r'```\s*\n(.*?)\n```',       # ``` ... ```
            r'\{[\s\S]*\}',              # Any JSON object
            r'\[[\s\S]*\]'               # Any JSON array
        ]
        
        for pattern in patterns:
            try:
                matches = re.findall(pattern, output, re.DOTALL)
                if matches:
                    json_str = matches[0] if isinstance(matches[0], str) else matches[0]
                    return json.loads(json_str.strip())
            except (json.JSONDecodeError, IndexError):
                continue
        
        # Method 3: Clean and try again
        try:
            cleaned = output.replace('```json', '').replace('```', '').strip()
            start = cleaned.find('{') if '{' in cleaned else cleaned.find('[')
            end = cleaned.rfind('}') + 1 if '}' in cleaned else cleaned.rfind(']') + 1
            
            if start >= 0 and end > start:
                json_str = cleaned[start:end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        logger.error(f"Failed to parse JSON after all attempts. Output preview: {output[:300]}")
        return {}
    
    
    def _validate_budget_realism(self, itinerary, total_budget, duration, currency):
        """
        Method 2: Validate and adjust budget to be realistic
        """
        try:
            calculated_cost = 0
            days = itinerary.get('days', [])
            
            for day in days:
                for activity in day.get('activities', []):
                    cost = activity.get('cost', 0)
                    if isinstance(cost, (int, float)):
                        calculated_cost += cost
            
            # estimate (30-40% of budget)
            accommodation_cost = total_budget * 0.35
            
            # estimate (25-30% of budget)
            food_cost = total_budget * 0.25
            
            total_estimated = calculated_cost + accommodation_cost + food_cost
            
            if calculated_cost < total_budget * 0.2:  # Less than 20% of budget
                logger.warning(f"Calculated cost too low: {calculated_cost} vs budget: {total_budget}")
                
                scale_factor = (total_budget * 0.4) / max(calculated_cost, 1)
                
                for day in days:
                    for activity in day.get('activities', []):
                        if 'cost' in activity:
                            old_cost = activity['cost']
                            activity['cost'] = round(old_cost * scale_factor, 2)
            
            final_cost = 0
            for day in days:
                for activity in day.get('activities', []):
                    final_cost += activity.get('cost', 0)
            
            itinerary['total_estimated_cost'] = round(final_cost + accommodation_cost + food_cost, 2)
            itinerary['cost_breakdown'] = {
                'activities': round(final_cost, 2),
                'accommodation': round(accommodation_cost, 2),
                'food': round(food_cost, 2),
                'miscellaneous': round(total_budget * 0.1, 2)
            }
            
            logger.info(f"Budget validation: {itinerary['total_estimated_cost']} {currency} (target: {total_budget})")
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Budget validation failed: {str(e)}")
            return itinerary
    
    
    def _is_day_unchanged(self, original_day, regenerated_day):
        """
        Method 3: Check if regenerated day is actually different
        """
        try:
            original_activities = original_day.get('activities', [])
            new_activities = regenerated_day.get('activities', [])
            
            if len(original_activities) == 0 or len(new_activities) == 0:
                return True
            
            original_names = set(a.get('activity', '') for a in original_activities)
            new_names = set(a.get('activity', '') for a in new_activities)
            
            if len(original_names) == 0:
                return True    
            
            # If 80% or more activities are the same, consider it unchanged
            same_count = len(original_names & new_names)
            similarity = same_count / len(original_names)
            
            return similarity > 0.8
            
        except Exception as e:
            logger.error(f"Error checking day changes: {str(e)}")
            return False
    
    
    def _force_day_modification(self, original_day, modification_request, destination, daily_budget, currency):
        """
        Method 3: Force modification when regeneration doesn't change enough
        """
        logger.info("Forcing day modification with fallback strategy")
        
        modified_day = original_day.copy()
        activities = modified_day.get('activities', [])
        
        request_lower = modification_request.lower()
        
        # Replace some activities with adventure-themed ones
        if 'adventure' in request_lower or 'active' in request_lower or 'outdoor' in request_lower:
            adventure_activities = [
                {"time": "09:00", "activity": "Hiking Trail", "location": f"{destination}", "category": "adventure", 
                "description": "Scenic hiking with beautiful views", "duration": 180, "cost": 15.00, 
                "tips": "Bring water and sunscreen"},
                {"time": "14:00", "activity": "Water Sports", "location": f"{destination}", "category": "adventure",
                "description": "Kayaking or paddleboarding", "duration": 120, "cost": 30.00,
                "tips": "Book in advance"},
                {"time": "17:00", "activity": "Rock Climbing", "location": f"{destination}", "category": "adventure",
                "description": "Indoor or outdoor climbing experience", "duration": 120, "cost": 35.00,
                "tips": "Equipment provided"}
            ]
        
            if len(activities) >= 2:
                activities[1] = adventure_activities[0]
                if len(activities) >= 3:
                    activities[2] = adventure_activities[1]
                    
        # Add food-focused activities
        elif 'food' in request_lower or 'culinary' in request_lower or 'eat' in request_lower:
            food_activities = [
                {"time": "10:00", "activity": "Local Food Market Tour", "location": f"{destination}", "category": "food",
                "description": "Explore local markets and taste street food", "duration": 150, "cost": 25.00,
                "tips": "Come hungry!"},
                {"time": "13:00", "activity": "Cooking Class", "location": f"{destination}", "category": "food",
                "description": "Learn to cook local dishes", "duration": 180, "cost": 45.00,
                "tips": "Book ahead"},
                {"time": "19:00", "activity": "Fine Dining Experience", "location": f"{destination}", "category": "food",
                "description": "Upscale restaurant with local cuisine", "duration": 120, "cost": 60.00,
                "tips": "Reservation required"}
            ]
            if len(activities) >= 2:
                activities[1] = food_activities[0]
                if len(activities) >= 3:
                    activities.append(food_activities[1])
                    
        # Add cultural activities
        elif 'cultural' in request_lower or 'museum' in request_lower or 'history' in request_lower:
            cultural_activities = [
                {"time": "09:00", "activity": "National Museum", "location": f"{destination}", "category": "cultural",
                "description": "Explore local history and art", "duration": 180, "cost": 15.00,
                "tips": "Get there early"},
                {"time": "14:00", "activity": "Historic Temple Tour", "location": f"{destination}", "category": "cultural",
                "description": "Visit ancient temples", "duration": 150, "cost": 10.00,
                "tips": "Dress modestly"},
                {"time": "17:00", "activity": "Cultural Performance", "location": f"{destination}", "category": "entertainment",
                "description": "Traditional dance or music show", "duration": 90, "cost": 25.00,
                "tips": "Book tickets online"}
            ]
            if len(activities) >= 1:
                activities[0] = cultural_activities[0]
                if len(activities) >= 2:
                    activities[1] = cultural_activities[1]

        # Reduce activities, make it more relaxed
        elif 'relax' in request_lower or 'less' in request_lower or 'slow' in request_lower:
            activities = activities[:2]  
            activities.append({
                "time": "15:00",
                "activity": "Spa and Wellness",
                "location": f"{destination}",
                "category": "relaxation",
                "description": "Relaxing spa treatment",
                "duration": 120,
                "cost": 40.00,
                "tips": "Book massage in advance"
            })
        
        # Generic modification - replace middle activity
        else:
            if len(activities) >= 2:
                activities[1] = {
                    "time": "12:00",
                    "activity": "Local Experience",
                    "location": f"{destination}",
                    "category": "cultural",
                    "description": f"Modified activity based on: {modification_request}",
                    "duration": 120,
                    "cost": 20.00,
                    "tips": "Enjoy the experience!"
                }
    
        modified_day['activities'] = activities
        modified_day['theme'] = f"Modified: {modification_request[:50]}"
        
        logger.info(f"Forced modification complete: {len(activities)} activities")
        return modified_day
        
    
    def _format_day_summary(self, activities):
        """Format activities for display in prompt"""
        summary = []
        for i, act in enumerate(activities, 1):
            summary.append(
                f"{i}. {act.get('time', 'N/A')}: {act.get('activity', 'Unknown')} "
                f"at {act.get('location', 'N/A')} ({act.get('cost', 0)} cost)"
            )
        return "\n".join(summary)
    
    
    def _add_activities_to_day(self, original_day, request, destination, budget, currency):
        """Add more activities to a day"""
        new_day = original_day.copy()
        logger.info(f"Adding activities based on: {request}")
        return new_day
    
    
    def _reduce_activities_in_day(self, original_day):
        """Remove some activities from day"""
        new_day = original_day.copy()
        activities = new_day.get('activities', [])
        if len(activities) > 2:
            # Keep only first 2-3 activities
            new_day['activities'] = activities[:3]
        return new_day
    
    
    def _replace_activities_in_day(self, original_day, request, destination, budget, currency):
        """Replace activities with different ones"""
        return original_day
    
    
    def _modify_activity_types(self, original_day, request, destination):
        """Modify activity categories/types"""
        return original_day
    
    
    def _format_weather_summary(self, weather_data):
        """Format weather data into readable summary"""
        if not weather_data or 'days' not in weather_data:
            return "Weather data unavailable"
        
        summary_parts = []
        for day in weather_data['days'][:7]:
            summary_parts.append(
                f"{day['date']}: {day['condition']}, "
                f"{day['temp_min']}°C-{day['temp_max']}°C"
            )
        
        return "\n".join(summary_parts)
    
    
    def _format_attractions(self, attractions):
        """Format attractions list for prompt"""
        if not attractions:
            return "No specific attractions data available"
        
        formatted = []
        for i, attr in enumerate(attractions[:15], 1):
            formatted.append(
                f"{i}. {attr.get('name', 'Unknown')} "
                f"(Rating: {attr.get('rating', 'N/A')})"
            )
        
        return "\n".join(formatted)
    
    
    def _get_default_destination_analysis(self):
        """Return default analysis when API fails"""
        return {
            'overview': 'Destination analysis unavailable',
            'best_neighborhoods': [],
            'top_attractions': [],
            'transportation': 'Local transportation available',
            'cultural_tips': [],
            'safety_tips': ['Exercise normal precautions'],
            'hidden_gems': [],
            'food_specialties': [],
            'seasonal_notes': []
        }
        
# Sequential chain for complete itinerary generation
class CompleteItineraryPipeline:
    """Pipeline that combines multiple chains for complete itinerary generation"""
    
    def __init__(self):
        self.chains = TravelPlannerChains()
    
    def generate_complete_itinerary(self, trip_request_data, external_data):
        """
        Generate complete itinerary with all components
        
        Args:
            trip_request_data: Trip request parameters
            external_data: Data from external APIs (weather, attractions, etc.)
            
        Returns:
            dict: Complete itinerary with all details
        """
        logger.info(f"Starting itinerary generation for {trip_request_data['destination']}")
        
        # Step 1: Analyze destination (for context)
        # destination_analysis = self.chains.analyze_destination(
        #     trip_request_data['destination'],
        #     trip_request_data['travel_style'],
        #     trip_request_data['duration'],
        #     trip_request_data.get('season', 'current')
        # )
        
        # Step 2: Generate main itinerary
        complete_trip_data = {
            **trip_request_data,
            **external_data
        }
        itinerary = self.chains.generate_itinerary(complete_trip_data)
        
        # Step 3: Generate local experiences
        local_experiences = self.chains.curate_local_experiences(
            trip_request_data['destination'],
            trip_request_data['travel_style'],
            trip_request_data.get('interests', []),
            trip_request_data['duration']
        )
        
        # Step 4: Budget optimization if needed
        total_cost = itinerary.get('total_estimated_cost', 0)
        budget = float(trip_request_data['budget'])
        
        if abs(total_cost - budget) > budget * 0.1:  # More than 10% difference
            optimization = self.chains.optimize_budget(
                itinerary,
                budget,
                trip_request_data['currency'],
                total_cost
            )
            itinerary['budget_optimization'] = optimization
        
        # Combine all results
        complete_itinerary = {
            'itinerary': itinerary,
            'local_experiences': local_experiences,
            'weather_data': external_data.get('weather_data', {}),
            'destination_info': external_data.get('destination_info', {}),
            'total_cost': total_cost,
            'currency': trip_request_data['currency']
        }
        
        logger.info("Itinerary generation completed: {total_cost} {trip_request_data['currency']}")
        return complete_itinerary
    
    
# Convenience functions
def generate_itinerary(trip_data, external_data):
    """Generate complete itinerary"""
    pipeline = CompleteItineraryPipeline()
    return pipeline.generate_complete_itinerary(trip_data, external_data)


def refine_itinerary(itinerary_summary, user_message):
    """Refine itinerary based on user feedback"""
    chains = TravelPlannerChains()
    return chains.refine_with_chat(itinerary_summary, user_message)
