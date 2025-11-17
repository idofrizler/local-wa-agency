"""
AI Agent wrapper for padel game analysis.
Uses Microsoft Agent Framework with Ollama.
"""
import asyncio
import requests
from typing import Optional
from agent_framework.openai import OpenAIChatClient
from src.models import PadelGameAnalysis
from src.config import config

class PadelAgent:
    """Wrapper for the padel game analyzer agent."""
    
    def __init__(self):
        self.agent = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the agent asynchronously."""
        if self._initialized:
            return
        
        # Check if Ollama is running
        self._check_ollama_connection()
        
        # Create chat client pointing to Ollama's OpenAI-compatible endpoint
        openai_compatible_url = f"{config.ollama_base_url}/v1"
        
        chat_client = OpenAIChatClient(
            model_id=config.ollama_model,
            api_key="not-needed",  # Ollama doesn't require API key
            base_url=openai_compatible_url
        )
        
        # Create the agent with structured output
        self.agent = chat_client.create_agent(
            name="PadelAnalyzer",
            instructions=config.get_agent_instructions(),
            response_format=PadelGameAnalysis
        )
        
        self._initialized = True
    
    def _check_ollama_connection(self):
        """Check if Ollama is running and accessible."""
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
    
    async def analyze_message(self, message: str) -> Optional[PadelGameAnalysis]:
        """
        Analyze a message to determine if it's a matching padel game invite.
        
        Args:
            message: The WhatsApp message text to analyze
            
        Returns:
            PadelGameAnalysis object or None if analysis fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self.agent.run(message)
            return result.value
        except Exception as e:
            print(f"Error analyzing message: {str(e)}")
            return None
    
    def analyze_message_sync(self, message: str) -> Optional[PadelGameAnalysis]:
        """
        Synchronous wrapper for analyze_message.
        Creates a new event loop if needed.
        
        Args:
            message: The WhatsApp message text to analyze
            
        Returns:
            PadelGameAnalysis object or None if analysis fails
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to create a new one in a thread
                # For now, raise an error - caller should use async version
                raise RuntimeError(
                    "Cannot call analyze_message_sync from an async context. "
                    "Use analyze_message instead."
                )
            else:
                return loop.run_until_complete(self.analyze_message(message))
        except RuntimeError:
            # No event loop exists, create a new one
            return asyncio.run(self.analyze_message(message))

# Global agent instance
_agent = None

def get_agent() -> PadelAgent:
    """Get or create the global agent instance."""
    global _agent
    if _agent is None:
        _agent = PadelAgent()
    return _agent
