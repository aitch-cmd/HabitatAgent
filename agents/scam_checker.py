from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from listingParser.Prompts import *
from listingParser.models.ListingInfo import Listing

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.2,
    google_api_key="AIzaSyCK33vqrJ9XZKmC6zgwEEgvld90HAfhuR8",
)


def checkIfListingIsValid(listing_text:str):
    # 🚨 Step 1: SCAM DETECTION (on raw listing_text)
    scam_chain = ChatPromptTemplate.from_messages([
        ("system", fake_scam_agent),
        ("human", "{listing}")
    ]) | llm

    scam_result_raw = scam_chain.invoke({"listing": listing_text})
    return scam_result_raw.content














