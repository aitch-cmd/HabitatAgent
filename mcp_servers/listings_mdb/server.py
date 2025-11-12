import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from db.connection import MongoDBClient
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts.chat import ChatPromptTemplate
from mcp_servers.listings_mdb.utilities.parser import ParserListings

mcp=FastMCP(
    "listings_mongodb",
    host="localhost",
    port=9001,
    stateless_http=True
)

db_client = MongoDBClient(database_name="rental_database")
collection = db_client.database["tulire_listings"]

parser = ParserListings()

def format_listing_summary(listing_data: Dict[str, Any]) -> str:
    """
    Format listing data into a readable summary for user confirmation
    """
    summary = f"""
**Property Listing Summary**
━━━━━━━━━━━━━━━━━━━━━━━━━━
**Address**: {listing_data.get('address', 'Not specified')}
**Monthly Rent**: ${listing_data.get('price', 0)}
**Bedrooms**: {listing_data.get('bedrooms', 'Not specified')}
**Bathrooms**: {listing_data.get('bathrooms', 'Not specified') if listing_data.get('bathrooms') else 'Not specified'}

📋 **Description**:
{listing_data.get('description', 'No description provided')}

**Application Fee**: {listing_data.get('application_fee', 'Not specified')}
**Lease Terms**: {listing_data.get('lease_terms', 'Not specified')}
**Security Deposit**: {listing_data.get('security_deposit', 'Not specified')}
**Contact**: {listing_data.get('contact', 'Not specified')}

**Amenities**: {', '.join(listing_data.get('amenities', [])) if listing_data.get('amenities') else 'None specified'}
**Utilities Included**: {', '.join(listing_data.get('utilities_included', [])) if listing_data.get('utilities_included') else 'None'}
**Pet Friendly**: {listing_data.get('pet_friendly', 'Not specified') if listing_data.get('pet_friendly') else 'Not specified'}
**Listing URL**: {listing_data.get('listing_url', 'None provided') if listing_data.get('listing_url') else 'None provided'}
━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return summary

@mcp.tool()
def parse_and_confirm_listing(raw_listing: str, user_confirmation: str = "pending") -> str:
    """
    Parse unstructured property listing text, show summary, and save to MongoDB after user confirmation.
    
    This tool handles the complete flow:
    1. Parse the raw listing text
    2. Show formatted summary
    3. Wait for user confirmation (yes/no)
    4. Save to MongoDB if confirmed, or ask what to change if rejected
    
    Args:
        raw_listing: Unstructured text containing property listing information
        user_confirmation: User's confirmation response - "yes" to confirm and save, "no" to modify, "pending" for initial parse
        
    Returns:
        Summary for confirmation (if pending), success message (if yes), or prompt for changes (if no)
    """
    try:
        parsed_data = parser.extract(raw_listing)
        
        if parsed_data.get("Parsed Text") is None:
            return "Error: Failed to parse the listing. Please check the format and try again."
        
        # Add metadata fields
        parsed_data["source"] = "user_created"
        parsed_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        
        # Format summary
        summary = format_listing_summary(parsed_data)
        
        # Handle user confirmation
        confirmation_lower = user_confirmation.lower().strip()
        
        if confirmation_lower in ["pending", "parse", "show"]:
            # Just show the summary and wait for confirmation
            return f"""{summary}

Please respond with:
- **'yes'** to confirm and save this listing
- **'no'** if you'd like to make changes
"""
        
        elif confirmation_lower in ["yes", "y", "confirm", "approve", "save"]:
            # User confirmed - save to MongoDB
            result = collection.insert_one(parsed_data)
            
            # Extract info for display
            address = parsed_data.get('address', '')
            city = address.split(',')[0].strip() if ',' in address else 'Unknown Location'
            
            bedrooms = parsed_data.get('bedrooms', 'N/A')
            bathrooms = parsed_data.get('bathrooms', 'N/A')
            bathrooms_display = f"{bathrooms}BA" if bathrooms else "N/A"
            
            rental_terms = parsed_data.get('rental_terms', {}) or {}
            rent = rental_terms.get('rent', 'N/A')
            
            success_message = f"""✅ **Listing Created Successfully!**

Your property listing has been created and is now live in our database.

**Listing Details**:
- **Property**: {bedrooms}BR/{bathrooms_display} in {city}
- **Monthly Rent**: {rent}
- **Database ID**: `{str(result.inserted_id)}`

Renters can now search and find your property. You'll be contacted at {parsed_data.get('contact', 'N/A')} when someone is interested.

Would you like to create another listing?
"""
            return success_message
        
        elif confirmation_lower in ["no", "n", "reject", "change", "modify", "edit"]:
            # User wants to make changes - provide guidance
            return f"""{summary}

I understand you'd like to make some changes. Please tell me:

**What would you like to change?**

You can specify:
- Field name and new value (e.g., "Change price to 35000" or "Update bedrooms to 3")
- Multiple changes (e.g., "Change price to 35000 and bedrooms to 3")

**Available fields to modify:**
- address, price, bedrooms, bathrooms, description
- contact, pet_friendly, listing_url
- rental_terms.rent, rental_terms.application_fee, rental_terms.security_deposit
- rental_terms.lease_terms, rental_terms.availability
- amenities.appliances, amenities.utilities_included, amenities.other_amenities

