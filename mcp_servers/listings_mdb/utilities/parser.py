import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class RentalTerms(BaseModel):
    rent: Optional[str] = Field(None, description="Monthly rent amount or range (e.g., '$2,500/month').")
    application_fee: Optional[str] = Field(None, description="Application fee, e.g., '$50' or 'TBD'.")
    security_deposit: Optional[str] = Field(None, description="Security deposit amount (e.g., '$3,750').")
    availability: Optional[str] = Field(None, description="Availability date (e.g., '11/1/26').")
    lease_terms: Optional[str] = Field(None, description="Lease terms text (e.g., '12 months').")

class Amenities(BaseModel):
    appliances: Optional[List[str]] = Field(default_factory=list, description="List of appliances.")
    utilities_included: Optional[List[str]] = Field(default_factory=list, description="List of included utilities.")
    other_amenities: Optional[List[str]] = Field(default_factory=list, description="List of other amenities.")

class PropertyListing(BaseModel):
    """Schema for structured property listing data parsed from unstructured text."""
    address: Optional[str] = Field(None, description="Full property address, including city and ZIP code.")
    price: Optional[int] = Field(None, description="Price in numeric form (e.g., 2500).")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms.")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms.")
    description: Optional[str] = Field(None, description="Detailed property description.")
    rental_terms: Optional[RentalTerms] = Field(None, description="Object containing rent, fee, and lease details.")
    amenities: Optional[Amenities] = Field(None, description="Object containing amenities and utilities info.")
    pet_friendly: Optional[str] = Field(None, description="'yes' or 'no' if pets are allowed.")
    listing_url: Optional[str] = Field(None, description="External listing URL, if any.")
    contact: Optional[str] = Field(None, description="Contact details (phone/email).")
    source: Optional[str] = Field(None, description="Listing source, e.g., 'tulire_realty' or 'user_created'.")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp.")

class ParserListings:
    """ 
    Parses user search queries into structured fields for property storing.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the message parser with Gemini LLM and output schema.
        
        Args:
            model_name
        """
        load_dotenv()
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Create JSON output parser with Pydantic model
        self.output_parser = JsonOutputParser(pydantic_object=PropertyListing)
        
        # Initialize OpenAI LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            openai_api_key=google_api_key
        )

        self.prompt = ChatPromptTemplate.from_template("""You are a property listing parser. Extract structured information from unstructured property listings.

    Extract these fields:
    - address: Full street address (REQUIRED)
    - price: Monthly rent in dollars (number only, REQUIRED)
    - bedrooms: Number of bedrooms (number, REQUIRED)
    - bathrooms: Number of bathrooms (number or null)
    - description: Detailed property description (REQUIRED)
    - application_fee: Fee amount or "TBD" or "none"
    - lease_terms: Lease duration (e.g., "12 months")
    - amenities: Array of amenities
    - utilities_included: Array of utilities
    - other: Array of additional info
    - pet_friendly: "yes", "no", or ""
    - listing_url: External URL or ""
    - contact: Contact information
    - security_deposit: Security deposit amount or ""

    Return ONLY valid JSON with these exact field names. Set missing optional fields to empty string "" or empty array [].
    For arrays like amenities, parse comma-separated items into array elements.
                                                       
    User message: {user_message}
    {format_instructions}""")
        
        self.chain = self.prompt | self.llm | self.output_parser

    
    def extract(self, user_message: str) -> dict:
        try:
            result=self.chain.invoke({
                "user_message":user_message,
                "format_instructions": self.output_parser.get_format_instructions()
            })
            return result
        
        except Exception as e:
            print(f"Error parsing message: {e}")
            return{
                "Parsed Text":None
            }
        
if __name__ == "__main__":
    extractor = ParserListings()
    text_messages=[
        """Hi, I have a 2 bedroom apartment for rent in Koramangala, near Forum Mall. 
        It’s semi-furnished with AC, washing machine, and covered parking. 
        Rent is around ₹32,000 per month, deposit 1.5 lakh. Available from December. 
        Contact me at 9876543210 if interested. Pets allowed"""
    ]
  
    result = extractor.extract(text_messages[0])
    print(f"Output: {result}\n")