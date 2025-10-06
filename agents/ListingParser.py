from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError
from agents.Prompts import *
from listingParser.models.ListingInfo import Listing
from LlmProviders.GoogleLangchain import llm


def getPromptTemplate(listing_text:str, parser):


    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", human_prompt_template)
    ])
    formatted_prompt = chat_prompt.format_messages(format_instructions=parser.get_format_instructions(),
                                                   input=listing_text)
    return formatted_prompt

def parseHouseListing(listing_text:str)->Listing:


    try:

        parser=PydanticOutputParser(pydantic_object=Listing)
        formatted_prompt = getPromptTemplate(listing_text, parser)
        response = llm.invoke(formatted_prompt)
        print(response.content)
        listing_instance = parser.parse(response.content)
        listing_instance.raw_listing=listing_text
        return listing_instance
    except Exception as e:
        print(f"Validation error: {e}")
        messages = [err["msg"] for err in e.errors()]
        print("Validation errors:", messages)
        return None