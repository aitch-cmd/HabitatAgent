import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Tuple
from bson import ObjectId
from mcp.server.fastmcp import FastMCP
from db.connection import MongoDBClient
from mcp_servers.listings_mdb.utilities.parser import ParserListings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("listings_mcp")

mcp = FastMCP(
    "listings_mongodb",
    host="localhost",
    port=9001,
    stateless_http=True
)

# ---------- DB Setup ----------
try:
    db_client = MongoDBClient(database_name="rental_database")
    collection = db_client.database["tulire_listings"]
    logger.info("Connected to MongoDB.")
except Exception as e:
    collection = None
    logger.error(f"MongoDB connection failed: {e}")

parser = ParserListings()

# ---------------------------------------------------------------
# Formatting & Validation
# ---------------------------------------------------------------

def format_listing_summary(data: Dict[str, Any]) -> str:
    def fmt(v, default="Not specified"):
        return v if v not in ["", None, []] else default

    rental = data.get("rental_terms") or {}

    amenities = data.get("amenities") or {}
    amenities_flat = (
        amenities.get("appliances", []) +
        amenities.get("utilities_included", []) +
        amenities.get("other_amenities", [])
    )

    return f"""
**Property Listing Summary**
━━━━━━━━━━━━━━━━━━━━━━━━━━
**Address**: {fmt(data.get("address"))}
**Monthly Rent**: ₹{fmt(data.get("price"))}
**Bedrooms**: {fmt(data.get("bedrooms"))}
**Bathrooms**: {fmt(data.get("bathrooms"))}

📋 **Description**:
{fmt(data.get("description"))}

**Application Fee**: {fmt(rental.get("application_fee"))}
**Security Deposit**: {fmt(rental.get("security_deposit"))}
**Lease Terms**: {fmt(rental.get("lease_terms"))}
**Availability**: {fmt(rental.get("availability"))}
**Contact**: {fmt(data.get("contact"))}

**Pet Friendly**: {fmt(data.get("pet_friendly"))}
**Amenities**: {", ".join(amenities_flat) if amenities_flat else "None"}
**Listing URL**: {fmt(data.get("listing_url"))}
━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def validate_listing(d: Dict[str, Any]) -> Tuple[bool, list]:
    errors = []
    if not d.get("address"):
        errors.append("address missing")
    if not d.get("price"):
        errors.append("price missing")
    if not d.get("bedrooms"):
        errors.append("bedrooms missing")
    if not d.get("description"):
        errors.append("description missing")
    return (len(errors) == 0, errors)

# ---------------------------------------------------------------
# TOOL 1 – Parse
# ---------------------------------------------------------------

@mcp.tool()
@mcp.tool()
def parse_and_confirm_listing(raw_listing: str) -> str:
    """
    Parse listing text → return normalized JSON + summary.
    (Does NOT save to DB.)
    """
    try:
        parsed = parser.extract(raw_listing)
        
        if not parsed or parsed.get("error"):
            error_msg = parsed.get("error", "Unknown parsing error") if parsed else "Parser returned None"
            logger.error(f"Parsing failed: {error_msg}")
            return f"❌ Error parsing listing: {error_msg}"
        
        if not parsed.get("address") or not parsed.get("price"):
            return "❌ Error: Missing required fields (address or price)"
        
        # Add metadata
        parsed["source"] = "user_created"
        parsed["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        ok, errs = validate_listing(parsed)
        summary = format_listing_summary(parsed)

        return f"""
{summary}

Validation: {"OK" if ok else ", ".join(errs)}

Next actions:
- To save → call **save_listing(parsed_listing_json)**
- To modify → call **update_listing_fields(parsed_listing_json, changes_description)**

