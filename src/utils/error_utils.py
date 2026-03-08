"""
Error handling utilities for TriliumPresenter.
Provides centralized error handling patterns and decorators.
"""

import functools
import traceback
from typing import Callable, Any, Optional, Dict, Type
from enum import Enum

# Import unified logging system
try:
    from .. import logging_manager
except ImportError:
    import logging_manager


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TriliumPresenterError(Exception):
    """Base exception class for TriliumPresenter."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.context = context or {}


class ConnectionError(TriliumPresenterError):
    """Error related to API/database connections."""
    
    def __init__(self, message: str, server_url: str = None, **kwargs):
        super().__init__(message, ErrorSeverity.HIGH, **kwargs)
        if server_url:
            self.context['server_url'] = server_url


class ConfigurationError(TriliumPresenterError):
    """Error related to configuration."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, ErrorSeverity.MEDIUM, **kwargs)
        if config_key:
            self.context['config_key'] = config_key


class ExportError(TriliumPresenterError):
    """Error related to export operations."""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(message, ErrorSeverity.MEDIUM, **kwargs)
        if operation:
            self.context['operation'] = operation


class ValidationError(TriliumPresenterError):
    """Error related to data validation."""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, ErrorSeverity.LOW, **kwargs)
        if field:
            self.context['field'] = field


def log_error(error: Exception, context: str = "general", logger_name: str = "error") -> None:
    """
    Log error with proper formatting and context.
    
    Args:
        error: Exception to log
        context: Context where error occurred
        logger_name: Logger destination name
    """
    logger = logging_manager.get_logger()
    
    if isinstance(error, TriliumPresenterError):
        # Structured logging for our custom errors
        error_info = {
            'message': error.message,
            'severity': error.severity.value,
            'context': error.context,
            'type': type(error).__name__
        }
        logger.error(f"[{context}] {error.message} | Severity: {error.severity.value} | Context: {error.context}", logger_name)
    else:
        # Standard exception logging
        logger.error(f"[{context}] {str(error)}", logger_name)
        logger.debug(f"[{context}] Traceback: {traceback.format_exc()}", logger_name)


def handle_errors(context: str = "operation", 
                 default_return: Any = None,
                 reraise_errors: tuple = (),
                 log_errors: bool = True) -> Callable:
    """
    Decorator for standardized error handling.
    
    Args:
        context: Context description for logging
        default_return: Value to return on error
        reraise_errors: Tuple of exception types to reraise
        log_errors: Whether to log errors
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    log_error(e, context)
                
                # Reraise specific error types
                if isinstance(e, reraise_errors):
                    raise
                
                return default_return
        return wrapper
    return decorator


def safe_operation(operation_name: str = "operation",
                  default_return: Any = None,
                  suppress_errors: bool = True) -> Callable:
    """
    Decorator for safe operations that shouldn't crash the application.
    
    Args:
        operation_name: Name of operation for logging
        default_return: Value to return on error
        suppress_errors: Whether to suppress all errors
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(e, operation_name)
                
                if not suppress_errors:
                    raise
                    
                return default_return
        return wrapper
    return decorator


def validate_required_args(**validators: Dict[str, Callable]) -> Callable:
    """
    Decorator to validate function arguments.
    
    Args:
        validators: Dictionary mapping argument names to validator functions
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate arguments
            for arg_name, validator in validators.items():
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]
                    try:
                        if not validator(value):
                            raise ValidationError(
                                f"Validation failed for argument '{arg_name}'",
                                field=arg_name
                            )
                    except Exception as e:
                        if not isinstance(e, ValidationError):
                            raise ValidationError(
                                f"Validator error for argument '{arg_name}': {e}",
                                field=arg_name
                            )
                        raise
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class ErrorCollector:
    """Collects and manages multiple errors."""
    
    def __init__(self):
        self.errors = []
    
    def add_error(self, error: Exception, context: str = "unknown"):
        """Add an error to the collection."""
        self.errors.append({
            'error': error,
            'context': context,
            'timestamp': __import__('time').time()
        })
    
    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0
    
    def get_errors(self) -> list:
        """Get all collected errors."""
        return self.errors.copy()
    
    def get_error_summary(self) -> str:
        """Get a summary of all errors."""
        if not self.has_errors():
            return "No errors"
        
        summary_parts = []
        for error_info in self.errors:
            error = error_info['error']
            context = error_info['context']
            summary_parts.append(f"[{context}] {str(error)}")
        
        return "; ".join(summary_parts)
    
    def clear(self):
        """Clear all collected errors."""
        self.errors.clear()
    
    def log_all_errors(self, logger_name: str = "error"):
        """Log all collected errors."""
        for error_info in self.errors:
            log_error(error_info['error'], error_info['context'], logger_name)


# Common validators for use with validate_required_args decorator
def not_none(value) -> bool:
    """Validate that value is not None."""
    return value is not None

def not_empty_string(value) -> bool:
    """Validate that value is not an empty string."""
    return isinstance(value, str) and value.strip() != ""

def positive_number(value) -> bool:
    """Validate that value is a positive number."""
    return isinstance(value, (int, float)) and value > 0

def valid_file_path(value) -> bool:
    """Validate that value is a valid file path."""
    from pathlib import Path
    try:
        path = Path(value)
        return path.is_file() or path.parent.exists()
    except:
        return False