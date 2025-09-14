import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from database.mongodb_client import MongoDBClient

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.2,
    google_api_key="AIzaSyCK33vqrJ9XZKmC6zgwEEgvld90HAfhuR8",
)

def convert_objectid(o):
    """Helper to safely serialize ObjectId or other non-JSON types."""
    return str(o)

def get_listings_with_normalized_fallback(user_budget, user_city):
    mongo_client = MongoDBClient()
    collection = mongo_client.database["listings"]

    max_budget = float(user_budget)  # ensure numeric
    city = user_city.strip().lower()

    # Step 1: Strict match (case-insensitive city + budget)
    query_strict = {
        "rent.price": {"$lte": max_budget},
        "location.city": {"$regex": f"^{city}$", "$options": "i"}
    }
    listings = list(collection.find(query_strict))
    if listings:
        return listings, f"Here are listings in {user_city} within your budget."

    # Step 2: Relax city (budget only)
    query_budget_only = {
        "rent.price": {"$lte": max_budget}
    }
    listings = list(collection.find(query_budget_only))
    if listings:
        return listings, f"We didn’t find matches in {user_city}, but here are some nearby within your budget."

    # Step 3: Ask user about widening budget
    widened_min = max_budget * 0.9
    widened_max = max_budget * 1.1
    return None, (
        f"No listings found under your budget. "
        f"Would you like me to expand the budget range to ${widened_min:.0f} - ${widened_max:.0f}?"
    )

def format_listings_with_llm(listings):
    if not listings:
        return "No matching listings found."

    llm_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes property listings."),
        ("human", """Here are some property listings in JSON format:

{listings}

Please:
1. Summarize them in natural language.
2. If any field has null/missing values, mention at the end:
   'The following details were not provided by the owner: ...'""")
    ])
    
    chain = llm_prompt | llm
    response = chain.invoke({"listings": json.dumps(listings, default=convert_objectid)})
    return response.content.strip()
