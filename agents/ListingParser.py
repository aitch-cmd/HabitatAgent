from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from agents.Prompts import *
from listingParser.models.ListingInfo import Listing

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.2,
    google_api_key="AIzaSyCK33vqrJ9XZKmC6zgwEEgvld90HAfhuR8",
)


def getPromptTemplate(listing_text:str, parser):


    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", human_prompt_template)
    ])
    formatted_prompt = chat_prompt.format_messages(format_instructions=parser.get_format_instructions(),
                                                   input=listing_text)
    return formatted_prompt

def parseHouseListing(listing_text:str)->Listing:

    parser=PydanticOutputParser(pydantic_object=Listing)
    formatted_prompt = getPromptTemplate(listing_text, parser)
    response = llm.invoke(formatted_prompt)
    print(response.content)
    listing_instance = parser.parse(response.content)
    return listing_instance