Parsed JSON:
```json
{json.dumps(parsed, indent=2)}
```
"""
    except Exception as e:
        logger.error(f"Exception in parse_and_confirm_listing: {str(e)}")
        return f"❌ Error parsing listing: {str(e)}"

# ---------------------------------------------------------------
# TOOL 2 – Update fields
# ---------------------------------------------------------------
@mcp.tool()
def update_listing_fields(parsed_listing_json: str, changes_description: str) -> str:
    """
    Update the listing data based on natural language edit requests.
    """
    try:
        data = json.loads(parsed_listing_json)
    except:
        return "❌ Invalid JSON input."

    text = changes_description.lower()

    # --- numeric updates ---
    numbers = re.findall(r"\d+", text)

    def apply_numeric(field):
        if field in text and numbers:
            data[field] = int(numbers[0])

    apply_numeric("price")
    apply_numeric("bedrooms")
    apply_numeric("bathrooms")

    # --- rental terms ---
    rental = data.get("rental_terms") or {}

    if "application fee" in text and numbers:
        rental["application_fee"] = numbers[0]

    if "security deposit" in text and numbers:
        rental["security_deposit"] = numbers[0]

    if "lease" in text:
        m = re.search(r"lease.*?(\d+\s*\w+)", text)
        if m:
            rental["lease_terms"] = m.group(1)

    data["rental_terms"] = rental

    # --- pet friendly ---
    if "pet" in text:
        if any(x in text for x in ["yes", "allowed", "friendly"]):
            data["pet_friendly"] = "yes"
        elif any(x in text for x in ["no", "not allowed"]):
            data["pet_friendly"] = "no"

    # --- amenities updates ---
    amenities = data.get("amenities") or {}

    # add amenity
    m = re.findall(r"(?:add|include)\s+([a-zA-Z0-9 ]+)", text)
    if m:
        amenities.setdefault("other_amenities", [])
        amenities["other_amenities"].extend([x.strip() for x in m])

    # remove amenity
    r = re.findall(r"(?:remove|delete)\s+([a-zA-Z0-9 ]+)", text)
    if r:
        for item in r:
            for k in ["appliances", "utilities_included", "other_amenities"]:
                if item in amenities.get(k, []):
                    amenities[k].remove(item)

    data["amenities"] = amenities

    # --- freeform fields ---
    def str_update(field):
        if field in text:
            m = re.search(field + r"\s*to\s*(.*)", text)
            if m:
                data[field] = m.group(1).strip()

    str_update("address")
    str_update("description")
    str_update("contact")
    str_update("listing_url")

    # update timestamp
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    ok, errs = validate_listing(data)
    summary = format_listing_summary(data)

    return f"""
Listing Updated

{summary}

Validation: {"OK" if ok else ", ".join(errs)}

Next:
- Call **save_listing(parsed_listing_json)** to save
- Or modify again

Updated JSON:
```json
{json.dumps(data, indent=2)}
```
"""

# ---------------------------------------------------------------
# TOOL 3 – Save
# ---------------------------------------------------------------
@mcp.tool()
def save_listing(parsed_listing_json: str) -> str:
    """
    Saves the final listing into MongoDB.
    """
    if collection is None:
        return "❌ MongoDB is not connected."

    try:
        data = json.loads(parsed_listing_json)
    except:
        return "❌ Invalid JSON."

    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    try:
        result = collection.insert_one(data)
    except Exception as e:
        return f"❌ Error saving to DB: {e}"

    return f"""
✅ Listing Saved Successfully

Database ID: {result.inserted_id}

Your listing is now live.
"""

# ---------------------------------------------------------------
# TOOL 4 – Delete
# ---------------------------------------------------------------
@mcp.tool()
def delete_listing(listing_id: str) -> str:
    """
    Delete a listing from MongoDB using its ID.
    
    Args:
        listing_id: The MongoDB ObjectId of the listing to delete (as string)
    
    Returns:
        Success or error message
    """
    if collection is None:
        return "❌ MongoDB is not connected."
    
    try:
        # Convert string to ObjectId
        object_id = ObjectId(listing_id)
    except Exception as e:
        return f"❌ Invalid listing ID format: {e}"
    
    try:
        # First, check if the listing exists
        existing = collection.find_one({"_id": object_id})
        
        if not existing:
            return f"❌ Listing not found with ID: {listing_id}"
        
        # Show what's being deleted
        address = existing.get("address", "Unknown")
        price = existing.get("price", "N/A")
        
        # Delete the listing
        result = collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 1:
            return f"""
✅ Listing Deleted Successfully

**Deleted Listing:**
- ID: {listing_id}
- Address: {address}
- Price: ₹{price}

The listing has been permanently removed from the database.
"""
        else:
            return f"❌ Failed to delete listing with ID: {listing_id}"
            
    except Exception as e:
        logger.error(f"Error deleting listing: {e}")
        return f"❌ Error deleting listing: {e}"

# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 MCP Server running on port 9001")
    mcp.run(transport="streamable-http")