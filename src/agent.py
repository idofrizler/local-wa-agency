"""
Scenario-aware AI agent wrapper using Ollama.
"""
import asyncio
import requests
from typing import Dict, Optional

from agent_framework.openai import OpenAIChatClient
from pydantic import BaseModel

from src.config import config, ScenarioDefinition

class ScenarioAgent:
    """Wraps an Ollama agent for a specific scenario."""
    
    def __init__(self, scenario: ScenarioDefinition):
        self.scenario = scenario
        self.agent = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the agent asynchronously."""
        if self._initialized:
            return
        
        self._check_ollama_connection()
        
        openai_compatible_url = f"{config.ollama_base_url}/v1"
        
        chat_client = OpenAIChatClient(
            model_id=config.ollama_model,
            api_key="not-needed",
            base_url=openai_compatible_url
        )
        
        # Use the dynamically created Pydantic model from scenario definition
        self.agent = chat_client.create_agent(
            name=f"{self.scenario.name.capitalize()}Analyzer",
            instructions=self.scenario.prompt,
            response_format=self.scenario.response_model
        )
        
        self._initialized = True
    
    def _check_ollama_connection(self):
        """Verify that Ollama is reachable."""
        try:
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(
                    f"Ollama responded with status {response.status_code}\n"
                    f"Make sure Ollama is running: ollama serve"
                )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Could not connect to Ollama at {config.ollama_base_url}\n"
                f"Make sure Ollama is running: ollama serve\n"
                f"Error: {str(e)}"
            )
    
    async def analyze_message(self, message: str) -> Optional[BaseModel]:
        """
        Analyze a message through the scenario's agent.
        
        Args:
            message: WhatsApp message text
        
        Returns:
            Structured analysis Pydantic model or None
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self.agent.run(message)
            return result.value
        except Exception as e:
            print(f"Error analyzing message ({self.scenario.name}): {str(e)}")
            return None

_agent_cache: Dict[str, ScenarioAgent] = {}

def get_agent_for_scenario(scenario: ScenarioDefinition) -> ScenarioAgent:
    """Return a cached scenario agent."""
    key = scenario.name
    if key not in _agent_cache:
        _agent_cache[key] = ScenarioAgent(scenario)
    return _agent_cache[key]
