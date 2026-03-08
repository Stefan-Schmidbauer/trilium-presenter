"""
Logging Utilities for consistent logging across TriliumPresenter.
Provides standardized logging methods and formatters.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path


class LogLevel:
    """Standardized log levels."""
    DEBUG = "debug"
    INFO = "info" 
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComponentLogger:
    """Component-specific logger wrapper with consistent formatting."""
    
    def __init__(self, component: str, base_logger=None):
        """
        Initialize component logger.
        
        Args:
            component: Component name (api, gui, file, etc.)
            base_logger: Base logger instance
        """
        self.component = component
        self.base_logger = base_logger
        self._message_filters = []
    
    def add_message_filter(self, filter_func):
        """Add a message filter function."""
        self._message_filters.append(filter_func)
    
    def _should_filter_message(self, message: str) -> bool:
        """Check if message should be filtered out."""
        for filter_func in self._message_filters:
            if filter_func(message):
                return True
        return False
    
    def _log(self, level: str, message: str, show_user: bool = False, **kwargs):
        """Internal logging method."""
        if self._should_filter_message(message):
            return
        
        # Format message with component
        formatted_message = f"[{self.component.upper()}] {message}"
        
        # Log via base logger if available
        if self.base_logger and hasattr(self.base_logger, level):
            method = getattr(self.base_logger, level)
            method(formatted_message, self.component, **kwargs)
        else:
            # Fallback to print
            level_prefix = {
                LogLevel.DEBUG: "🐛 DEBUG",
                LogLevel.INFO: "ℹ️ INFO", 
                LogLevel.SUCCESS: "✅ SUCCESS",
                LogLevel.WARNING: "⚠️ WARNING",
                LogLevel.ERROR: "❌ ERROR",
                LogLevel.CRITICAL: "🚨 CRITICAL"
            }.get(level, "LOG")
            
            print(f"{level_prefix}: {formatted_message}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log success message."""
        self._log(LogLevel.SUCCESS, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def section(self, title: str, **kwargs):
        """Log section header."""
        separator = "=" * len(title)
        self.info(f"\n{separator}\n{title}\n{separator}", **kwargs)
    
    def operation_start(self, operation: str, **kwargs):
        """Log operation start."""
        self.info(f"🚀 Starting: {operation}", **kwargs)
    
    def operation_complete(self, operation: str, **kwargs):
        """Log operation completion."""
        self.success(f"✅ Completed: {operation}", **kwargs)
    
    def operation_failed(self, operation: str, error: str, **kwargs):
        """Log operation failure."""
        self.error(f"❌ Failed: {operation} - {error}", **kwargs)


class LoggerFactory:
    """Factory for creating component loggers."""
    
    def __init__(self, base_logger=None):
        """Initialize logger factory."""
        self.base_logger = base_logger
        self._loggers: Dict[str, ComponentLogger] = {}
        self._global_filters = []
    
    def add_global_filter(self, filter_func):
        """Add a global message filter."""
        self._global_filters.append(filter_func)
        # Apply to existing loggers
        for logger in self._loggers.values():
            logger.add_message_filter(filter_func)
    
    def get_logger(self, component: str) -> ComponentLogger:
        """Get or create component logger."""
        if component not in self._loggers:
            logger = ComponentLogger(component, self.base_logger)
            # Apply global filters
            for filter_func in self._global_filters:
                logger.add_message_filter(filter_func)
            self._loggers[component] = logger
        return self._loggers[component]
    
    def set_base_logger(self, base_logger):
        """Update base logger for all component loggers."""
        self.base_logger = base_logger
        for logger in self._loggers.values():
            logger.base_logger = base_logger


# Global logger factory instance
_logger_factory: Optional[LoggerFactory] = None


def initialize_logging(base_logger=None) -> LoggerFactory:
    """Initialize global logging system."""
    global _logger_factory
    _logger_factory = LoggerFactory(base_logger)
    
    # Add common filters
    _logger_factory.add_global_filter(lambda msg: "Browser found:" in msg)
    _logger_factory.add_global_filter(lambda msg: "DEBUG:" in msg and len(msg) > 200)
    _logger_factory.add_global_filter(lambda msg: "SQL:" in msg)
    
    return _logger_factory


def get_component_logger(component: str) -> ComponentLogger:
    """Get component logger from global factory."""
    if _logger_factory is None:
        initialize_logging()
    return _logger_factory.get_logger(component)


def set_base_logger(base_logger):
    """Set base logger for global factory."""
    if _logger_factory is None:
        initialize_logging(base_logger)
    else:
        _logger_factory.set_base_logger(base_logger)


# Standard component loggers
def get_api_logger() -> ComponentLogger:
    """Get API component logger."""
    return get_component_logger("api")


def get_gui_logger() -> ComponentLogger:
    """Get GUI component logger."""
    return get_component_logger("gui")


def get_file_logger() -> ComponentLogger:
    """Get file operations logger."""
    return get_component_logger("file")


def get_config_logger() -> ComponentLogger:
    """Get configuration logger."""
    return get_component_logger("config")


def get_server_logger() -> ComponentLogger:
    """Get server operations logger."""
    return get_component_logger("server")


def get_pdf_logger() -> ComponentLogger:
    """Get PDF operations logger."""
    return get_component_logger("pdf")