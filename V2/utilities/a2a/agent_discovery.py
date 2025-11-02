import os
import json
from a2a.types import (AgentCard)
import httpx
from a2a.client import A2ACardResolver, A2AClient

class AgentDiscovery:
    """
    Discovers A2A agent by reading a registry file of URLs and
    querying each one's /.well-known/agent.json endpoint to retrieve an AgentCard.

    Attributes:
        registry_file (str): Path to the registry file containing agent URLs.
        base_urls (List[str]): List of base URLs read from the registry file.
    """

    def __init__(self, registry_file: str = None):
        """ 
        Initilaizes the AgentDiscovery.

        Args:
            registry_file(str): Path to the agent registry file.
            Defaults to 'utilities/a2a/agent_registry.json'.
        """
        if registry_file:
            self.registry_file = registry_file
        else:
            self.registry_file = os.path.join(os.path.dirname(__file__), 
                                              'agent_registry.json')

        self.base_urls = self._load_registry()

    def _load_registry(self) -> list[str]:
        """
        Loads and parse the registry JSON file into a list of URLs.

        Returns:
            list[str]: List of base URLs for A2A agents.
        """
        try:
            with open(self.registry_file, 'r') as f:
                data=json.load(f)
            if not isinstance(data,list):
                return ValueError("Registry file must contain a list of URLs")
            return data
        except FileNotFoundError:
            print(f"Registry file {self.registry_file} not found.")
            return []
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error decoding JSON from registry file {self.registry_file}.")
            return []
        

    async def list_agents_cards(self)->list[AgentCard]:
        """
        Asynchronously fetches the AegntCard frp, eacj base URL in the registry.
        
        Returns:
            list[AgentCard]: List of AgentCard retrieved from the Agents.
        """
        cards: list[AgentCard] = []

        async with httpx.AsyncClient(timeout=300.0) as httpx_client:
            for base_url in self.base_urls:
                resolver=A2ACardResolver(
                    base_url=base_url.rstrip('/'),
                    httpx_client=httpx_client
                )

                card=await resolver.get_agent_card()
                cards.append(card)
        return cards

        
