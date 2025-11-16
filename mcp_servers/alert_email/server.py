import logging
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from db.connection import MongoDBClient
from mcp_servers.alert_email.utilities.parser import UserMessageParser
from bson import ObjectId
from mcp_servers.alert_email.utilities.listing_monitor import ListingMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alert_mcp")

mcp = FastMCP(
    "alert_service",
    host="localhost",
    port=9002,
    stateless_http=True
)

# ---------- DB Setup ----------
try:
    db_client = MongoDBClient(database_name="rental_database")
    alert_collection = db_client.database["alert_mongodb"]
    listings_collection = db_client.database["tulire_listings"]
    
    # Create indexes for efficient queries
    alert_collection.create_index("email")
    alert_collection.create_index("location")
    alert_collection.create_index([("email", 1), ("location", 1)])
    
    logger.info("Connected to MongoDB - alert_mongodb and tulire_listings collections")
except Exception as e:
    alert_collection = None
    listings_collection = None
    logger.error(f"MongoDB connection failed: {e}")

# Initialize parser
parser = UserMessageParser()

# ---------------------------------------------------------------
# TOOL 1 – Create Alert
# ---------------------------------------------------------------
@mcp.tool()
def create_alert(user_message: str) -> str:
    """
    Parse user message and create a property alert.
    
    Extracts email, location, and price from natural language input.
    Saves alert to MongoDB for future notifications.
    
    Args:
        user_message: Natural language message containing alert preferences
                     Example: "Alert me for 2BHK in Bangalore under 30k at john@example.com"
    
    Returns:
        Success message with alert details and ID, or error message
    """
    if alert_collection is None:
        return "❌ MongoDB is not connected."
    
    try:
        # Parse the user message
        parsed = parser.extract(user_message)
        
        email = parsed.get("email")
        location = parsed.get("location")
        price = parsed.get("price")
        
        # Validate required field
        if not email:
            return """
❌ Email address is required to create an alert.

Please provide your email address in the message.
Example: "Alert me for properties in Bangalore at john.doe@gmail.com"
"""
        
        # Create alert document
        alert_doc = {
            "email": email.lower().strip(),
            "location": location.strip() if location else None,
            "price": price,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "original_message": user_message
        }
        
        # Save to database
        result = alert_collection.insert_one(alert_doc)
        alert_id = str(result.inserted_id)
        
        # Format response - FIXED VERSION
        price_display = f"${price:,}" if price else "Any price"
        location_display = location if location else "Any location"
        
        response = f"""
✅ Alert Created Successfully!

**Alert ID**: {alert_id}
**Email**: {email}
**Location**: {location_display}
**Max Price**: {price_display}

📧 You'll receive notifications when new properties matching your criteria are listed.

To manage your alerts:
- View all alerts: call `get_user_alerts(email="{email}")`
- Delete this alert: call `delete_alert(alert_id="{alert_id}")`
"""
        
        logger.info(f"Alert created: {alert_id} for {email}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return f"❌ Error creating alert: {str(e)}"

# ---------------------------------------------------------------
# TOOL 2 – Get User Alerts
# ---------------------------------------------------------------
@mcp.tool()
def get_user_alerts(email: str) -> str:
    """
    Get all alerts for a specific email address.
    
    Args:
        email: User's email address
    
    Returns:
        Formatted list of all alerts for the user
    """
    if alert_collection is None:
        return "❌ MongoDB is not connected."
    
    try:
        alerts = list(alert_collection.find(
            {"email": email.lower().strip(), "status": "active"}
        ).sort("created_at", -1))
        
        if not alerts:
            return f"""
🔭 No active alerts found for {email}

Would you like to create one? 
Example: "Alert me for 2BHK in Bangalore under 30k at {email}"
"""
        
        response = f"📬 Found {len(alerts)} active alert(s) for {email}:\n\n"
        
        for i, alert in enumerate(alerts, 1):
            alert_id = str(alert["_id"])
            location = alert.get("location", "Any location")
            price = alert.get("price")
            created = alert.get("created_at").strftime("%Y-%m-%d %H:%M")
            price_display = f"${price:,}" if price else "Any price"
            
            response += f"""
**Alert {i}**
- ID: {alert_id}
- Location: {location}
- Max Price: {price_display}
- Created: {created}
─────────────────────────
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        return f"❌ Error retrieving alerts: {str(e)}"

# ---------------------------------------------------------------
# TOOL 3 – Delete Alert
# ---------------------------------------------------------------
@mcp.tool()
def delete_alert(alert_id: str) -> str:
    """
    Delete an alert permanently.
    
    Args:
        alert_id: MongoDB ObjectId of the alert to delete
    
    Returns:
        Success or error message
    """
    if alert_collection is None:
        return "❌ MongoDB is not connected."
    
    try:
        object_id = ObjectId(alert_id)
        
        # Get alert details before deletion
        existing = alert_collection.find_one({"_id": object_id})
        if not existing:
            return f"❌ Alert not found with ID: {alert_id}"
        
        email = existing.get("email")
        location = existing.get("location", "Any location")
        
        # Delete the alert
        result = alert_collection.delete_one({"_id": object_id})
        
        if result.deleted_count > 0:
            return f"""
✅ Alert Deleted Successfully!

**Deleted Alert:**
- ID: {alert_id}
- Email: {email}
- Location: {location}

The alert has been permanently removed.
"""
        else:
            return f"❌ Failed to delete alert with ID: {alert_id}"
        
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        return f"❌ Error deleting alert: {str(e)}"


# ---------------------------------------------------------------
# TOOL 5 – Search Matching Listings
# ---------------------------------------------------------------
@mcp.tool()
def search_matching_listings(location: str = None, max_price: int = None) -> str:
    """
    Search for property listings that match the given criteria.
    
    Args:
        location: Location to search for (optional, case-insensitive)
        max_price: Maximum price filter (optional)
    
    Returns:
        Formatted list of matching properties
    """
    if listings_collection is None:
        return "❌ MongoDB is not connected."
    
    try:
        # Build query
        query = {}
        
        if location:
            # Case-insensitive search in address field
            query["address"] = {"$regex": location, "$options": "i"}
        
        if max_price:
            # Filter by price less than or equal to max_price
            query["price"] = {"$lte": max_price}
        
        # Execute query
        listings = list(listings_collection.find(query).limit(20))
        
        if not listings:
            return f"""
🔍 No listings found matching your criteria:
- Location: {location if location else "Any"}
- Max Price: ${max_price:,} if max_price else "Any"
"""
        
        response = f"🏠 Found {len(listings)} matching listing(s):\n\n"
        
        for i, listing in enumerate(listings, 1):
            listing_id = str(listing.get("_id", ""))
            address = listing.get("address", "N/A")
            price = listing.get("price", 0)
            bedrooms = listing.get("bedroom", "N/A")
            bathrooms = listing.get("bathroom", "N/A")
            description = listing.get("description", "")[:100]
            listing_url = listing.get("listing_url", "")
            
            response += f"""
**Listing {i}**
- Address: {address}
- Price: ${price:,}
- Bedrooms: {bedrooms} | Bathrooms: {bathrooms}
- Description: {description}...
- URL: {listing_url}
─────────────────────────
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Error searching listings: {e}")
        return f"❌ Error searching listings: {str(e)}"


# ---------------------------------------------------------------
# TOOL 6 – Process Single Listing Against Alerts (NEW)
# ---------------------------------------------------------------
@mcp.tool()
def check_listing_for_alerts(listing_id: str) -> str:
    """
    Check if a specific listing matches any active alerts and send notifications.
    This is useful for manually triggering alert checks for a new listing.
    
    Args:
        listing_id: MongoDB ObjectId of the listing to check
    
    Returns:
        Summary of notifications sent
    """
    if alert_collection is None or listings_collection is None:
        return "❌ MongoDB is not connected."
    
    try:
        
        # Get the listing
        listing = listings_collection.find_one({"_id": ObjectId(listing_id)})
        
        if not listing:
            return f"❌ Listing not found with ID: {listing_id}"
        
        # Process listing through monitor
        monitor = ListingMonitor()
        stats = monitor.process_new_listing(listing)
        
        return f"""
✅ Listing Checked Against Alerts!

📊 Summary:
- Listing: {listing.get('address', 'N/A')}
- Price: ${listing.get('price', 0):,}
- Active alerts checked: {stats['alerts_checked']}
- Matching alerts found: {stats['matches_found']}
- Emails sent: {stats['emails_sent']}
- Errors: {stats['errors']}
"""
        
    except Exception as e:
        logger.error(f"Error checking listing: {e}")
        return f"❌ Error: {str(e)}"


# ---------------------------------------------------------------
# TOOL 7 – Get All Alerts (Admin)
# ---------------------------------------------------------------
@mcp.tool()
def get_all_alerts() -> str:
    """
    Get all active alerts in the system (admin function).
    
    Returns:
        Summary of all active alerts
    """
    if alert_collection is None:
        return "❌ MongoDB is not connected."
    
    try:
        alerts = list(alert_collection.find({"status": "active"}).sort("created_at", -1))
        
        if not alerts:
            return "🔭 No active alerts in the system."
        
        response = f"📊 **Alert System Summary**\n\n"
        response += f"Total Active Alerts: {len(alerts)}\n\n"
        
        # Group by location
        by_location = {}
        for alert in alerts:
            loc = alert.get("location", "Any location")
            by_location[loc] = by_location.get(loc, 0) + 1
        
        response += "**Alerts by Location:**\n"
        for loc, count in sorted(by_location.items(), key=lambda x: x[1], reverse=True):
            response += f"- {loc}: {count} alerts\n"
        
        # Price distribution
        with_price = sum(1 for a in alerts if a.get("price"))
        response += f"\n**Price Criteria:**\n"
        response += f"- With price limit: {with_price}\n"
        response += f"- Any price: {len(alerts) - with_price}\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting all alerts: {e}")
        return f"❌ Error retrieving alerts: {str(e)}"


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Alert MCP Server running on port 9002")
    mcp.run(transport="streamable-http")