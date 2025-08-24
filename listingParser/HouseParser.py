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
from MongoDB.connection import MongoDBClient
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
    # 🚨 Step 1: SCAM DETECTION (on raw listing_text)
    scam_chain = ChatPromptTemplate.from_messages([
        ("system", fake_scam_agent),
        ("human", "{listing}")
    ]) | llm
    scam_result_raw = scam_chain.invoke({"listing": listing_text})
    scam_response = scam_result_raw.content.strip() if hasattr(scam_result_raw, "content") else scam_result_raw['text'].strip()

    if scam_response.upper() == "YES":
        print("❗ Scam listing detected. Skipping extraction and insertion.")
        return

    # ✅ Step 2: Extract listing details
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", human_prompt_template)
    ])
    chain = chat_prompt | llm
    response = chain.invoke({"listing": listing_text})
    raw_text = response.content.strip() if hasattr(response, "content") else response['text'].strip()

    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    try:
        extracted_data = json.loads(raw_text)
        parsed_listing = Listing(**extracted_data)
        listing_dict = parsed_listing.model_dump()

        #  Step 3: Connect to MongoDB
        mongo_client = MongoDBClient()
        collection = mongo_client.database["listings"]

        #  Step 4: Check for duplicates
        duplicate_checker = CatchDuplicateListings()
        existing_listings = list(collection.find({
            "contact.phone_numbers": {"$in": listing_dict["contact"]["phone_numbers"]}
        }))

        is_duplicate, _ = duplicate_checker.is_similar_listing(listing_dict, existing_listings)

        listing_dict["is_duplicate"] = True if is_duplicate else False

        #  Step 5: Store the listing
        result = collection.insert_one(listing_dict)
        print(json.dumps(listing_dict, indent=4, default=convert_objectid))
        print(f"\n✅ Listing stored in MongoDB with ID: {result.inserted_id}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Raw LLM response: {response}")
extractDetails()