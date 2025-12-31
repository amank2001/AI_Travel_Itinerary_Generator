from .vector_store import vector_store
import logging

logger = logging.getLogger(__name__)

def seed_destinations():
    """Seed popular travel destinations"""
    
    destinations = [
        {
            'destination_id': 'dest_paris',
            'name': 'Paris',
            'country': 'France',
            'description': 'The City of Light, known for its art, fashion, gastronomy, and culture. Home to iconic landmarks like the Eiffel Tower and Louvre Museum.',
            'characteristics': ['romantic', 'cultural', 'historic', 'artistic', 'fashionable', 'culinary'],
            'best_time_to_visit': 'April to June, September to October',
            'average_budget': {'low': 80, 'medium': 150, 'high': 300},
            'popular_activities': ['visit museums', 'Seine river cruise', 'café culture', 'shopping', 'architecture tours']
        },
        {
            'destination_id': 'dest_tokyo',
            'name': 'Tokyo',
            'country': 'Japan',
            'description': 'A vibrant metropolis blending ultra-modern and traditional culture. Famous for technology, anime, temples, and incredible food scene.',
            'characteristics': ['modern', 'traditional', 'technological', 'culinary', 'safe', 'efficient'],
            'best_time_to_visit': 'March to May (cherry blossoms), September to November',
            'average_budget': {'low': 70, 'medium': 120, 'high': 250},
            'popular_activities': ['temple visits', 'food tours', 'shopping', 'karaoke', 'anime culture', 'cherry blossom viewing']
        },
        {
            'destination_id': 'dest_bali',
            'name': 'Bali',
            'country': 'Indonesia',
            'description': 'Island paradise known for beautiful beaches, rice terraces, spiritual culture, and affordable luxury. Perfect for relaxation and adventure.',
            'characteristics': ['tropical', 'spiritual', 'affordable', 'beach', 'adventure', 'wellness'],
            'best_time_to_visit': 'April to October (dry season)',
            'average_budget': {'low': 30, 'medium': 60, 'high': 150},
            'popular_activities': ['beach activities', 'yoga retreats', 'temple visits', 'surfing', 'rice terrace tours', 'spa treatments']
        },
        {
            'destination_id': 'dest_new_york',
            'name': 'New York City',
            'country': 'USA',
            'description': 'The city that never sleeps. A global hub for art, culture, fashion, and finance with iconic landmarks and diverse neighborhoods.',
            'characteristics': ['urban', 'diverse', 'energetic', 'cultural', 'modern', 'expensive'],
            'best_time_to_visit': 'April to June, September to November',
            'average_budget': {'low': 100, 'medium': 200, 'high': 400},
            'popular_activities': ['Broadway shows', 'museum visits', 'Central Park', 'shopping', 'food tours', 'skyline views']
        },
        {
            'destination_id': 'dest_barcelona',
            'name': 'Barcelona',
            'country': 'Spain',
            'description': 'Cosmopolitan city famous for Gaudí architecture, Mediterranean beaches, vibrant nightlife, and incredible tapas culture.',
            'characteristics': ['artistic', 'beach', 'cultural', 'nightlife', 'architectural', 'culinary'],
            'best_time_to_visit': 'May to June, September to October',
            'average_budget': {'low': 60, 'medium': 110, 'high': 220},
            'popular_activities': ['Gaudí architecture tours', 'beach time', 'tapas crawls', 'Gothic Quarter walks', 'nightlife']
        },
        {
            'destination_id': 'dest_dubai',
            'name': 'Dubai',
            'country': 'UAE',
            'description': 'Futuristic city known for luxury shopping, modern architecture, and vibrant nightlife. Features the world\'s tallest building.',
            'characteristics': ['luxury', 'modern', 'shopping', 'desert', 'family-friendly', 'cosmopolitan'],
            'best_time_to_visit': 'November to March',
            'average_budget': {'low': 80, 'medium': 150, 'high': 350},
            'popular_activities': ['desert safari', 'luxury shopping', 'beach resorts', 'skyscraper visits', 'water parks']
        },
        {
            'destination_id': 'dest_rome',
            'name': 'Rome',
            'country': 'Italy',
            'description': 'The Eternal City, a living museum with ancient ruins, Renaissance art, and incredible Italian cuisine at every corner.',
            'characteristics': ['historic', 'cultural', 'romantic', 'culinary', 'artistic', 'religious'],
            'best_time_to_visit': 'April to June, September to October',
            'average_budget': {'low': 70, 'medium': 130, 'high': 260},
            'popular_activities': ['ancient ruins tours', 'Vatican visits', 'pasta making classes', 'gelato tasting', 'piazza hopping']
        },
        {
            'destination_id': 'dest_santorini',
            'name': 'Santorini',
            'country': 'Greece',
            'description': 'Stunning Greek island with white-washed buildings, blue-domed churches, and spectacular sunsets over the Aegean Sea.',
            'characteristics': ['romantic', 'scenic', 'island', 'beach', 'luxury', 'photogenic'],
            'best_time_to_visit': 'April to November',
            'average_budget': {'low': 80, 'medium': 150, 'high': 300},
            'popular_activities': ['sunset watching', 'wine tasting', 'beach clubs', 'boat tours', 'photography', 'cliff walking']
        },
        {
            'destination_id': 'dest_bangkok',
            'name': 'Bangkok',
            'country': 'Thailand',
            'description': 'Vibrant capital city mixing ornate temples, bustling markets, modern malls, and legendary street food culture.',
            'characteristics': ['affordable', 'culinary', 'cultural', 'nightlife', 'shopping', 'spiritual'],
            'best_time_to_visit': 'November to February',
            'average_budget': {'low': 25, 'medium': 50, 'high': 120},
            'popular_activities': ['temple visits', 'street food tours', 'floating markets', 'rooftop bars', 'Thai massage', 'shopping']
        },
        {
            'destination_id': 'dest_iceland',
            'name': 'Reykjavik/Iceland',
            'country': 'Iceland',
            'description': 'Land of fire and ice with stunning natural phenomena including geysers, waterfalls, northern lights, and volcanic landscapes.',
            'characteristics': ['nature', 'adventure', 'scenic', 'unique', 'photography', 'expensive'],
            'best_time_to_visit': 'June to August (midnight sun), September to March (northern lights)',
            'average_budget': {'low': 100, 'medium': 180, 'high': 350},
            'popular_activities': ['northern lights viewing', 'Blue Lagoon', 'Golden Circle tour', 'glacier hiking', 'waterfall tours']
        }
    ]
    
    print("Seeding destinations...")
    for dest in destinations:
        vector_store.add_destination(**dest)
    print(f"✓ Added {len(destinations)} destinations")
    

