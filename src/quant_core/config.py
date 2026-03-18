"""Configuration management for quant trading."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file or environment variables.

    Args:
        config_path: Path to config file. Defaults to ~/.hermes/config.yaml

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = os.path.expanduser("~/.hermes/config.yaml")

    config = {}

    # Load from file if exists
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    # Override with environment variables
    env_vars = {
        "API_KEY": "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
        "DATABASE_URL": "DATABASE_URL",
        "DATA_PATH": "DATA_PATH",
    }

    for env_key, var_name in env_vars.items():
        if var_name in os.environ:
            config[env_key.lower()] = os.environ[var_name]

    return config


def get_data_path() -> Path:
    """Get the default data directory."""
    return Path(os.environ.get("DATA_PATH", "~/quant_data")).expanduser()


def get_cache_path() -> Path:
    """Get the cache directory."""
    cache_dir = Path("~/quant_cache").expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
