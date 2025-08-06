from itertools import chain
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import os
from dotenv import load_dotenv
load_dotenv()
from Prompts import *
from langchain.chains import LLMChain
from models.ListingInfo import Listing
from MongoDB import MongoDBClient
from duplicates import CatchDuplicateListings
from bson import ObjectId


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


# Initialize Gemini Pro
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.2,
    google_api_key="AIzaSyCK33vqrJ9XZKmC6zgwEEgvld90HAfhuR8",
)
def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def extractDetails():
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", human_prompt_template)
    ])

    chain = chat_prompt | llm
    response = chain.invoke({"listing": listing_text})
    raw_text = response.content.strip() if hasattr(response, "content") else response['text'].strip()

    # Remove markdown code block formatting
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

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

        # ✅ Save the listing and print confirmation
        result = collection.insert_one(listing_dict)
        print(json.dumps(listing_dict, indent=4, default=convert_objectid))  # Only print non-duplicate
        print(f"\n✅ Listing stored in MongoDB with ID: {result.inserted_id}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Raw LLM response: {response}")

extractDetails()