def seed_activities():
    """Seed popular activities and attractions"""
    
    activities = [
        # Paris Activities
        {
            'activity_id': 'act_eiffel_tower',
            'name': 'Eiffel Tower Visit',
            'destination': 'Paris',
            'category': 'sightseeing',
            'description': 'Iconic iron lattice tower offering stunning views of Paris from observation decks. Visit at sunset for magical views.',
            'duration': '2-3 hours',
            'cost_range': {'min': 15, 'max': 30},
            'best_for': ['couples', 'families', 'photographers', 'first-timers']
        },
        {
            'activity_id': 'act_louvre',
            'name': 'Louvre Museum',
            'destination': 'Paris',
            'category': 'cultural',
            'description': 'World\'s largest art museum housing the Mona Lisa and thousands of masterpieces. Allow full day to explore.',
            'duration': '4-6 hours',
            'cost_range': {'min': 17, 'max': 17},
            'best_for': ['art lovers', 'culture seekers', 'history buffs']
        },
        {
            'activity_id': 'act_seine_cruise',
            'name': 'Seine River Cruise',
            'destination': 'Paris',
            'category': 'relaxation',
            'description': 'Romantic boat cruise along the Seine passing under beautiful bridges and by famous landmarks.',
            'duration': '1-2 hours',
            'cost_range': {'min': 15, 'max': 100},
            'best_for': ['couples', 'romantic travelers', 'families']
        },
        
        # Tokyo Activities
        {
            'activity_id': 'act_sensoji',
            'name': 'Senso-ji Temple',
            'destination': 'Tokyo',
            'category': 'cultural',
            'description': 'Tokyo\'s oldest and most significant Buddhist temple with beautiful architecture and traditional shopping street.',
            'duration': '2-3 hours',
            'cost_range': {'min': 0, 'max': 0},
            'best_for': ['culture seekers', 'photographers', 'spiritual travelers', 'families']
        },
        {
            'activity_id': 'act_tsukiji',
            'name': 'Tsukiji Outer Market Food Tour',
            'destination': 'Tokyo',
            'category': 'food',
            'description': 'Explore Japan\'s famous fish market and sample fresh sushi, street food, and local delicacies.',
            'duration': '2-3 hours',
            'cost_range': {'min': 20, 'max': 50},
            'best_for': ['foodies', 'culture seekers', 'adventurous eaters']
        },
        {
            'activity_id': 'act_shibuya',
            'name': 'Shibuya Crossing Experience',
            'destination': 'Tokyo',
            'category': 'sightseeing',
            'description': 'Experience the world\'s busiest pedestrian crossing and explore vibrant Shibuya district with shopping and dining.',
            'duration': '2-4 hours',
            'cost_range': {'min': 0, 'max': 50},
            'best_for': ['photographers', 'culture seekers', 'shoppers', 'first-timers']
        },
        
        # Bali Activities
        {
            'activity_id': 'act_ubud_rice',
            'name': 'Tegallalang Rice Terraces',
            'destination': 'Bali',
            'category': 'nature',
            'description': 'Stunning emerald-green rice terraces with scenic walking trails and photo opportunities.',
            'duration': '2-3 hours',
            'cost_range': {'min': 5, 'max': 15},
            'best_for': ['photographers', 'nature lovers', 'hikers', 'couples']
        },
        {
            'activity_id': 'act_tanah_lot',
            'name': 'Tanah Lot Temple Sunset',
            'destination': 'Bali',
            'category': 'cultural',
            'description': 'Ancient sea temple perched on a rock formation, famous for spectacular sunset views.',
            'duration': '2-3 hours',
            'cost_range': {'min': 5, 'max': 10},
            'best_for': ['photographers', 'spiritual travelers', 'couples', 'culture seekers']
        },
        {
            'activity_id': 'act_bali_surf',
            'name': 'Surfing Lessons at Canggu',
            'destination': 'Bali',
            'category': 'adventure',
            'description': 'Learn to surf or improve your skills at Bali\'s famous surf beaches with experienced instructors.',
            'duration': '2-3 hours',
            'cost_range': {'min': 30, 'max': 60},
            'best_for': ['adventure seekers', 'beginners', 'active travelers']
        },
        
        # New York Activities
        {
            'activity_id': 'act_central_park',
            'name': 'Central Park Exploration',
            'destination': 'New York City',
            'category': 'nature',
            'description': 'Urban oasis with walking paths, lakes, gardens, and famous landmarks like Bethesda Fountain.',
            'duration': '3-4 hours',
            'cost_range': {'min': 0, 'max': 40},
            'best_for': ['families', 'nature lovers', 'joggers', 'photographers']
        },
        {
            'activity_id': 'act_broadway',
            'name': 'Broadway Show',
            'destination': 'New York City',
            'category': 'entertainment',
            'description': 'Experience world-class theater productions in iconic Broadway theaters.',
            'duration': '2-3 hours',
            'cost_range': {'min': 50, 'max': 300},
            'best_for': ['culture seekers', 'theater lovers', 'date nights']
        },
        {
            'activity_id': 'act_met_museum',
            'name': 'Metropolitan Museum of Art',
            'destination': 'New York City',
            'category': 'cultural',
            'description': 'One of the world\'s finest art museums with collections spanning 5,000 years of culture.',
            'duration': '3-5 hours',
            'cost_range': {'min': 30, 'max': 30},
            'best_for': ['art lovers', 'culture seekers', 'history buffs']
        },
        
        # Barcelona Activities
        {
            'activity_id': 'act_sagrada',
            'name': 'Sagrada Familia',
            'destination': 'Barcelona',
            'category': 'cultural',
            'description': 'Gaudí\'s unfinished masterpiece basilica with stunning modernist architecture and intricate details.',
            'duration': '2-3 hours',
            'cost_range': {'min': 26, 'max': 40},
            'best_for': ['architecture lovers', 'culture seekers', 'photographers']
        },
        {
            'activity_id': 'act_park_guell',
            'name': 'Park Güell',
            'destination': 'Barcelona',
            'category': 'sightseeing',
            'description': 'Whimsical public park designed by Gaudí with colorful mosaics and panoramic city views.',
            'duration': '2-3 hours',
            'cost_range': {'min': 10, 'max': 13},
            'best_for': ['families', 'photographers', 'architecture lovers', 'nature lovers']
        },
        {
            'activity_id': 'act_barcelona_beach',
            'name': 'Barceloneta Beach',
            'destination': 'Barcelona',
            'category': 'relaxation',
            'description': 'Popular urban beach with golden sand, beach bars, and Mediterranean vibes.',
            'duration': '2-4 hours',
            'cost_range': {'min': 0, 'max': 30},
            'best_for': ['beach lovers', 'families', 'sun seekers', 'active travelers']
        }
    ]
    
    print("Seeding activities...")
    for activity in activities:
        vector_store.add_activity(**activity)
    print(f"✓ Added {len(activities)} activities")
    
    
