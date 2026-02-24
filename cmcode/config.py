"""Configuration handling for cmcode."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Config:
    """Configuration for cmcode CLI."""
    
    # API settings
    endpoint: str = "https://ae-ai-coding-agent-workshop.cognitiveservices.azure.com/openai/v1/"
    model: str = "gpt-4o"
    api_key: str | None = None
    
    # Behavior settings
    streaming: bool = True
    auto_confirm: bool = False
    verbose: int = 0
    
    # Paths
    system_prompt_path: str | None = None
    workspace_dir: str | None = None
    
    # Output settings
    output_format: str = "rich"  # "rich", "plain", "json"
    
    @classmethod
    def get_config_paths(cls) -> list[Path]:
        """Return list of config file paths to check, in priority order."""
        paths = []
        
        # Current directory
        paths.append(Path.cwd() / ".cmcode.yaml")
        paths.append(Path.cwd() / ".cmcode.yml")
        
        # Home directory
        home = Path.home()
        paths.append(home / ".cmcode.yaml")
        paths.append(home / ".cmcode.yml")
        
        # XDG config directory
        xdg_config = os.environ.get("XDG_CONFIG_HOME", home / ".config")
        paths.append(Path(xdg_config) / "cmcode" / "config.yaml")
        paths.append(Path(xdg_config) / "cmcode" / "config.yml")
        
        return paths
    
    @classmethod
    def load(cls, config_path: str | None = None) -> "Config":
        """
        Load configuration from file and environment variables.
        
        Priority (highest to lowest):
        1. Explicitly provided config_path
        2. Environment variables
        3. Config files (in order from get_config_paths)
        4. Default values
        """
        config = cls()
        
        # Load from config file
        if config_path:
            config._load_from_file(Path(config_path))
        else:
            for path in cls.get_config_paths():
                if path.exists():
                    config._load_from_file(path)
                    break
        
        # Override with environment variables
        config._load_from_env()
        
        return config
    
    def _load_from_file(self, path: Path) -> None:
        """Load configuration from a YAML file."""
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            
            if "endpoint" in data:
                self.endpoint = data["endpoint"]
            if "model" in data:
                self.model = data["model"]
            if "api_key" in data:
                self.api_key = data["api_key"]
            if "streaming" in data:
                self.streaming = data["streaming"]
            if "auto_confirm" in data:
                self.auto_confirm = data["auto_confirm"]
            if "verbose" in data:
                self.verbose = data["verbose"]
            if "system_prompt_path" in data:
                self.system_prompt_path = data["system_prompt_path"]
            if "workspace_dir" in data:
                self.workspace_dir = data["workspace_dir"]
            if "output_format" in data:
                self.output_format = data["output_format"]
                
        except Exception as e:
            # Silently ignore config file errors, use defaults
            pass
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        if os.environ.get("AZURE_OPENAI_API_KEY"):
            self.api_key = os.environ["AZURE_OPENAI_API_KEY"]
        if os.environ.get("CMCODE_ENDPOINT"):
            self.endpoint = os.environ["CMCODE_ENDPOINT"]
        if os.environ.get("CMCODE_MODEL"):
            self.model = os.environ["CMCODE_MODEL"]
        if os.environ.get("CMCODE_STREAMING"):
            self.streaming = os.environ["CMCODE_STREAMING"].lower() in ("true", "1", "yes")
        if os.environ.get("CMCODE_OUTPUT_FORMAT"):
            self.output_format = os.environ["CMCODE_OUTPUT_FORMAT"]
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.api_key:
            errors.append("API key not configured. Set AZURE_OPENAI_API_KEY environment variable or add api_key to config file.")
        
        if self.output_format not in ("rich", "plain", "json"):
            errors.append(f"Invalid output_format: {self.output_format}. Must be 'rich', 'plain', or 'json'.")
        
        return errors


def get_default_config_template() -> str:
    """Return a template for the config file."""
    return """# cmcode configuration file
# Place this file at ~/.cmcode.yaml or ./.cmcode.yaml

# API Configuration
# endpoint: https://ae-ai-coding-agent-workshop.cognitiveservices.azure.com/openai/v1/
# model: gpt-4o
# api_key: your-api-key-here  # Better to use AZURE_OPENAI_API_KEY env var

# Behavior
# streaming: true          # Stream responses as they arrive
# auto_confirm: false      # Auto-confirm file overwrites
# verbose: 0               # Verbosity level (0-2)

# Paths
# system_prompt_path: ./system-prompt.md
# workspace_dir: ./

# Output
# output_format: rich      # rich, plain, or json
"""
