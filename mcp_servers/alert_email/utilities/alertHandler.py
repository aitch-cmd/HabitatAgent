import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from bson import ObjectId
from db.connection import MongoDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alert_mongodb")


class AlertMongoDBHandler:
    """
    Handles MongoDB operations for property alert storage.
    
    This class manages the alert_email collection which stores:
    - User email addresses
    - Location preferences
    - Price/budget criteria
    - Timestamps for alert creation and updates
    """

    def __init__(self, collection_name: str = "alert_email"):
        """
        Initialize DB connection and ensure indexes exist.
        
        Args:
            collection_name: Name of the MongoDB collection (default: "alert_email")
        """
        try:
            self.db_client = MongoDBClient(database_name="rental_database")
            self.collection = self.db_client.database[collection_name]
            self._ensure_indexes()
            logger.info(f"Connected to MongoDB collection: {collection_name}")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def _ensure_indexes(self):
        """Create indexes for efficient queries."""
        try:
            # Index on email for fast lookups
            self.collection.create_index("email", unique=False)
            
            # Index on location for filtering alerts by area
            self.collection.create_index("location")
            
            # Index on created_at for time-based queries
            self.collection.create_index("created_at")
            
            # Compound index for email + location queries
            self.collection.create_index([("email", 1), ("location", 1)])
            
            logger.info("Indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    def save_alert(self, email: str, location: Optional[str] = None, 
                   price: Optional[int] = None) -> str:
        """
        Save a new alert to the database.
        
        Args:
            email: User's email address (required)
            location: Preferred location/area (optional)
            price: Maximum budget (optional)
            
        Returns:
            str: MongoDB ObjectId of the inserted document
            
        Raises:
            ValueError: If email is not provided
            Exception: If database operation fails
        """
        if not email:
            raise ValueError("Email is required to create an alert")
        
        alert_document = {
            "email": email.lower().strip(),
            "location": location.strip() if location else None,
            "price": price,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        }
        
        try:
            result = self.collection.insert_one(alert_document)
            logger.info(f"Alert saved: {result.inserted_id} for {email}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
            raise

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an alert by its MongoDB ObjectId.
        
        Args:
            alert_id: MongoDB ObjectId as string
            
        Returns:
            dict: Alert document or None if not found
        """
        try:
            object_id = ObjectId(alert_id)
            alert = self.collection.find_one({"_id": object_id})
            
            if alert:
                alert["_id"] = str(alert["_id"])
            
            return alert
        except Exception as e:
            logger.error(f"Error retrieving alert: {e}")
            return None

    def get_alerts_by_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Get all alerts for a specific email address.
        
        Args:
            email: User's email address
            
        Returns:
            list: List of alert documents
        """
        try:
            alerts = list(self.collection.find(
                {"email": email.lower().strip()}
            ).sort("created_at", -1))
            
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
            
            return alerts
        except Exception as e:
            logger.error(f"Error retrieving alerts for {email}: {e}")
            return []

    def get_all_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Get all active alerts from the database.
        
        Returns:
            list: List of all active alert documents
        """
        try:
            alerts = list(self.collection.find(
                {"status": "active"}
            ).sort("created_at", -1))
            
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
            
            return alerts
        except Exception as e:
            logger.error(f"Error retrieving active alerts: {e}")
            return []

   
    def delete_alert(self, alert_id: str) -> bool:
        """
        Delete an alert by its ID.
        
        Args:
            alert_id: MongoDB ObjectId as string
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            object_id = ObjectId(alert_id)
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                logger.info(f"Alert deleted: {alert_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            return False

    def deactivate_alert(self, alert_id: str) -> bool:
        """
        Deactivate an alert (soft delete - keeps in database but marks as inactive).
        
        Args:
            alert_id: MongoDB ObjectId as string
            
        Returns:
            bool: True if deactivated successfully, False otherwise
        """
        try:
            object_id = ObjectId(alert_id)
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deactivating alert: {e}")
            return False

    def get_alerts_by_criteria(self, location: Optional[str] = None, 
                               max_price: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find alerts matching specific criteria (useful for matching new listings to alerts).
        
        Args:
            location: Location to match
            max_price: Maximum price to match
            
        Returns:
            list: List of matching alert documents
        """
        query = {"status": "active"}
        
        if location:
            query["location"] = {"$regex": location, "$options": "i"}
        
        if max_price:
            query["$or"] = [
                {"price": {"$gte": max_price}},
                {"price": None}
            ]
        
        try:
            alerts = list(self.collection.find(query))
            
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
            
            return alerts
        except Exception as e:
            logger.error(f"Error querying alerts: {e}")
            return []

    def count_alerts(self) -> int:
        """
        Get total count of active alerts.
        
        Returns:
            int: Number of active alerts
        """
        try:
            return self.collection.count_documents({"status": "active"})
        except Exception as e:
            logger.error(f"Error counting alerts: {e}")
            return 0


# Example usage and testing
if __name__ == "__main__":
    print("Testing AlertMongoDBHandler...\n")
    
    try:
        handler = AlertMongoDBHandler()
        
        # Test 1: Save a new alert
        print("Test 1: Saving alert...")
        alert_id = handler.save_alert(
            email="john.doe@example.com",
            location="Bangalore",
            price=30000
        )
        print(f"✅ Alert saved with ID: {alert_id}\n")
        
        # Test 2: Retrieve alert by ID
        print("Test 2: Retrieving alert by ID...")
        alert = handler.get_alert_by_id(alert_id)
        print(f"✅ Retrieved: {alert}\n")
        
        # Test 3: Get alerts by email
        print("Test 3: Getting alerts by email...")
        alerts = handler.get_alerts_by_email("john.doe@example.com")
        print(f"✅ Found {len(alerts)} alerts\n")
        
        
        # Test 5: Get all active alerts
        print("Test 5: Getting all active alerts...")
        all_alerts = handler.get_all_active_alerts()
        print(f"✅ Found {len(all_alerts)} active alerts\n")
        
        # Test 6: Count alerts
        print("Test 6: Counting alerts...")
        count = handler.count_alerts()
        print(f"✅ Total active alerts: {count}\n")
        
        # Test 7: Deactivate alert
        print("Test 7: Deactivating alert...")
        success = handler.deactivate_alert(alert_id)
        print(f"✅ Deactivation {'successful' if success else 'failed'}\n")
        
        # Test 8: Delete alert (cleanup)
        print("Test 8: Deleting alert...")
        success = handler.delete_alert(alert_id)
        print(f"✅ Deletion {'successful' if success else 'failed'}\n")
        
        print("All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")