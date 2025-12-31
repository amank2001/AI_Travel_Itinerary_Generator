from .vector_store import vector_store
from typing import List, Dict, Any
import json, logging

logger = logging.getLogger(__name__)

class RAGItineraryEnhancer:
    """
    Enhances itinerary generation with RAG-based recommendations
    """
    
    def __init__(self):
        self.vector_store = vector_store
    
    def get_context_for_itinerary(
        self,
        destination: str,
        travel_style: str,
        interests: List[str],
        budget: str,
        duration: int
    ) -> Dict[str, Any]:
        """
        Get comprehensive context from vector store for itinerary generation
        
        Args:
            destination: Destination name
            travel_style: Travel style (adventure, relaxation, cultural, etc.)
            interests: List of interests
            budget: Budget level (low, medium, high)
            duration: Number of days
            
        Returns:
            Dictionary with relevant context for AI generation
        """
        try:
            logger.info(f"Fetching RAG context for {destination}")
            
            dest_query = f"{destination} travel destination information"
            destination_info = self.vector_store.search_destinations(
                query=dest_query,
                n_results=1
            )
            
            activities_context = {}
            for interest in interests:
                query = f"{interest} activities in {destination} for {travel_style} travelers"
                activities = self.vector_store.search_activities(
                    query=query,
                    destination=destination,
                    n_results=10
                )
                activities_context[interest] = activities
            
            experience_query = f"authentic local experiences hidden gems {destination} {travel_style}"
            local_experiences = self.vector_store.search_local_experiences(
                query=experience_query,
                destination=destination,
                n_results=15
            )
            
            tips_query = f"travel tips advice for {destination}"
            travel_tips = self.vector_store.search_travel_tips(
                query=tips_query,
                n_results=5
            )
            
            activities_per_day = self._calculate_activities_per_day(travel_style)
            
            context = {
                'destination_info': destination_info[0] if destination_info else None,
                'activities_by_interest': activities_context,
                'local_experiences': local_experiences,
                'travel_tips': travel_tips,
                'recommended_activities_per_day': activities_per_day,
                'total_activities_found': sum(len(acts) for acts in activities_context.values()),
                'total_experiences_found': len(local_experiences)
            }
            
            logger.info(f"Retrieved {context['total_activities_found']} activities and {context['total_experiences_found']} experiences")
            return context
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {str(e)}")
            return {
                'destination_info': None,
                'activities_by_interest': {},
                'local_experiences': [],
                'travel_tips': [],
                'recommended_activities_per_day': 3
            }
    
    def _calculate_activities_per_day(self, travel_style: str) -> int:
        """Calculate recommended activities per day based on travel style"""
        style_mapping = {
            'adventure': 4,
            'cultural': 4,
            'relaxation': 2,
            'romantic': 3,
            'family': 3,
            'budget': 3,
            'luxury': 3,
            'food_tour': 4
        }
        return style_mapping.get(travel_style, 3)
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format RAG context into a prompt-friendly string
        
        Args:
            context: Context dictionary from get_context_for_itinerary
            
        Returns:
            Formatted string for AI prompt
        """
        try:
            prompt_context = []
            
            if context.get('destination_info'):
                dest = context['destination_info']['metadata']
                prompt_context.append(f"DESTINATION INFORMATION:")
                prompt_context.append(f"- {dest.get('name')}, {dest.get('country')}")
                prompt_context.append(f"- Best time: {dest.get('best_time')}")
                
                characteristics = json.loads(dest.get('characteristics', '[]'))
                if characteristics:
                    prompt_context.append(f"- Characteristics: {', '.join(characteristics)}")
                prompt_context.append("")
                
            if context.get('activities_by_interest'):
                prompt_context.append("RECOMMENDED ACTIVITIES:")
                for interest, activities in context['activities_by_interest'].items():
                    if activities:
                        prompt_context.append(f"\n{interest.upper()} Activities:")
                        for i, act in enumerate(activities[:5], 1):  # Top 5 per interest
                            meta = act['metadata']
                            prompt_context.append(
                                f"  {i}. {meta.get('name')} - {meta.get('category')} "
                                f"({meta.get('duration', 'N/A')})"
                            )
                prompt_context.append("")
            
            if context.get('local_experiences'):
                prompt_context.append("LOCAL EXPERIENCES & HIDDEN GEMS:")
                for i, exp in enumerate(context['local_experiences'][:10], 1):
                    meta = exp['metadata']
                    gem_marker = "🌟 " if meta.get('hidden_gem') else ""
                    prompt_context.append(
                        f"  {i}. {gem_marker}{meta.get('name')} - {meta.get('category')}"
                    )
                prompt_context.append("")
            
            if context.get('travel_tips'):
                prompt_context.append("RELEVANT TRAVEL TIPS:")
                for i, tip in enumerate(context['travel_tips'], 1):
                    meta = tip['metadata']
                    prompt_context.append(f"  {i}. {meta.get('title')}")
                prompt_context.append("")
            
            return "\n".join(prompt_context)
            
        except Exception as e:
            logger.error(f"Error formatting context: {str(e)}")
            return ""
    
    def enhance_activities_with_rag(
        self,
        activities: List[Dict[str, Any]],
        destination: str
    ) -> List[Dict[str, Any]]:
        """
        Enhance generated activities with additional context from RAG
        
        Args:
            activities: List of generated activities
            destination: Destination name
            
        Returns:
            Enhanced activities with additional tips and insights
        """
        try:
            enhanced = []
            
            for activity in activities:
                activity_name = activity.get('name', '')
                activity_type = activity.get('activity_type', '')
                
                # Search for similar activities in vector store
                query = f"{activity_name} {activity_type} {destination}"
                similar = self.vector_store.search_activities(
                    query=query,
                    destination=destination,
                    n_results=1
                )
                
                if similar:
                    similar_meta = similar[0]['metadata']
                    if not activity.get('tips'):
                        activity['tips'] = f"Insider tip: {similar[0].get('content', '')[:200]}"
                
                enhanced.append(activity)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing activities: {str(e)}")
            return activities
    
    def get_similar_destinations(
        self,
        destination: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find destinations similar to the given one
        
        Args:
            destination: Destination name
            n_results: Number of similar destinations
            
        Returns:
            List of similar destinations
        """
        try:
            similar = self.vector_store.find_similar_destinations(
                destination_name=destination,
                n_results=n_results + 1  
            )
            
            filtered = [
                dest for dest in similar 
                if dest['metadata'].get('name', '').lower() != destination.lower()
            ]
            
            return filtered[:n_results]
            
        except Exception as e:
            logger.error(f"Error finding similar destinations: {str(e)}")
            return []
    
    def get_personalized_recommendations(
        self,
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get personalized recommendations based on user preferences
        
        Args:
            user_preferences: Dictionary with user preferences
                {
                    'travel_style': str,
                    'interests': List[str],
                    'budget': str,
                    'destination': str (optional)
                }
                
        Returns:
            Dictionary with personalized recommendations
        """
        try:
            travel_style = user_preferences.get('travel_style', 'cultural')
            interests = user_preferences.get('interests', [])
            budget = user_preferences.get('budget', 'medium')
            destination = user_preferences.get('destination')
            
            recommendations = self.vector_store.get_recommendations_for_preferences(
                travel_style=travel_style,
                interests=interests,
                budget=budget,
                destination=destination
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {str(e)}")
            return {}


rag_enhancer = RAGItineraryEnhancer()

def get_rag_enhanced_prompt(
    destination: str,
    travel_style: str,
    interests: List[str],
    budget: str,
    duration: int
) -> str:
    """
    Helper function to get RAG-enhanced prompt for itinerary generation
    Use this in your tasks.py when generating itineraries
    
    Example usage in tasks.py:
    
    from apps.ai_engine.rag_integration import get_rag_enhanced_prompt
    
    rag_context = get_rag_enhanced_prompt(
        destination=trip_request.destination,
        travel_style=trip_request.travel_style,
        interests=trip_request.interests,
        budget='medium',
        duration=trip_request.duration
    )
    
    # Add this to your AI prompt
    full_prompt = f'''
    {your_existing_prompt}
    
    RELEVANT CONTEXT FROM KNOWLEDGE BASE:
    {rag_context}
    
    Use the above context to create an authentic, well-informed itinerary.
    '''
    """
    try:
        # Get context
        context = rag_enhancer.get_context_for_itinerary(
            destination=destination,
            travel_style=travel_style,
            interests=interests,
            budget=budget,
            duration=duration
        )
        
        # Format for prompt
        formatted_context = rag_enhancer.format_context_for_prompt(context)
        
        return formatted_context
        
    except Exception as e:
        logger.error(f"Error getting RAG enhanced prompt: {str(e)}")
        return ""
    

def integrate_rag_with_ai_prompt(trip_request) -> str:
    """
    function showing how to integrate RAG with your AI prompts
    """
    
    # Get RAG context
    rag_context = get_rag_enhanced_prompt(
        destination=trip_request.destination,
        travel_style=trip_request.travel_style,
        interests=trip_request.interests,
        budget='medium',  # Or map from trip_request.budget
        duration=trip_request.duration
    )
    
    # Your existing prompt template
    base_prompt = f"""
    Create a {trip_request.duration}-day itinerary for {trip_request.destination}.
    Travel style: {trip_request.travel_style}
    Interests: {', '.join(trip_request.interests)}
    Budget: {trip_request.budget} {trip_request.currency}
    """
    
    # Enhanced prompt with RAG context
    enhanced_prompt = f"""
    {base_prompt}
    
    RELEVANT CONTEXT FROM KNOWLEDGE BASE:
    {rag_context}
    
    INSTRUCTIONS:
    - Use the recommended activities and local experiences from the knowledge base
    - Incorporate the hidden gems and insider tips
    - Follow the travel tips provided
    - Ensure authenticity by referencing local culture and customs
    - Create a balanced itinerary with {rag_enhancer._calculate_activities_per_day(trip_request.travel_style)} activities per day
    
    Generate a detailed, day-by-day itinerary in JSON format.
    """
    
    return enhanced_prompt