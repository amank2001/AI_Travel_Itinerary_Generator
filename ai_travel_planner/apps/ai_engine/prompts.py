from langchain.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


TRAVEL_PLANNER_SYSTEM = """
You are an expert travel planner with extensive knowledge of destinations worldwide. 
You create personalized, realistic, and well-structured travel itineraries that balance activities, rest, and local experiences.

Your planning principles:
1. Consider travel time between locations to avoid rushed schedules
2. Mix popular attractions with hidden gems and local experiences
3. Account for opening hours, best visiting times, and seasonal factors
4. Respect the traveler's budget and preferences
5. Include practical tips and insider knowledge
6. Balance different types of activities (cultural, adventure, relaxation, food)
7. Leave some flexibility for spontaneous discoveries

Always provide specific, actionable recommendations with realistic time estimates.

IMPORTANT:
- Output MUST be valid JSON
- Do NOT use markdown
- Do NOT use commas in numbers
- Numbers must be raw (e.g., 1000.5 not 1,000.5)
- Output JSON only, no explanations
"""

DESTINATION_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(TRAVEL_PLANNER_SYSTEM),
    HumanMessagePromptTemplate.from_template("""Analyze this destination for travel planning:

Destination: {destination}
Travel Style: {travel_style}
Duration: {duration} days
Season/Month: {season}

Provide a comprehensive analysis including:
1. Overview of the destination
2. Best neighborhoods to stay in
3. Must-see attractions (top 10)
4. Local transportation options
5. Cultural considerations and etiquette
6. Safety tips
7. Best times to visit attractions
8. Hidden gems and local favorites
9. Food specialties to try
10. Seasonal considerations for this time of year

Format your response as a structured JSON object.""")
])


ITINERARY_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(TRAVEL_PLANNER_SYSTEM),
    HumanMessagePromptTemplate.from_template("""Create a detailed {duration}-day itinerary for {destination}.

Trip Details:
- Destination: {destination}
- Duration: {duration} days
- Budget: {budget} {currency} total
- Travel Style: {travel_style}
- Group Size: {group_size}
- Interests: {interests}
- Dietary Restrictions: {dietary_restrictions}

Context Information:
- Weather Forecast: {weather_summary}
- Top Attractions: {attractions}
- Accommodation Preference: {accommodation_preference}

Requirements:
1. Create a day-by-day itinerary with specific activities
2. Include morning, afternoon, and evening plans for each day
3. Specify approximate times for each activity
4. Include estimated costs for activities, meals, and transportation
5. Add travel time between locations
6. Suggest specific restaurants for meals (breakfast, lunch, dinner)
7. Balance different types of activities
8. Keep the daily budget around {daily_budget} {currency}
9. Add practical tips and insider recommendations

For each day, structure as:
{{
  "day": 1,
  "theme": "Day theme/focus",
  "activities": [
    {{
      "time": "09:00 AM",
      "activity": "Activity name",
      "location": "Specific location",
      "duration": "2 hours",
      "cost": 25.00,
      "description": "Detailed description",
      "tips": "Insider tips",
      "category": "sightseeing/food/adventure/etc"
    }}
  ],
  "total_cost": 150.00
}}

Return only a valid JSON object with this structure:
{{
  "trip_title": "Engaging trip title",
  "overview": "Brief trip overview",
  "days": [array of day objects],
  "total_estimated_cost": total_cost
}}""")
])


LOCAL_EXPERIENCES_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(TRAVEL_PLANNER_SYSTEM),
    HumanMessagePromptTemplate.from_template("""Suggest unique local experiences for {destination}.

Traveler Profile:
- Travel Style: {travel_style}
- Interests: {interests}
- Duration: {duration} days

Focus on:
1. Hidden gems and off-the-beaten-path locations
2. Local food experiences (street food, markets, family-run restaurants)
3. Cultural activities and workshops
4. Authentic neighborhood experiences
5. Seasonal events or festivals
6. Local hangout spots
7. Best viewpoints and photo spots
8. Unique shopping opportunities

For each experience, provide:
- Name
- Category (food/culture/adventure/hidden_gem/etc)
- Description (2-3 sentences)
- Why it's special
- Approximate cost
- Best time to visit
- Insider tip

Return as a JSON array of experience objects, limit to 8-10 experiences.""")
])


