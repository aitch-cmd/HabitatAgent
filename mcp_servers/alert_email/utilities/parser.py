import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional


class PropertySearchCriteria(BaseModel):
    """Schema for structured extraction from the user message."""
    
    location: Optional[str] = Field(
        default=None,
        description="City, area, or neighborhood mentioned by the user"
    )
    price: Optional[int] = Field(
        default=None,
        description="Budget extracted as a number (e.g., 20000 from '20k')"
    )
    email: Optional[str] = Field(
        default=None,
        description="Email address extracted from the user message if present"
    )

class UserMessageParser:
    """
    Parses user input to extract location, price, and email ID.
    """

    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.3):
        load_dotenv()
        openai_api_key = os.environ.get("OPENAI_API_KEY")

        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Bind schema
        self.output_parser = JsonOutputParser(pydantic_object=PropertySearchCriteria)

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=openai_api_key
        )

        # Updated prompt with email instructions
        self.prompt = ChatPromptTemplate.from_template("""
You are an expert at extracting structured information from user messages.

Extract the following fields:
1. **location**: City, area, or neighborhood (if mentioned)
2. **price**: Maximum budget as a number (convert 20k → 20000, 1.5L → 150000)
3. **email**: Extract valid email address (example@gmail.com). If none present, return null.

User message: {user_message}

{format_instructions}

Rules:
- If a field is not mentioned, set it to null.
- For price, return only the numeric value.
- For email, extract only the email string.
- Always return valid JSON.
""")

        self.chain = self.prompt | self.llm | self.output_parser

    def extract(self, user_message: str) -> dict:
        """Extract structured fields from user message."""
        try:
            return self.chain.invoke({
                "user_message": user_message,
                "format_instructions": self.output_parser.get_format_instructions()
            })
        except Exception as e:
            print(f"Error parsing message: {e}")
            return {
                "location": None,
                "price": None,
                "email": None
            }


# Run tests
if __name__ == "__main__":
    extractor = UserMessageParser()

    test_messages = [
        "I'm looking for a 2BHK in Bangalore under 30k. Contact me at john.doe@gmail.com",
        "Find me something in Noida, budget 20k",
        "Here is my mail harshit_singh123@outlook.com",
        "Flat in Koramangala for 25k"
    ]

    print("Testing UserMessageParser:\n")
    for msg in test_messages:
        print(f"Input: {msg}")
        result = extractor.extract(msg)
        print(f"Output: {result}\n")