def seed_local_experiences():
    """Seed local experiences and hidden gems"""
    
    experiences = [
        # Paris
        {
            'experience_id': 'exp_paris_boulangerie',
            'name': 'Neighborhood Boulangerie Morning',
            'destination': 'Paris',
            'category': 'food',
            'description': 'Start your day like a true Parisian at a local boulangerie in Le Marais. Try fresh croissants and pain au chocolat.',
            'insider_tip': 'Go before 9 AM when everything is fresh from the oven. Locals buy their bread twice daily!',
            'best_time': 'Early morning (7-9 AM)',
            'hidden_gem': True
        },
        {
            'experience_id': 'exp_paris_canal',
            'name': 'Canal Saint-Martin Picnic',
            'destination': 'Paris',
            'category': 'culture',
            'description': 'Join locals for a picnic along the trendy Canal Saint-Martin. Bring wine, cheese, and baguette from local shops.',
            'insider_tip': 'Visit Du Pain et des Idées bakery nearby for the best pastries in Paris.',
            'best_time': 'Late afternoon/evening',
            'hidden_gem': True
        },
        
        # Tokyo
        {
            'experience_id': 'exp_tokyo_izakaya',
            'name': 'Local Izakaya Experience',
            'destination': 'Tokyo',
            'category': 'food',
            'description': 'Experience authentic Japanese pub culture in a tiny izakaya under the train tracks in Yurakucho.',
            'insider_tip': 'Order yakitori (grilled chicken skewers) and try whatever the chef recommends - it\'s always fresh!',
            'best_time': 'Evening (6-10 PM)',
            'hidden_gem': True
        },
        {
            'experience_id': 'exp_tokyo_onsen',
            'name': 'Neighborhood Sento (Public Bath)',
            'destination': 'Tokyo',
            'category': 'culture',
            'description': 'Visit a traditional neighborhood bathhouse frequented by locals. A quintessential Tokyo experience.',
            'insider_tip': 'Bring your own small towel. Remember to wash thoroughly before entering the bath!',
            'best_time': 'Evening',
            'hidden_gem': True
        },
        
        # Bali
        {
            'experience_id': 'exp_bali_ceremony',
            'name': 'Balinese Temple Ceremony',
            'destination': 'Bali',
            'category': 'culture',
            'description': 'Attend a traditional temple ceremony with gamelan music, offerings, and colorful processions.',
            'insider_tip': 'Wear a sarong and sash (provided at temples). Be respectful during prayers and photography.',
            'best_time': 'Check local temple calendars, often full moon',
            'hidden_gem': True
        },
        {
            'experience_id': 'exp_bali_warung',
            'name': 'Local Warung Breakfast',
            'destination': 'Bali',
            'category': 'food',
            'description': 'Eat breakfast at a family-run warung. Try nasi goreng or bubur ayam for authentic Balinese flavors.',
            'insider_tip': 'Look for warungs where you see lots of locals eating. They have the best food and lowest prices!',
            'best_time': 'Morning',
            'hidden_gem': True
        },
        
        # New York
        {
            'experience_id': 'exp_ny_speakeasy',
            'name': 'Hidden Speakeasy Bar',
            'destination': 'New York City',
            'category': 'nightlife',
            'description': 'Discover secret speakeasy bars hidden behind phone booths, bookshelf doors, and unmarked entrances.',
            'insider_tip': 'Try PDT (Please Don\'t Tell) - enter through a phone booth in a hot dog shop!',
            'best_time': 'Evening/night',
            'hidden_gem': True
        },
        {
            'experience_id': 'exp_ny_street_food',
            'name': 'Queens Street Food Tour',
            'destination': 'New York City',
            'category': 'food',
            'description': 'Explore authentic ethnic cuisines in Queens - from Tibetan momos to Colombian arepas.',
            'insider_tip': 'Jackson Heights and Flushing have the most diverse and authentic food scenes.',
            'best_time': 'Lunch or dinner time',
            'hidden_gem': True
        },
        
        # Barcelona
        {
            'experience_id': 'exp_bcn_vermuteria',
            'name': 'Vermouth Hour at Local Vermuteria',
            'destination': 'Barcelona',
            'category': 'food',
            'description': 'Join locals for Sunday vermouth hour (l\'hora del vermut) with tapas and good conversation.',
            'insider_tip': 'Try La Pepita in Gracia neighborhood. Order house vermouth with olives and chips.',
            'best_time': 'Sunday noon-2 PM',
            'hidden_gem': True
        },
        {
            'experience_id': 'exp_bcn_bunkers',
            'name': 'Bunkers del Carmel Sunset',
            'destination': 'Barcelona',
            'category': 'nature',
            'description': 'Watch sunset from abandoned civil war bunkers with 360-degree views of Barcelona.',
            'insider_tip': 'Bring snacks and drinks. It gets crowded, so arrive 1 hour before sunset for good spots.',
            'best_time': 'Sunset',
            'hidden_gem': True
        }
    ]
    
    print("Seeding local experiences...")
    for exp in experiences:
        vector_store.add_local_experience(**exp)
    print(f"✓ Added {len(experiences)} local experiences")
    
    
