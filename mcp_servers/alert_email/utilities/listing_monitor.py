import logging
from datetime import datetime
from typing import Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from db.connection import MongoDBClient
from mcp_servers.alert_email.utilities.email import EmailService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("listing_monitor")


class ListingMonitor:
    """
    Monitors the tulire_listings collection for new insertions
    and triggers alert notifications in real-time.
    """

    def __init__(self):
        """Initialize the listing monitor."""
        try:
            self.db_client = MongoDBClient(database_name="rental_database")
            self.listings_collection = self.db_client.database["tulire_listings"]
            self.alerts_collection = self.db_client.database["alert_mongodb"]
            self.email_service = EmailService()
            
            logger.info("Listing monitor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize listing monitor: {e}")
            raise

    def find_matching_alerts(self, listing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find all alerts that match the given listing.
        
        Args:
            listing: The new listing document
            
        Returns:
            list: List of matching alert documents
        """
        try:
            listing_address = listing.get("address", "")
            listing_price = listing.get("price", 0)
            
            # Extract location from address (e.g., "Jersey City" from full address)
            # This handles cases like "96-100 Tuers Avenue - 201, Jersey City, NJ 07306"
            address_parts = listing_address.split(",")
            city = address_parts[1].strip() if len(address_parts) > 1 else listing_address
            
            logger.info(f"Looking for alerts matching: {city}, Price: ${listing_price}")
            
            # Find alerts where:
            # 1. Location is None (any location) OR location matches the listing city/address
            # 2. Price is None (any price) OR price >= listing price (user willing to pay more)
            
            matching_alerts = []
            
            # Get all active alerts
            all_alerts = list(self.alerts_collection.find({"status": "active"}))
            
            for alert in all_alerts:
                alert_location = alert.get("location")
                alert_price = alert.get("price")
                
                # Check location match
                location_matches = False
                if alert_location is None:
                    location_matches = True  # User wants any location
                else:
                    # Case-insensitive partial match
                    if alert_location.lower() in listing_address.lower():
                        location_matches = True
                
                # Check price match
                price_matches = False
                if alert_price is None:
                    price_matches = True  # User has no price limit
                else:
                    # User's max price should be >= listing price
                    if alert_price >= listing_price:
                        price_matches = True
                
                # If both match, add to results
                if location_matches and price_matches:
                    matching_alerts.append(alert)
                    logger.info(f"Match found for alert {alert['_id']} - {alert['email']}")
            
            return matching_alerts
            
        except Exception as e:
            logger.error(f"Error finding matching alerts: {e}")
            return []

    def send_notification(self, alert: Dict[str, Any], listing: Dict[str, Any]) -> bool:
        """
        Send email notification about a new matching listing.
        
        Args:
            alert: Alert document
            listing: New listing document
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            email = alert.get("email")
            
            # Prepare email subject
            subject = "🏠 New Property Alert - Perfect Match Found!"
            
            # Format listing details
            address = listing.get("address", "N/A")
            price = listing.get("price", 0)
            bedrooms = listing.get("bedroom", "N/A")
            bathrooms = listing.get("bathroom", "N/A")
            description = listing.get("description", "")
            listing_url = listing.get("listing_url", "")
            pet_friendly = listing.get("pet_friendly", "N/A")
            
            # Truncate description
            if len(description) > 300:
                description = description[:300] + "..."
            
            # Format amenities if available
            amenities_text = ""
            if "amenities" in listing and isinstance(listing["amenities"], dict):
                amenities = listing["amenities"]
                amenities_list = [f"  • {k}: {v}" for k, v in amenities.items() if v]
                if amenities_list:
                    amenities_text = "\n\n🎯 Amenities:\n" + "\n".join(amenities_list[:10])
            
            # Format rental terms if available
            rental_terms_text = ""
            if "rental_terms" in listing and isinstance(listing["rental_terms"], dict):
                terms = listing["rental_terms"]
                terms_list = [f"  • {k}: {v}" for k, v in terms.items() if v]
                if terms_list:
                    rental_terms_text = "\n\n📋 Rental Terms:\n" + "\n".join(terms_list[:5])
            
            # Prepare email message
            message = f"""Hello,

🎉 Great news! A new property has been listed that matches your alert criteria!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 PROPERTY DETAILS

📍 Address: {address}
💵 Rent: ${price:,}/month
🛏️  Bedrooms: {bedrooms} | 🚿 Bathrooms: {bathrooms}
🐾 Pet Friendly: {pet_friendly}

📝 Description:
{description}
{amenities_text}
{rental_terms_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR ALERT CRITERIA:
✓ Location: {alert.get('location', 'Any location')}
✓ Max Budget: ${alert.get('price'):,} if alert.get('price') else 'Any price'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 VIEW FULL LISTING:
{listing_url}

⚡ ACT FAST! Good properties get rented quickly.

💡 Next Steps:
1. Visit the listing URL above
2. Contact the landlord/agent immediately
3. Schedule a viewing as soon as possible
4. Prepare your documents (ID, pay stubs, references)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To manage your alerts, please contact our support team.

Best regards,
Property Alert System

---
This alert was triggered by new listing added on {datetime.now().strftime('%Y-%m-%d at %I:%M %p')}
"""
            
            # Send email
            result = self.email_service.send_email(email, subject, message)
            logger.info(f"Email notification sent to {email}: {result}")
            
            return "successfully" in result.lower()
            
        except Exception as e:
            logger.error(f"Error sending notification to {alert.get('email')}: {e}")
            return False

    def process_new_listing(self, listing: Dict[str, Any]) -> Dict[str, int]:
        """
        Process a new listing: find matching alerts and send notifications.
        
        Args:
            listing: New listing document
            
        Returns:
            dict: Statistics about notifications sent
        """
        stats = {
            "alerts_checked": 0,
            "matches_found": 0,
            "emails_sent": 0,
            "errors": 0
        }
        
        try:
            listing_id = listing.get("_id")
            address = listing.get("address", "Unknown")
            price = listing.get("price", 0)
            
            logger.info(f"Processing new listing: {listing_id}")
            logger.info(f"  Address: {address}")
            logger.info(f"  Price: ${price}")
            
            # Find matching alerts
            matching_alerts = self.find_matching_alerts(listing)
            stats["matches_found"] = len(matching_alerts)
            stats["alerts_checked"] = self.alerts_collection.count_documents({"status": "active"})
            
            if not matching_alerts:
                logger.info("No matching alerts found for this listing")
                return stats
            
            logger.info(f"Found {len(matching_alerts)} matching alerts!")
            
            # Send notifications to all matching alerts
            for alert in matching_alerts:
                try:
                    success = self.send_notification(alert, listing)
                    if success:
                        stats["emails_sent"] += 1
                    else:
                        stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Error processing alert {alert.get('_id')}: {e}")
                    stats["errors"] += 1
            
            logger.info(f"Notification stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing new listing: {e}")
            stats["errors"] += 1
            return stats

    def watch_for_new_listings(self):
        """
        Watch the tulire_listings collection for new insertions using Change Streams.
        This runs continuously and processes each new listing in real-time.
        """
        logger.info("=" * 60)
        logger.info("Starting Change Stream Monitor for tulire_listings")
        logger.info("Watching for new property listings...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        try:
            # Create a change stream that watches for insert operations only
            pipeline = [
                {"$match": {"operationType": "insert"}}
            ]
            
            with self.listings_collection.watch(pipeline) as stream:
                logger.info("✓ Change stream connected successfully!")
                logger.info("Waiting for new listings...\n")
                
                for change in stream:
                    try:
                        logger.info("\n" + "=" * 60)
                        logger.info("🆕 NEW LISTING DETECTED!")
                        logger.info("=" * 60)
                        
                        # Extract the new listing document
                        new_listing = change["fullDocument"]
                        
                        # Process the listing and send notifications
                        stats = self.process_new_listing(new_listing)
                        
                        # Log summary
                        logger.info("\n📊 Processing Summary:")
                        logger.info(f"  ✓ Active alerts checked: {stats['alerts_checked']}")
                        logger.info(f"  ✓ Matching alerts found: {stats['matches_found']}")
                        logger.info(f"  ✓ Emails sent: {stats['emails_sent']}")
                        logger.info(f"  ✗ Errors: {stats['errors']}")
                        logger.info("=" * 60 + "\n")
                        
                    except Exception as e:
                        logger.error(f"Error processing change event: {e}")
                        continue
                        
        except KeyboardInterrupt:
            logger.info("\n\nStopping change stream monitor...")
            logger.info("Monitor stopped by user")
            
        except PyMongoError as e:
            logger.error(f"MongoDB error: {e}")
            logger.error("Make sure MongoDB is configured as a replica set for change streams")
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


def test_with_existing_listing():
    """
    Test the notification system with an existing listing from the database.
    Useful for testing without inserting new data.
    """
    logger.info("Running test with existing listing...")
    
    try:
        monitor = ListingMonitor()
        
        # Get one listing from the database
        sample_listing = monitor.listings_collection.find_one()
        
        if not sample_listing:
            logger.error("No listings found in database for testing")
            return
        
        logger.info(f"Testing with listing: {sample_listing.get('address')}")
        
        # Process as if it's a new listing
        stats = monitor.process_new_listing(sample_listing)
        
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(f"Active alerts checked: {stats['alerts_checked']}")
        print(f"Matching alerts found: {stats['matches_found']}")
        print(f"Emails sent: {stats['emails_sent']}")
        print(f"Errors: {stats['errors']}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    import sys
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Property Listing Monitor - Real-Time Alerts          ║
║     Watches for new listings and triggers alerts         ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - use existing listing
        test_with_existing_listing()
    else:
        # Production mode - watch for changes
        try:
            monitor = ListingMonitor()
            monitor.watch_for_new_listings()
        except Exception as e:
            logger.error(f"Failed to start monitor: {e}")
            print("\n⚠️  ERROR: Could not start change stream monitor")
            print("Make sure MongoDB is running as a replica set!")
            print("\nTo enable replica set:")
            print("1. Add to mongod.conf: replication.replSetName: 'rs0'")
            print("2. Restart MongoDB")
            print("3. Run: mongosh --eval 'rs.initiate()'")