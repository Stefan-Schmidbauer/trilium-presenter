"""
Error Handling Utilities for TriliumPresenter.
Provides decorators and utilities for consistent error handling across the application.
"""

import functools
import traceback
import threading
from typing import Callable, Optional, Any, Union, Type
from contextlib import contextmanager
import tkinter as tk
from tkinter import messagebox


class ErrorContext:
    """Context information for error handling."""
    
    def __init__(self, operation: str, component: str = "general", user_message: str = None):
        """
        Initialize error context.
        
        Args:
            operation: Name of the operation being performed
            component: Component where error occurred (api, gui, file, etc.)
            user_message: Custom user-friendly message
        """
        self.operation = operation
        self.component = component
        self.user_message = user_message
        self.thread_safe = threading.current_thread().name != "MainThread"


class ErrorHandler:
    """Centralized error handler with configurable behaviors."""
    
    def __init__(self, logger=None, services=None):
        """
        Initialize error handler.
        
        Args:
            logger: Logger instance for logging errors
            services: ServiceContainer for GUI callbacks
        """
        self.logger = logger
        self.services = services
    
    def handle_error(self, error: Exception, context: ErrorContext, 
                    reraise: bool = False, show_user: bool = True) -> bool:
        """
        Handle an error with consistent logging and user notification.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            reraise: Whether to reraise the exception
            show_user: Whether to show error to user
            
        Returns:
            bool: True if error was handled successfully
        """
        # Create error message
        error_msg = str(error)
        if not error_msg:
            error_msg = f"{type(error).__name__} occurred"
        
        # Log the error
        if self.logger:
            log_msg = f"{context.operation} failed: {error_msg}"
            self.logger.error(log_msg, context.component)
            
            # Log full traceback in debug mode
            if hasattr(self.logger, 'debug'):
                self.logger.debug(f"Traceback: {traceback.format_exc()}", context.component)
        else:
            print(f"ERROR [{context.component}]: {context.operation} failed: {error_msg}")
        
        # Show user-friendly message if requested
        if show_user and self.services:
            user_msg = context.user_message or f"Error in {context.operation}: {error_msg}"
            
            if context.thread_safe:
                # Schedule on main thread
                if hasattr(self.services, 'root') and self.services.root:
                    self.services.root.after(0, lambda: self._show_error_dialog(context.operation, user_msg))
            else:
                self._show_error_dialog(context.operation, user_msg)
        
        # Reraise if requested
        if reraise:
            raise error
        
        return True
    
    def _show_error_dialog(self, title: str, message: str):
        """Show error dialog to user."""
        try:
            messagebox.showerror(f"Error: {title}", message)
        except Exception as e:
            # Fallback if GUI is not available
            print(f"GUI Error Dialog failed: {e}")
            print(f"Original error: {message}")


# Global error handler instance (will be initialized by main window)
_global_error_handler: Optional[ErrorHandler] = None


def set_global_error_handler(handler: ErrorHandler):
    """Set the global error handler instance."""
    global _global_error_handler
    _global_error_handler = handler


def get_global_error_handler() -> Optional[ErrorHandler]:
    """Get the global error handler instance."""
    return _global_error_handler


# Decorator factories for different types of operations
def handle_api_errors(operation: str = None, user_message: str = None, reraise: bool = False):
    """
    Decorator for API operations.
    
    Args:
        operation: Name of the API operation
        user_message: Custom user message
        reraise: Whether to reraise exceptions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"API {func.__name__}"
            context = ErrorContext(op_name, "api", user_message)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_global_error_handler()
                if handler:
                    handler.handle_error(e, context, reraise=reraise)
                else:
                    print(f"API Error in {op_name}: {e}")
                    if reraise:
                        raise
                return None
        return wrapper
    return decorator


def handle_gui_errors(operation: str = None, user_message: str = None, silent: bool = False):
    """
    Decorator for GUI operations.
    
    Args:
        operation: Name of the GUI operation
        user_message: Custom user message
        silent: If True, don't show error dialogs to user
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"GUI {func.__name__}"
            context = ErrorContext(op_name, "gui", user_message)
            
            try:
                return func(*args, **kwargs)
            except tk.TclError:
                # Ignore Tkinter errors (widget destroyed, etc.)
                pass
            except Exception as e:
                handler = get_global_error_handler()
                if handler:
                    handler.handle_error(e, context, show_user=not silent)
                else:
                    print(f"GUI Error in {op_name}: {e}")
                return None
        return wrapper
    return decorator


def handle_file_errors(operation: str = None, user_message: str = None, reraise: bool = False):
    """
    Decorator for file operations.
    
    Args:
        operation: Name of the file operation
        user_message: Custom user message
        reraise: Whether to reraise exceptions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"File {func.__name__}"
            context = ErrorContext(op_name, "file", user_message)
            
            try:
                return func(*args, **kwargs)
            except (FileNotFoundError, PermissionError, OSError) as e:
                handler = get_global_error_handler()
                if handler:
                    handler.handle_error(e, context, reraise=reraise)
                else:
                    print(f"File Error in {op_name}: {e}")
                    if reraise:
                        raise
                return None
        return wrapper
    return decorator


def handle_config_errors(operation: str = None, default_value: Any = None):
    """
    Decorator for configuration operations.
    
    Args:
        operation: Name of the config operation
        default_value: Value to return on error
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"Config {func.__name__}"
            context = ErrorContext(op_name, "config", "Configuration error")
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_global_error_handler()
                if handler:
                    handler.handle_error(e, context, show_user=False)  # Config errors are usually not critical
                else:
                    print(f"Config Error in {op_name}: {e}")
                return default_value
        return wrapper
    return decorator


@contextmanager
def safe_operation(operation: str, component: str = "general", 
                  user_message: str = None, reraise: bool = False):
    """
    Context manager for safe operations.
    
    Args:
        operation: Name of the operation
        component: Component performing the operation
        user_message: Custom user message
        reraise: Whether to reraise exceptions
    """
    context = ErrorContext(operation, component, user_message)
    
    try:
        yield
    except Exception as e:
        handler = get_global_error_handler()
        if handler:
            handler.handle_error(e, context, reraise=reraise)
        else:
            print(f"Error in {operation}: {e}")
            if reraise:
                raise


def safe_thread_operation(func: Callable, *args, operation: str = None, 
                         component: str = "thread", **kwargs):
    """
    Execute a function safely in a background thread.
    
    Args:
        func: Function to execute
        *args: Function arguments
        operation: Name of the operation
        component: Component name
        **kwargs: Function keyword arguments
    """
    op_name = operation or f"Thread {func.__name__}"
    
    def safe_wrapper():
        context = ErrorContext(op_name, component)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handler = get_global_error_handler()
            if handler:
                handler.handle_error(e, context)
            else:
                print(f"Thread Error in {op_name}: {e}")
    
    thread = threading.Thread(target=safe_wrapper, daemon=True)
    thread.start()
    return thread