BUDGET_OPTIMIZATION_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(TRAVEL_PLANNER_SYSTEM),
    HumanMessagePromptTemplate.from_template("""Optimize this itinerary to fit the budget:

Original Itinerary: {itinerary}
Budget: {budget} {currency}
Current Estimated Cost: {current_cost} {currency}

The itinerary is {{"over budget" if {current_cost} > {budget} else "under budget"}}.

Provide recommendations to:
1. Adjust the itinerary to meet the budget
2. Suggest alternative activities that are more/less expensive
3. Recommend budget-saving tips
4. Identify which expenses can be reduced
5. Suggest splurge-worthy experiences if under budget

Return a JSON object with:
{{
  "status": "over_budget" or "within_budget" or "under_budget",
  "adjustments": [list of specific changes],
  "alternative_activities": [list of alternatives],
  "budget_tips": [list of money-saving tips],
  "revised_total": estimated new total
}}""")
])


CHAT_REFINEMENT_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(TRAVEL_PLANNER_SYSTEM + """

You are now in conversation mode helping a user refine their existing travel itinerary.

IMPORTANT INSTRUCTIONS:
1. Carefully analyze the user's request and the current itinerary
2. Identify EXACTLY what needs to change
3. Return ONLY the sections that need updates in the 'updated_sections' field
4. Keep the same data structure as the original itinerary
5. Be specific - if changing day 2, only return day 2 data, not all days
6. Include complete information for changed sections (don't truncate)

COMMON REFINEMENT TYPES:
- Adding/removing activities
- Changing activity timing or order
- Adjusting budget or costs
- Modifying accommodation preferences
- Adding specific attractions or restaurants
- Changing travel pace (more/less packed schedule)
- Dietary restrictions or special requirements

DATA STRUCTURE GUIDELINES:
- For day changes: Return complete day objects with all activities
- For activity changes: Include full activity details (name, description, time, location, cost)
- For multiple day changes: Return array of complete day objects
- Always include day numbers for proper merging
"""),
    HumanMessagePromptTemplate.from_template("""Current Itinerary Summary:
{itinerary_summary}

User Request: {user_message}

Analyze the request and provide a detailed response. Return ONLY valid JSON in this exact format:

{{
  "understanding": "Clear explanation of what the user wants to change",
  "changes": [
    "Specific change 1",
    "Specific change 2",
    "Specific change 3"
  ],
  "updated_sections": {{
    "days": [
      {{
        "day": 1,
        "date": "YYYY-MM-DD",
        "title": "Day title",
        "activities": [
          {{
            "time_slot": "morning/afternoon/evening",
            "start_time": "09:00",
            "duration": 120,
            "name": "Activity name",
            "description": "Detailed description",
            "type": "sightseeing/dining/activity/transport/accommodation",
            "location": "Location name",
            "address": "Full address",
            "latitude": 0.0,
            "longitude": 0.0,
            "cost": 50.00,
            "booking_required": false,
            "booking_url": "https://...",
            "tips": "Helpful tips"
          }}
        ],
        "accommodation": {{
          "name": "Hotel name",
          "type": "hotel/hostel/resort/apartment",
          "address": "Address",
          "cost_per_night": 0,
          "check_in": "14:00",
          "check_out": "11:00"
        }},
        "transportation": {{
          "type": "walking/taxi/bus/train/car",
          "details": "Transportation details",
          "cost": 0
        }},
        "meals": {{
          "breakfast": "Location or included",
          "lunch": "Location and cost",
          "dinner": "Location and cost"
        }},
        "total_day_cost": 0
      }}
    ]
  }},
  "budget_impact": "Detailed explanation of how this affects the total budget (increase/decrease by amount)",
  "response_message": "Friendly, conversational response to the user confirming the changes"
}}

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no code blocks, no extra text
2. Include ONLY the days/sections that are changing
3. When returning a day, include ALL activities for that day (not just the changed ones)
4. If changing day 2 only, return only day 2 in the days array - BUT include ALL activities
5. If no changes needed, return empty "updated_sections": {{}}
6. Always maintain the exact structure shown above
7. Include all required fields for EVERY activity (name, description, time, location, cost, etc.)
8. **IMPORTANT: duration must be INTEGER minutes (e.g., 120 for 2 hours, 60 for 1 hour)**
9. **IMPORTANT: cost must be NUMERIC value (e.g., 50.00, not "$50" or "50 USD")**
10. Boolean values should be true/false (not "true"/"false")
11. start_time should be in 24-hour format "HH:MM" (e.g., "09:00", "14:30")
12. **NEVER omit or truncate activities - include complete activity details for ALL activities in affected days**

Examples of what to return:

Example 1 - Add romantic dinner on day 2:
{{
  "understanding": "User wants to add a romantic dinner experience on day 2 of their trip",
  "changes": ["Adding romantic dinner reservation at upscale restaurant on day 2 evening"],
  "updated_sections": {{
    "days": [{{
      "day": 2,
      "activities": [...existing activities..., {{
        "time_slot": "evening",
        "start_time": "19:00",
        "duration": 120,
        "name": "Romantic Dinner at Le Bernardin",
        "description": "Fine dining experience at Michelin-starred seafood restaurant",
        "type": "dining",
        "location": "Le Bernardin",
        "cost": 250.00,
        "booking_required": true
      }}]
    }}]
  }},
  "budget_impact": "This adds $250 to day 2, increasing total budget by $250",
  "response_message": "I've added a romantic dinner reservation at Le Bernardin for day 2 evening. It's a Michelin-starred restaurant perfect for a special occasion!"
}}

Example 2 - Make day 3 less packed:
{{
  "understanding": "User wants to reduce the number of activities on day 3 to have a more relaxed pace",
  "changes": ["Removed 2 activities from day 3", "Extended lunch time", "Added afternoon relaxation time"],
  "updated_sections": {{
    "days": [{{
      "day": 3,
      "activities": [...only 3-4 key activities instead of 6-7...]
    }}]
  }},
  "budget_impact": "This reduces day 3 costs by approximately $80 due to fewer paid activities",
  "response_message": "I've made day 3 more relaxed by reducing activities and adding downtime. You'll now have a leisurely morning and relaxed afternoon!"
}}

Now process the user's request and return the JSON response.""")
])


