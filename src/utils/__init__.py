"""
Utilities package for TriliumPresenter.
Contains common utility functions extracted from various modules.
"""

from .text_processing import html_to_markdown, process_title_with_prefix
from .file_utils import make_safe_filename, make_safe_dirname
from .config_utils import (
    load_config, save_config, merge_config, 
    get_config_value, set_config_value, 
    validate_config_schema, ConfigManager
)
from .error_utils import (
    TriliumPresenterError, ConnectionError, ConfigurationError, 
    ExportError, ValidationError, ErrorSeverity,
    log_error, handle_errors, safe_operation, 
    validate_required_args, ErrorCollector,
    not_none, not_empty_string, positive_number, valid_file_path
)
from .imports import import_module, get_standard_imports

__all__ = [
    # Text processing
    'html_to_markdown',
    'process_title_with_prefix', 
    # File utils
    'make_safe_filename',
    'make_safe_dirname',
    # Config utils
    'load_config',
    'save_config', 
    'merge_config',
    'get_config_value',
    'set_config_value',
    'validate_config_schema',
    'ConfigManager',
    # Error utils
    'TriliumPresenterError', 
    'ConnectionError', 
    'ConfigurationError', 
    'ExportError', 
    'ValidationError', 
    'ErrorSeverity',
    'log_error', 
    'handle_errors', 
    'safe_operation', 
    'validate_required_args', 
    'ErrorCollector',
    'not_none', 
    'not_empty_string', 
    'positive_number', 
    'valid_file_path',
    # Import utils
    'import_module',
    'get_standard_imports'
]