
import os
import sys

# Add project root to the Python path to resolve module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from LlmProviders.GoogleLangchain import llm
from langchain_core.messages import BaseMessage
from Prompts import root_agent_prompt, root_agent_promptV2
from langchain.agents import tool, AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class RootAgent:
    """
    A root agent class that interacts with a language model.
    """


    def __init__(self):
        """
        Initializes the RootAgent and assigns the shared llm instance.
        """
        self.llm = llm
        # Add a placeholder for the human message and chat history
        self.templateMessageHolder= ChatPromptTemplate.from_messages([
            ("system", root_agent_promptV2),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
        ])

    def process_message(self, message: str) -> BaseMessage:
        # We pass an empty list for chat_history for now.
        response = self.llm.invoke({"input": message, "chat_history": []})
        return response