def seed_travel_tips():
    """Seed general travel tips"""
    
    tips = [
        {
            'tip_id': 'tip_booking',
            'title': 'Book Flights on Tuesday',
            'content': 'Airlines often release deals on Monday evenings, making Tuesday the best day to find lower fares. Use incognito mode to avoid price tracking.',
            'category': 'budgeting',
            'applicable_to': ['all destinations']
        },
        {
            'tip_id': 'tip_local_food',
            'title': 'Eat Where Locals Eat',
            'content': 'Avoid restaurants near major tourist attractions. Walk 2-3 blocks away or ask locals for recommendations. Street food is often delicious and authentic.',
            'category': 'food',
            'applicable_to': ['all destinations']
        },
        {
            'tip_id': 'tip_free_walking',
            'title': 'Take Free Walking Tours',
            'content': 'Most cities offer free walking tours (tip-based). Great way to orient yourself, learn history, and get local recommendations on your first day.',
            'category': 'budgeting',
            'applicable_to': ['all destinations']
        },
        {
            'tip_id': 'tip_shoulder_season',
            'title': 'Travel During Shoulder Season',
            'content': 'Visit popular destinations in shoulder season (just before/after peak) for better weather than off-season, fewer crowds than peak, and lower prices.',
            'category': 'planning',
            'applicable_to': ['all destinations']
        },
        {
            'tip_id': 'tip_sim_card',
            'title': 'Buy Local SIM Card',
            'content': 'Get a local SIM card at the airport or convenience stores. Much cheaper than international roaming and essential for navigation and communication.',
            'category': 'technology',
            'applicable_to': ['all destinations']
        },
        {
            'tip_id': 'tip_copy_docs',
            'title': 'Keep Digital Copies of Documents',
            'content': 'Scan passport, visa, insurance, and important documents. Email them to yourself and save in cloud storage. Lifesaver if originals are lost.',
            'category': 'safety',
            'applicable_to': ['all destinations']
        },
        {
            'tip_id': 'tip_learn_phrases',
            'title': 'Learn Basic Local Phrases',
            'content': 'Learn "hello", "thank you", "sorry", and "help" in the local language. Locals appreciate the effort and it can help in emergencies.',
            'category': 'cultural',
            'applicable_to': ['all destinations']
        },
        {
            'tip_id': 'tip_early_attractions',
            'title': 'Visit Popular Attractions Early',
            'content': 'Arrive at famous sites right when they open. You\'ll beat crowds, get better photos, and enjoy a more peaceful experience.',
            'category': 'sightseeing',
            'applicable_to': ['Paris', 'Rome', 'Barcelona', 'Tokyo', 'New York City']
        },
        {
            'tip_id': 'tip_cash_backup',
            'title': 'Always Carry Some Cash',
            'content': 'Even in card-friendly cities, keep some local currency for small purchases, markets, tipping, and emergencies. Not all places accept cards.',
            'category': 'budgeting',
            'applicable_to': ['all destinations']
        },
        {
            'tip_id': 'tip_pack_light',
            'title': 'Pack Light - You\'ll Buy More',
            'content': 'Leave room in your luggage. You\'ll likely buy souvenirs, and overpacking makes travel exhausting. If you can\'t carry it easily, it\'s too much.',
            'category': 'packing',
            'applicable_to': ['all destinations']
        }
    ]
    
    print("Seeding travel tips...")
    for tip in tips:
        vector_store.add_travel_tip(**tip)
    print(f"✓ Added {len(tips)} travel tips")


def main():
    """Main seeding function"""
    print("\n" + "="*60)
    print("SEEDING TRAVEL VECTOR STORE")
    print("="*60 + "\n")
    
    # Initialize collections
    print("Initializing collections...")
    vector_store.initialize_collections()
    print("✓ Collections initialized\n")
    
    # Seed all data
    seed_destinations()
    print()
    seed_activities()
    print()
    seed_local_experiences()
    print()
    seed_travel_tips()
    print()
    
    # Show statistics
    stats = vector_store.get_collection_stats()
    print("="*60)
    print("SEEDING COMPLETE!")
    print("="*60)
    print(f"\nVector Store Statistics:")
    print(f"  Destinations: {stats.get('destinations', 0)}")
    print(f"  Activities: {stats.get('activities', 0)}")
    print(f"  Local Experiences: {stats.get('experiences', 0)}")
    print(f"  Travel Tips: {stats.get('tips', 0)}")
    print(f"  Total Documents: {stats.get('total', 0)}")
    print("\n✨ Vector store is ready for RAG queries!\n")


if __name__ == "__main__":
    main()