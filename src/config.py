"""
Configuration management for WhatsApp Padel Match Tracker and scenario definitions.
"""
import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Type

from dotenv import load_dotenv
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from test_apps.padel import UserPreferences

# Load environment variables
load_dotenv()

@dataclass
class ScenarioDefinition:
    """Definition for a monitoring scenario."""
    name: str
    prompt: str
    response_model: Type[BaseModel]  # Now holds the actual Pydantic model class
    groups: List[str]
    confidence_field: Optional[str] = "confidence"
    reasoning_field: Optional[str] = "reasoning"

class Config:
    """Configuration loader and manager."""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.scenarios_dir = self.base_dir / "scenarios"
        self.session_dir = self.base_dir / "whatsapp_session"
        self.scenario_definitions: Dict[str, ScenarioDefinition] = {}
        self.group_to_scenario: Dict[str, ScenarioDefinition] = {}

        # Ollama configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")

        # User preferences
        self.user_preferences = UserPreferences()

        # Scanning configuration
        self.default_scroll_count = 5
        self.default_monitor_interval = 60  # seconds

        # Load scenarios to know available groups
        self._load_scenarios()

    def _load_scenarios(self):
        """Load scenario definitions from individual JSON files and create Pydantic models dynamically."""
        if not self.scenarios_dir.exists():
            return

        # Load all .json files from scenarios directory
        for scenario_file in self.scenarios_dir.glob("*.json"):
            name = scenario_file.stem  # Filename without .json extension
            
            with open(scenario_file, "r", encoding="utf-8") as f:
                details = json.load(f)
            prompt = (details.get("prompt") or "").strip()
            response_schema = details.get("response_schema")
            groups = details.get("groups") or []
            if not prompt or not response_schema or not groups:
                continue

            # Create Pydantic model dynamically from JSON schema
            model_class = self._create_pydantic_model_from_schema(
                name=f"{name.capitalize()}Analysis",
                schema=response_schema
            )

            confidence_field = details.get("confidence_field", "confidence")
            reasoning_field = details.get("reasoning_field", "reasoning")
            scenario = ScenarioDefinition(
                name=name,
                prompt=prompt,
                response_model=model_class,
                groups=groups,
                confidence_field=confidence_field,
                reasoning_field=reasoning_field,
            )
            self.scenario_definitions[name] = scenario
            for group in groups:
                self.group_to_scenario[group] = scenario

    def _create_pydantic_model_from_schema(self, name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
        """Create a Pydantic model dynamically from a JSON schema."""
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))
        
        field_definitions = {}
        for field_name, field_schema in properties.items():
            field_type = self._json_type_to_python(field_schema)
            default_value = field_schema.get("default", ...)
            description = field_schema.get("description", "")
            
            # If field is not required and has no default, use None as default
            if field_name not in required_fields and default_value == ...:
                default_value = None
                # Make the type Optional
                from typing import Union
                field_type = Union[field_type, type(None)]
            
            field_definitions[field_name] = (
                field_type,
                FieldInfo(default=default_value, description=description)
            )
        
        return create_model(name, **field_definitions)
    
    def _json_type_to_python(self, field_schema: Dict[str, Any]) -> Type:
        """Convert JSON schema type to Python type."""
        from typing import Literal
        
        json_type = field_schema.get("type")
        
        if json_type == "string":
            # Check for enum (Literal type)
            if "enum" in field_schema:
                enum_values = tuple(field_schema["enum"])
                return Literal[enum_values]
            return str
        elif json_type == "boolean":
            return bool
        elif json_type == "integer":
            return int
        elif json_type == "number":
            return float
        elif json_type == "array":
            return list
        elif json_type == "object":
            return dict
        else:
            return str  # Default fallback

    def load_groups(self) -> List[str]:
        """Return the list of WhatsApp groups defined in scenarios."""
        groups = list(self.group_to_scenario.keys())
        if not groups:
            raise ValueError(
                f"No groups defined in {self.scenarios_dir}. Please add at least one scenario JSON file with a 'groups' list."
            )
        return groups

    def get_scenario_for_group(self, group_name: str) -> Optional[ScenarioDefinition]:
        """Get the scenario definition for a given group."""
        return self.group_to_scenario.get(group_name)

    def get_all_scenarios(self) -> List[ScenarioDefinition]:
        """Return all loaded scenario definitions."""
        return list(self.scenario_definitions.values())
    
    def get_default_scenario(self) -> ScenarioDefinition:
        """Return a fallback scenario if a group is not mapped."""
        if self.scenario_definitions:
            return next(iter(self.scenario_definitions.values()))
        raise RuntimeError("No scenario definitions are available")

# Global config instance
config = Config()
