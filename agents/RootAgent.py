
import os
import sys

# Add project root to the Python path to resolve module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from LlmProviders.GoogleLangchain import llm
from langchain_core.messages import BaseMessage


class RootAgent:
    """
    A root agent class that interacts with a language model.
    """
    def __init__(self):
        """
        Initializes the RootAgent and assigns the shared llm instance.
        """
        self.llm = llm

    def process_message(self, message: str) -> BaseMessage:
        """
        Processes a given message using the configured language model.
        :param message: The input string to send to the language model.
        :return: The response object from the language model.
        """
        response = self.llm.invoke(message)
        return response
