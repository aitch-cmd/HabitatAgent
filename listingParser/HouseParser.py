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


def extractDetails():
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", human_prompt_template)
    ])


    chain = LLMChain(
        llm=llm,
        prompt=chat_prompt
    )
    response = chain.invoke({"listing": listing_text})
    try:
        extracted_data = json.loads(response['text'])
        parsed_listing=Listing(**extracted_data)
        print(parsed_listing)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Raw LLM response: {response['text']}")



extractDetails()