Once you tell me what to change, I'll update the listing and show you the new summary for confirmation.
"""
        
        else:
            # Invalid response - show summary again
            return f"""{summary}

Invalid response. Please respond with:
- **'yes'** to confirm and save
- **'no'** to make changes
"""
        
    except Exception as e:
        return f"❌ Error: {str(e)}\n\nPlease check your input and try again."
    

@mcp.tool()
def update_listing_fields(parsed_listing_json: str, changes_description: str) -> str:
    """
    Update specific fields in a parsed listing based on user's change request.
    
    Args:
        parsed_listing_json: JSON string of the previously parsed listing data
        changes_description: Natural language description of what to change (e.g., "change price to 35000 and bedrooms to 3")
        
    Returns:
        Updated summary with modified fields for confirmation
    """
    try:
        # Parse the listing data from JSON
        listing_data = json.loads(parsed_listing_json)
        
        change_prompt = f"""Based on this change request: "{changes_description}"
        
Extract the field updates needed. Return in this format:
- field_name: new_value

Current listing data:
{json.dumps(listing_data, indent=2)}
"""
        
        # For now, let's do simple keyword matching
        # In production, you might want to use LLM to parse the changes
        changes_lower = changes_description.lower()
        
        # Common field mappings
        field_keywords = {
            'price': ['price', 'rent amount', 'cost'],
            'bedrooms': ['bedroom', 'bed', 'br'],
            'bathrooms': ['bathroom', 'bath', 'ba'],
            'address': ['address', 'location'],
            'description': ['description', 'desc'],
            'contact': ['contact', 'phone', 'email'],
            'pet_friendly': ['pet', 'pets'],
            'listing_url': ['url', 'link'],
        }
        
        # Try to extract numeric values for price/bedrooms/bathrooms
        import re
        numbers = re.findall(r'\d+', changes_description)
        
        # Simple update logic (can be enhanced)
        if any(kw in changes_lower for kw in field_keywords['price']) and numbers:
            listing_data['price'] = int(numbers[0])
            if 'rental_terms' in listing_data and listing_data['rental_terms']:
                listing_data['rental_terms']['rent'] = f"₹{numbers[0]}/month"
        
        if any(kw in changes_lower for kw in field_keywords['bedrooms']) and numbers:
            listing_data['bedrooms'] = int(numbers[-1])
        
        if any(kw in changes_lower for kw in field_keywords['bathrooms']) and numbers:
            listing_data['bathrooms'] = int(numbers[-1])
        
        # Update last_updated
        listing_data['last_updated'] = datetime.now().strftime("%Y-%m-%d")
        
        # Format updated summary
        summary = format_listing_summary(listing_data)
        
        return f"""**Listing Updated!**

{summary}

**Does this look correct now?**

Please respond with:
- **'yes'** to confirm and save
- **'no'** to make more changes

**Updated listing data** (for next update call):
```json
{json.dumps(listing_data, indent=2)}
```
"""
        
    except json.JSONDecodeError:
        return "❌ Error: Invalid listing data format. Please start over with parse_and_confirm_listing."
    except Exception as e:
        return f"❌ Error updating fields: {str(e)}"


@mcp.tool()
def save_listing(parsed_listing_json: str) -> str:
    """
    Save a confirmed listing to MongoDB without re-parsing.
    
    Args:
        parsed_listing_json: JSON string of the parsed and confirmed listing data
        
    Returns:
        Success message with MongoDB document ID
    """
    try:
        # Parse the listing data from JSON
        listing_data = json.loads(parsed_listing_json)
        
        # Ensure metadata is set
        listing_data["source"] = "user_created"
        listing_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        
        # Save to MongoDB
        result = collection.insert_one(listing_data)
        
        # Extract info for display
        address = listing_data.get('address', '')
        city = address.split(',')[0].strip() if ',' in address else 'Unknown Location'
        
        bedrooms = listing_data.get('bedrooms', 'N/A')
        bathrooms = listing_data.get('bathrooms', 'N/A')
        bathrooms_display = f"{bathrooms}BA" if bathrooms else "N/A"
        
        rental_terms = listing_data.get('rental_terms', {}) or {}
        rent = rental_terms.get('rent', 'N/A')
        
        success_message = f"""✅ **Listing Created Successfully!**

Your property listing has been created and is now live in our database.

**Listing Details**:
- **Property**: {bedrooms}BR/{bathrooms_display} in {city}
- **Monthly Rent**: {rent}
- **Database ID**: `{str(result.inserted_id)}`

Renters can now search and find your property. You'll be contacted at {listing_data.get('contact', 'N/A')} when someone is interested.

Would you like to create another listing?
"""
        return success_message
        
    except json.JSONDecodeError:
        return "❌ Error: Invalid listing data format."
    except Exception as e:
        return f"❌ Error saving listing: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server on port 9001
    print("🚀 Starting Property Listing Parser MCP Server on port 9001...")
    print("📡 Using Google Gemini parser (parser.py)")
    print(f"🗄️  Connected to MongoDB: rental_database.tulire_listings")
    print("✅ Server is ready to accept connections")
    mcp.run()