import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from LlmProviders.GoogleLangchain import llm


# Load .env variables
load_dotenv()

parser = JsonOutputParser()

# Prompt for extracting structured data from unstructured WhatsApp listings
extract_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant that extracts structured room rental info from unstructured WhatsApp messages. "
        "Return ONLY a JSON object with fields: location, price, type, features (list). "
        "If data is missing, set the value to null or an empty list."
    ),
    ("human", "{listing_text}"),
])
extract_chain = extract_prompt | llm | parser

#### ***** MAIN CHANGE: LLM-POWERED SMART SEARCH PROMPT *****
search_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert assistant matching room seekers to listings. "
        "Ignore misspellings and synonyms. Match features and room type by intent, not by exact spelling. "
        "Your output is ONLY a JSON list of the matched listings (copy from input)."
    ),
    ("human",
     """
Requirements:
- Budget: {budget}
- Room type: {room_type}
- Must-have features: {features}
- Location: {location}

Below are available room listings in JSON. For each listing, include it in your output JSON list if it matches ALL requirements—EVEN IF there are typos, synonyms, or slightly different phrases. 
Your output must be a JSON list of matched listing objects only, no explanation.

Listings: 
{room_listings}
""")
])
search_chain = search_prompt | llm | parser

# Store structured listings
room_listings = []

# Load unstructured WhatsApp listings from file
def load_listings_from_file(filename):
    print(f"Loading listings from file...")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.read().strip().split("\n\n")  # Each listing separated by double newline
            for text in lines:
                structured = extract_chain.invoke({"listing_text": text.strip()})
                room_listings.append(structured)
            print(f"[✓] Loaded {len(room_listings)} listings into memory.")
    except Exception as e:
        print(f"[!] Error loading listings: {e}")

# Add new listing manually (simulate WhatsApp message)
def add_new_listing():
    print("\nPaste the new room listing (from WhatsApp):")
    user_input = input("> ")
    try:
        structured = extract_chain.invoke({"listing_text": user_input.strip()})
        room_listings.append(structured)
        print("[✓] Listing added successfully!\n")
    except Exception as e:
        print(f"[!] Could not parse listing: {e}\n")

# LLM-powered fuzzy search for rooms
def search_rooms():
    print("\nLet's find you a room!")
    try:
        budget = int(input("What's your budget? (e.g., 850): "))
        room_type = input("Room type (private/shared/entire apt): ").strip().lower()
        features = input("Any must-have features? (comma separated): ").strip()
        features = [f.strip() for f in features.lower().split(",") if f.strip()]
        location = input("Preferred part of Jersey City or just 'anywhere'? ").strip().lower()

        # Here we send the requirements and all listings to the LLM for smart matching!
        results = search_chain.invoke({
            "budget": budget,
            "room_type": room_type,
            "features": features,
            "location": location,
            "room_listings": room_listings,
        })

        # Display results
        if not results or len(results) == 0:
            print("\nNo matching listings found at this time.\n")
        else:
            print(f"\nFound {len(results)} matching rooms:")
            for i, m in enumerate(results, 1):
                print(f"\n[{i}]")
                print(f"Location: {m['location']}")
                print(f"Price: ${m['price']}")
                print(f"Type: {m['type']}")
                print(f"Features: {', '.join(m['features']) if m['features'] else 'N/A'}")
            print()
    except Exception as e:
        print(f"[!] Error during search: {e}\n")

# === MAIN INTERFACE ===
if __name__ == "__main__":
    print("=== WhatsApp Room Bot (LangChain + Gemini 2.5 Pro) ===")
    load_listings_from_file("sample_listings.txt")

    while True:
        print("\nWhat would you like to do?")
        print("[1] Add new room listing (simulate WhatsApp message)")
        print("[2] Find a room (user search)")
        print("[3] Exit")
        choice = input("> ")

        if choice == "1":
            add_new_listing()
        elif choice == "2":
            search_rooms()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid option.\n")
