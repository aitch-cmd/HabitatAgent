import json
import os
import sys
from dotenv import load_dotenv

# Add project root to the Python path to resolve module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

from listingParser.duplicates import CatchDuplicateListings
from database.mongodb_client import MongoDBClient
from agentsV1.ListingParser import parseHouseListing
from agentsV1.scam_checker import checkIfListingIsValid
from models.ListingInfo import Listing
from listingRetrieval.retrieval import convert_objectid

listing_text = """
🏡 Full 1-Bedroom  Apartment for Rent – Not for Sharing
Spacious 1-bedroom apartment available for rent starting September 1st Poplar St, Jersey City.

🛋️ Features:
– Large living area
– Separate dining space
– 1bedroom unit (not for sharing)
– Clean and quiet environment
– Prime location with easy access to transportation and nearby stores

📍 Location: Poplar St, Jersey City, NJ
📅 Move-in Date: urgent

🚫 Only serious inquiries will be considered.
"""


def extractDetails(listing:str):

    # # 🚨 Step 1: SCAM DETECTION (on raw listing_text)
    # scam_result_raw = checkIfListingIsValid(listing_text)
    # if  scam_result_raw == "YES":
    #     return "Listing Has a problem initate the sequencing for the folder."

    listing_instance=parseHouseListing(listing)
    if not listing_instance:
        print(listing_instance)
    try:
        mongo_client = MongoDBClient()
        collection = mongo_client.database["listings"]
        duplicateListingChecker=CatchDuplicateListings()
        duplicateListingQuery=duplicateListingChecker.getDuplicateListingQuery(listing_instance)
        existing = collection.find_one(duplicateListingQuery)
        if existing:
            print("⚠️ Similar listing already exists:")
            print(json.dumps(existing, indent=4, default=convert_objectid))
            print("\n❗Skipping insertion.")
            return "Similar listing already exists. Skipping insertion."
        result = collection.insert_one(listing_instance.model_dump())
        print(f"\n✅ Listing stored in MongoDB with ID: {result.inserted_id}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Raw LLM response:")

def extractDetailsV2():
    
    try:
        extracted_data = json.loads(raw_text)
        parsed_listing = Listing(**extracted_data)
        listing_dict = parsed_listing.model_dump()
    
        mongo_client = MongoDBClient()  # Will auto use DATABASE_NAME from .env
        collection = mongo_client.database["listings"]
    
        duplicate_checker = CatchDuplicateListings()
    
        existing_listings = list(collection.find({
            "contact.phone_numbers": {"$in": listing_dict["contact"]["phone_numbers"]}
        }))
    
        is_duplicate, matched_listing = duplicate_checker.is_similar_listing(listing_dict, existing_listings)
    
        if is_duplicate:
            print("⚠️ Similar listing already exists:")
            print(json.dumps(matched_listing, indent=4, default=convert_objectid))
            print("\n❗Skipping insertion.")
            return
    
        result = collection.insert_one(listing_dict)
        print(f"\n✅ Listing stored in MongoDB with ID: {result.inserted_id}")
        return f"Listing has been saved. The ID is: {result.inserted_id}"

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return "Failed to parse the listing data."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred while processing the listing."


if __name__ == "__main__":
    result_message = extractDetails(listing=listing_text)
    print(f"\n--- Operation Result ---\n{result_message}")