"""
- ChromaDB initialization and management
- Travel data embedding and storage
- Semantic search for destinations, activities, and local experiences
- RAG (Retrieval Augmented Generation) for personalized recommendations
"""
import os, warnings, logging

os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False'

warnings.filterwarnings('ignore', category=Warning, module='chromadb')
logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)


import chromadb,json
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

class TravelVectorStore:
    """
    Manages vector embeddings for travel-related data using ChromaDB
    """
    
    def __init__(self, persist_directory: str = None):
        
        if persist_directory is None:
            persist_directory = str(Path(settings.BASE_DIR) / 'chroma_db')
        self.persist_directory = persist_directory
        
        import os
        os.environ['ANONYMIZED_TELEMETRY'] = 'False'
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"  
        )
        
        self.destinations_collection = None
        self.activities_collection = None
        self.experiences_collection = None
        self.tips_collection = None
        
        logger.info(f"TravelVectorStore initialized at: {persist_directory}")
        
        
    def initialize_collections(self):
        
        try:
            self.destinations_collection = self.client.get_or_create_collection(
                name="destinations",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Travel destinations with details, best times to visit, and characteristics"
                }
            )
            
            self.activities_collection = self.client.get_or_create_collection(
                name="activities",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Tourist activities, attractions, and things to do"
                }
            )
            
            self.experiences_collection = self.client.get_or_create_collection(
                name="local_experiences",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Local experiences, hidden gems, and insider tips"
                }
            )
            
            self.tips_collection = self.client.get_or_create_collection(
                name="travel_tips",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "General travel tips, advice, and best practices"
                }
            )
            
            logger.info("All collections initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing collections: {str(e)}")
            return False
    
    
    def get_collection_stats(self) -> Dict[str, int]:
        
        stats = {}
        
        if self.destinations_collection:
            stats['destinations'] = self.destinations_collection.count()
        if self.activities_collection:
            stats['activities'] = self.activities_collection.count()
        if self.experiences_collection:
            stats['experiences'] = self.experiences_collection.count()
        if self.tips_collection:
            stats['tips'] = self.tips_collection.count()
        
        stats['total'] = sum(stats.values())
        
        return stats
    
    
    def reset_collections(self):
        """
        Use this for testing or re-seeding data
        """
        try:
            collections = ['destinations', 'activities', 'local_experiences', 'travel_tips']
            
            for collection_name in collections:
                try:
                    self.client.delete_collection(name=collection_name)
                    logger.info(f"Deleted collection: {collection_name}")
                except Exception as e:
                    logger.warning(f"Collection {collection_name} not found or already deleted")
            
            self.initialize_collections()
            logger.info("All collections reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collections: {str(e)}")
            return False
    
    def add_destination(
        self,
        destination_id: str,
        name: str,
        country: str,
        description: str,
        characteristics: List[str],
        best_time_to_visit: str,
        average_budget: Dict[str, float],
        popular_activities: List[str],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a destination to the vector store
        
        Args:
            destination_id: Unique identifier for the destination
            name: Destination name (e.g., "Paris", "Tokyo")
            country: Country name
            description: Detailed description of the destination
            characteristics: List of characteristics (e.g., ["romantic", "historic", "cultural"])
            best_time_to_visit: Best time to visit (e.g., "April to October")
            average_budget: Budget info (e.g., {"low": 50, "medium": 100, "high": 200})
            popular_activities: List of popular activities
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.destinations_collection:
                self.initialize_collections()
            
            searchable_text = f"""
            Destination: {name}, {country}
            Description: {description}
            Characteristics: {', '.join(characteristics)}
            Best time to visit: {best_time_to_visit}
            Popular activities: {', '.join(popular_activities)}
            """
            
            doc_metadata = {
                "name": name,
                "country": country,
                "characteristics": json.dumps(characteristics),
                "best_time": best_time_to_visit,
                "budget_range": json.dumps(average_budget),
                "type": "destination"
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            self.destinations_collection.add(
                documents=[searchable_text],
                metadatas=[doc_metadata],
                ids=[destination_id]
            )
            
            logger.info(f"Added destination: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding destination {name}: {str(e)}")
            return False
        
    
    def add_activity(
        self,
        activity_id: str,
        name: str,
        destination: str,
        category: str,
        description: str,
        duration: str,
        cost_range: Dict[str, float],
        best_for: List[str],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add an activity to the vector store
        
        Args:
            activity_id: Unique identifier
            name: Activity name
            destination: Destination where activity is located
            category: Activity category (e.g., "sightseeing", "food", "adventure")
            description: Detailed description
            duration: Typical duration (e.g., "2-3 hours")
            cost_range: Cost information
            best_for: List of travel styles this suits (e.g., ["families", "couples"])
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.activities_collection:
                self.initialize_collections()
            
            searchable_text = f"""
            Activity: {name}
            Location: {destination}
            Category: {category}
            Description: {description}
            Duration: {duration}
            Best for: {', '.join(best_for)}
            """
            
            doc_metadata = {
                "name": name,
                "destination": destination,
                "category": category,
                "duration": duration,
                "cost_range": json.dumps(cost_range),
                "best_for": json.dumps(best_for),
                "type": "activity"
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            self.activities_collection.add(
                documents=[searchable_text],
                metadatas=[doc_metadata],
                ids=[activity_id]
            )
            
            logger.info(f"Added activity: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding activity {name}: {str(e)}")
            return False
    
    
    def add_local_experience(
        self,
        experience_id: str,
        name: str,
        destination: str,
        category: str,
        description: str,
        insider_tip: str,
        best_time: str,
        hidden_gem: bool = False,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a local experience/hidden gem to the vector store
        
        Args:
            experience_id: Unique identifier
            name: Experience name
            destination: Destination where experience is located
            category: Category (e.g., "food", "culture", "nature")
            description: Detailed description
            insider_tip: Special insider tip
            best_time: Best time to experience this
            hidden_gem: Whether this is a hidden gem
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.experiences_collection:
                self.initialize_collections()
            
            searchable_text = f"""
            Experience: {name}
            Location: {destination}
            Category: {category}
            Description: {description}
            Insider tip: {insider_tip}
            Best time: {best_time}
            {"This is a hidden gem!" if hidden_gem else ""}
            """
            
            doc_metadata = {
                "name": name,
                "destination": destination,
                "category": category,
                "best_time": best_time,
                "hidden_gem": hidden_gem,
                "type": "local_experience"
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            self.experiences_collection.add(
                documents=[searchable_text],
                metadatas=[doc_metadata],
                ids=[experience_id]
            )
            
            logger.info(f"Added local experience: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding local experience {name}: {str(e)}")
            return False
        
    
    def add_travel_tip(
        self,
        tip_id: str,
        title: str,
        content: str,
        category: str,
        applicable_to: List[str],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a travel tip to the vector store
        
        Args:
            tip_id: Unique identifier
            title: Tip title
            content: Tip content
            category: Category (e.g., "safety", "budgeting", "packing")
            applicable_to: List of destinations or situations this applies to
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.tips_collection:
                self.initialize_collections()
            
            searchable_text = f"""
            {title}
            {content}
            Category: {category}
            Applicable to: {', '.join(applicable_to)}
            """
            
            doc_metadata = {
                "title": title,
                "category": category,
                "applicable_to": json.dumps(applicable_to),
                "type": "travel_tip"
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            self.tips_collection.add(
                documents=[searchable_text],
                metadatas=[doc_metadata],
                ids=[tip_id]
            )
            
            logger.info(f"Added travel tip: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding travel tip {title}: {str(e)}")
            return False


vector_store = TravelVectorStore()