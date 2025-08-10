import json
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()
from agents.Prompts import *
from models.ListingInfo import Listing
from duplicates import CatchDuplicateListings
from database.mongo_client import MongoDBClient
from agents.ListingParser import parseHouseListing
from agents.scam_checker import checkIfListingIsValid

listing_text = """
*Permanent Accommodation available.”

Newly renovated apartment
Available starting August 1st onwards 
2 people ideally, max 3

Address -  Pierce Ave, Heights, Jersey City, NJ, 07307
🏠 Apartment Details 🏠
Garden level unit
2 Bedrooms
1 Bathroom

Rent: $1750 (includes free Wi-Fi, heat, and water)

Amenities include:
Dishwasher and Laundry in the unit

(NO-SMOKING)

No Broker Fee. Security Deposit - 1.5 Month Rent.

Please text if you have any questions: 
6174705145
"""


def extractDetails(listing:str):

    # 🚨 Step 1: SCAM DETECTION (on raw listing_text)
    scam_result_raw = checkIfListingIsValid(listing_text)
    if  scam_result_raw is "YES":
        return "Listing Has a problem"

    listing_instance=parseHouseListing(listing)

    try:

        # ✅ Step 3: Connect to MongoDB
        mongo_client = MongoDBClient()
        collection = mongo_client.database["listings"]

        # 🔍 Step 4: Check for duplicates
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

        # 💾 Step 5: Store the listing
        result = collection.insert_one(listing_dict)
        print(json.dumps(listing_dict, indent=4, default=convert_objectid))
        print(f"\n✅ Listing stored in MongoDB with ID: {result.inserted_id}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Raw LLM response: {response}")

def getPromptMessagesAndFormat(parser):
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", human_prompt_template)
    ])
    formatted_prompt = chat_prompt.format_messages(format_instructions=parser.get_format_instructions(),
                                                   input=listing_text)
    return formatted_prompt

def extractDetailsV2():
    return None
    #
    # try:
    #     extracted_data = json.loads(raw_text)
    #     parsed_listing = Listing(**extracted_data)
    #     listing_dict = parsed_listing.model_dump()
    #
    #     mongo_client = MongoDBClient()  # Will auto use DATABASE_NAME from .env
    #     collection = mongo_client.database["listings"]
    #
    #     duplicate_checker = CatchDuplicateListings()
    #
    #     existing_listings = list(collection.find({
    #         "contact.phone_numbers": {"$in": listing_dict["contact"]["phone_numbers"]}
    #     }))
    #
    #     is_duplicate, matched_listing = duplicate_checker.is_similar_listing(listing_dict, existing_listings)
    #
    #     if is_duplicate:
    #         print("⚠️ Similar listing already exists:")
    #         print(json.dumps(matched_listing, indent=4, default=convert_objectid))
    #         print("\n❗Skipping insertion.")
    #         return
    #
    #     # ✅ Save the listing and print confirmation
    #     result = collection.insert_one(listing_dict)
    #     print(json.dumps(listing_dict, indent=4, default=convert_objectid))  # Only print non-duplicate
    #     print(f"\n✅ Listing stored in MongoDB with ID: {result.inserted_id}")
    #
    # except json.JSONDecodeError as e:
    #     print(f"Error decoding JSON: {e}")
    #     print(f"Raw LLM response: {response}")
