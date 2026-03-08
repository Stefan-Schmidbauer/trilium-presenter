"""
Configuration utilities for TriliumPresenter.
Handles centralized configuration loading, merging, and validation.
"""

import yaml
import copy
from pathlib import Path
from typing import Dict, Any, Optional, Union
import os
from dotenv import load_dotenv

# Import unified logging system
try:
    from .. import logging_manager
except ImportError:
    import logging_manager


def load_config(config_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from YAML file with error handling.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Configuration dictionary (empty if load fails)
    """
    config_path = Path(config_file)
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger = logging_manager.get_logger()
        logger.warning(f"Failed to load config file {config_file}: {e}", "config")
        return {}


def save_config(config: Dict[str, Any], config_file: Union[str, Path]) -> bool:
    """
    Save configuration to YAML file with error handling.
    
    Args:
        config: Configuration dictionary
        config_file: Path to configuration file
        
    Returns:
        True if successful, False otherwise
    """
    config_path = Path(config_file)
    
    try:
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        logger = logging_manager.get_logger()
        logger.error(f"Failed to save config file {config_file}: {e}", "config")
        return False


def merge_config(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two configuration dictionaries.
    Override config values take precedence over base config values.
    
    Args:
        base_config: Base configuration dictionary
        override_config: Override configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    result = copy.deepcopy(base_config)
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    
    return result


def get_config_value(config: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Get nested configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        path: Dot-separated path to value (e.g., "trilium.server_url")
        default: Default value if path not found
        
    Returns:
        Configuration value or default
    """
    keys = path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def set_config_value(config: Dict[str, Any], path: str, value: Any) -> None:
    """
    Set nested configuration value using dot notation.
    
    Args:
        config: Configuration dictionary (modified in-place)
        path: Dot-separated path to value (e.g., "trilium.server_url")
        value: Value to set
    """
    keys = path.split('.')
    current = config
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def validate_config_schema(config: Dict[str, Any], required_keys: Dict[str, type]) -> Dict[str, str]:
    """
    Validate configuration against schema.
    
    Args:
        config: Configuration dictionary to validate
        required_keys: Dictionary of required keys and their expected types
        
    Returns:
        Dictionary of validation errors (empty if valid)
    """
    errors = {}
    
    for key, expected_type in required_keys.items():
        try:
            value = get_config_value(config, key)
            if value is None:
                errors[key] = f"Required key '{key}' is missing"
            elif not isinstance(value, expected_type):
                errors[key] = f"Key '{key}' should be of type {expected_type.__name__}, got {type(value).__name__}"
        except Exception as e:
            errors[key] = f"Error validating key '{key}': {e}"
    
    return errors


def load_default_config() -> Dict[str, Any]:
    """
    Load default configuration values.

    Note: Trilium credentials (server_url, token) will be loaded from .env file.
    These are just placeholder values that will be overridden.

    Returns:
        Default configuration dictionary
    """
    return {
        'trilium': {
            'server_url': '',  # Will be loaded from .env
            'token': '',       # Will be loaded from .env
        },
        'browser': {
            'preferred': 'auto',
            'fallback': 'auto'
        },
        'navigation': {
            'show_keyboard_hints': False,
            'show_nav_buttons': False,
            'show_presenter_link': False,
            'show_slide_counter': False
        },
        'logging': {
            'level': 'INFO',
            'destinations': ['console']
        }
    }


class ConfigManager:
    """
    Centralized configuration manager for TriliumPresenter.
    """
    
    def __init__(self, config_file: Union[str, Path] = "config/presentation.yaml"):
        self.config_file = Path(config_file)
        self.config = load_default_config()
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from files and environment variables.

        Priority:
        1. Default values (hardcoded)
        2. User configuration from presentation.yaml (application settings only)
        3. Environment variables from .env (Trilium credentials: server URL and token)

        Note: Trilium credentials (server_url, token) are ONLY loaded from .env file,
              never from presentation.yaml for security reasons.
        """
        # 1. Load default configuration
        self.config = load_default_config()

        # 2. Load user configuration from presentation.yaml
        user_config = load_config(self.config_file)

        # IMPORTANT: Remove trilium credentials from YAML config if present
        # Credentials should ONLY come from .env file
        if 'trilium' in user_config:
            # Remove server_url if present in YAML (should be in .env only)
            if 'server_url' in user_config['trilium']:
                del user_config['trilium']['server_url']
            # Remove any form of token (should be in .env only)
            if 'token' in user_config['trilium']:
                del user_config['trilium']['token']
            if 'etapi_token' in user_config['trilium']:
                del user_config['trilium']['etapi_token']

        self.config = merge_config(self.config, user_config)

        # 3. Load .env file
        load_dotenv()

        # 4. Override Trilium credentials with environment variables
        # This is the ONLY source for Trilium server URL and token
        server_url_env = os.getenv('TRILIUM_SERVER_URL')
        token_env = os.getenv('TRILIUM_ETAPI_TOKEN')

        if server_url_env:
            self.set('trilium.server_url', server_url_env)
        if token_env:
            self.set('trilium.token', token_env)

        return self.config
    
    def save(self) -> bool:
        """Save configuration to file."""
        return save_config(self.config, self.config_file)
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        return get_config_value(self.config, path, default)
    
    def set(self, path: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        set_config_value(self.config, path, value)
    
    def validate(self) -> Dict[str, str]:
        """Validate configuration against expected schema."""
        required_keys = {
            'trilium.server_url': str,
            'port': int,
            'browser.preferred': str
        }
        return validate_config_schema(self.config, required_keys)
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = load_default_config()
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration dictionary."""
        return copy.deepcopy(self.config)

    def reload(self) -> Dict[str, Any]:
        """Reload configuration from file and environment variables."""
        from dotenv import load_dotenv
        load_dotenv(override=True)  # Reload .env with override
        return self.load()

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.get(section, {})

    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """Update entire configuration section."""
        current = self.get_section(section)
        current.update(values)
        self.set(section, current)

    # GUI-specific convenience methods

    def get_trilium_config(self) -> Dict[str, Any]:
        """Get Trilium API configuration."""
        return self.get_section('trilium')

    def get_navigation_config(self) -> Dict[str, Any]:
        """Get navigation configuration."""
        return self.get_section('navigation')

    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration."""
        return self.get_section('browser')