COST_ESTIMATION_PROMPT = PromptTemplate(
    input_variables=["destination", "activity_type", "duration", "group_size"],
    template="""Estimate the cost for this activity in {destination}:

Activity Type: {activity_type}
Duration: {duration}
Group Size: {group_size}

Provide a realistic cost estimate in local currency with:
1. Base cost
2. Any additional fees or tips
3. Cost range (low/medium/high)

Return as JSON:
{{
  "estimated_cost": numeric_value,
  "currency": "currency_code",
  "cost_breakdown": {{item: cost}},
  "cost_level": "low/medium/high"
}}"""
)


WEATHER_ADJUSTMENT_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(TRAVEL_PLANNER_SYSTEM),
    HumanMessagePromptTemplate.from_template("""Adjust this itinerary based on weather forecast:

Itinerary: {itinerary_summary}
Weather Forecast: {weather_forecast}

For any days with poor weather conditions:
1. Suggest indoor alternatives
2. Reorder activities if needed
3. Add weather-appropriate tips
4. Recommend backup plans

Return adjusted activities and recommendations as JSON.""")
])


ITINERARY_EXAMPLE = """Example of a well-structured day:
{
  "day": 1,
  "theme": "Historic Rome & Vatican",
  "activities": [
    {
      "time": "08:00 AM",
      "activity": "Breakfast at Roscioli Caffè",
      "location": "Via dei Chiavari, 34",
      "duration": "1 hour",
      "cost": 12.00,
      "description": "Start your day with authentic Italian cornetto and cappuccino at this beloved local spot",
      "tips": "Arrive early to avoid crowds. Try their pistachio cornetto!",
      "category": "food"
    },
    {
      "time": "09:30 AM",
      "activity": "Vatican Museums & Sistine Chapel",
      "location": "Viale Vaticano",
      "duration": "3 hours",
      "cost": 17.00,
      "description": "Explore one of the world's greatest art collections, culminating in Michelangelo's Sistine Chapel ceiling",
      "tips": "Book skip-the-line tickets online. Go counter-clockwise through the museum to avoid crowds. Dress modestly (covered shoulders and knees).",
      "category": "cultural"
    }
  ],
  "total_cost": 165.00
}"""