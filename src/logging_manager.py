#!/usr/bin/env python3
"""
Centralized Logging Manager for HTML Presentation Generator
Provides unified logging with configurable destinations and formatting.
"""

import logging
import sys
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


class LoggingManager:
    """Central logging manager with multiple output destinations."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the logging manager with configuration."""
        self.config = config or {}
        self.gui_text_widget = None
        self.gui_callback = None
        self.gui_root = None  # Store reference to root window for thread-safe messagebox
        self.enabled_destinations = set()
        self.log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        # Thread safety
        self.lock = threading.Lock()

        # Setup logging configuration
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration based on config."""
        logging_config = self.config.get('logging', {})
        
        # Set enabled destinations
        destinations = logging_config.get('destinations', ['console'])
        self.enabled_destinations = set(destinations)
        
        # Set log level
        log_level = logging_config.get('level', 'INFO')
        self.log_level = self.log_levels.get(log_level, logging.INFO)
        
        # Configure Python logging
        logging.basicConfig(
            level=self.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[]
        )
        
        # Add console handler if enabled
        if 'console' in self.enabled_destinations:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)
        
        # Add file handler if enabled
        if 'file' in self.enabled_destinations:
            file_path = Path(logging_config.get('file_path', 'tech/logs/presentation.log'))
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(self.log_level)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
    
    def set_gui_widget(self, text_widget: tk.Text):
        """Set the GUI text widget for logging output."""
        self.gui_text_widget = text_widget
        self.enabled_destinations.add('gui')

    def set_gui_callback(self, callback: Callable[[str], None]):
        """Set a callback function for GUI logging."""
        self.gui_callback = callback
        self.enabled_destinations.add('gui')

    def set_gui_root(self, root_widget):
        """Set the GUI root window for thread-safe messagebox operations."""
        self.gui_root = root_widget
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp."""
        return datetime.now().strftime("%H:%M:%S")
    
    def _format_message(self, level: str, message: str, component: str = None) -> str:
        """Format log message with timestamp and level."""
        timestamp = self._get_timestamp()
        component_part = f" [{component}]" if component else ""
        
        # Add emoji for visual appeal
        emoji_map = {
            'DEBUG': '🐛',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        emoji = emoji_map.get(level, 'ℹ️')
        return f"{timestamp} {emoji} {level}{component_part}: {message}"
    
    def _log_to_console(self, level: str, message: str, component: str = None):
        """Log to console."""
        if 'console' in self.enabled_destinations:
            formatted_msg = self._format_message(level, message, component)
            print(formatted_msg, flush=True)
    
    def _log_to_gui(self, level: str, message: str, component: str = None):
        """Log to GUI text widget."""
        if 'gui' not in self.enabled_destinations:
            return
        
        formatted_msg = self._format_message(level, message, component)
        
        # Use callback if available
        if self.gui_callback:
            try:
                self.gui_callback(formatted_msg)
            except Exception:
                pass  # Ignore GUI errors
        
        # Use text widget if available
        elif self.gui_text_widget:
            try:
                if self.gui_text_widget.winfo_exists():
                    self.gui_text_widget.insert(tk.END, formatted_msg + "\n")
                    self.gui_text_widget.see(tk.END)
                    self.gui_text_widget.update_idletasks()  # Force refresh without blocking
            except Exception:
                pass  # Ignore GUI errors
    
    def _log_to_file(self, level: str, message: str, component: str = None):
        """Log to file using Python logging."""
        if 'file' in self.enabled_destinations:
            logger = logging.getLogger(component or 'presentation')
            log_method = getattr(logger, level.lower(), logger.info)
            log_method(message)
    
    def _show_messagebox(self, level: str, message: str, title: str = None):
        """Show messagebox for important messages (thread-safe)."""
        if 'messagebox' not in self.enabled_destinations:
            return

        title = title or f"{level.capitalize()}"

        try:
            # Schedule messagebox in main thread if GUI root is available
            if self.gui_root:
                self.gui_root.after(0, self._show_messagebox_gui, level, title, message)
            else:
                # Fallback: show directly (may not be thread-safe)
                self._show_messagebox_gui(level, title, message)
        except Exception:
            pass  # Ignore GUI errors

    def _show_messagebox_gui(self, level: str, title: str, message: str):
        """Show messagebox in GUI thread (must be called from main thread)."""
        try:
            if level == 'ERROR' or level == 'CRITICAL':
                messagebox.showerror(title, message)
            elif level == 'WARNING':
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)
        except Exception:
            pass  # Ignore GUI errors
    
    def debug(self, message: str, component: str = None):
        """Log debug message."""
        self._log_to_console('DEBUG', message, component)
        self._log_to_gui('DEBUG', message, component)
        self._log_to_file('DEBUG', message, component)

    def info(self, message: str, component: str = None):
        """Log info message."""
        self._log_to_console('INFO', message, component)
        self._log_to_gui('INFO', message, component)
        self._log_to_file('INFO', message, component)

    def warning(self, message: str, component: str = None, show_messagebox: bool = False):
        """Log warning message."""
        self._log_to_console('WARNING', message, component)
        self._log_to_gui('WARNING', message, component)
        self._log_to_file('WARNING', message, component)

        if show_messagebox:
            self._show_messagebox('WARNING', message, "Warning")

    def error(self, message: str, component: str = None, show_messagebox: bool = False):
        """Log error message."""
        self._log_to_console('ERROR', message, component)
        self._log_to_gui('ERROR', message, component)
        self._log_to_file('ERROR', message, component)

        if show_messagebox:
            self._show_messagebox('ERROR', message, "Error")

    def critical(self, message: str, component: str = None, show_messagebox: bool = True):
        """Log critical message."""
        self._log_to_console('CRITICAL', message, component)
        self._log_to_gui('CRITICAL', message, component)
        self._log_to_file('CRITICAL', message, component)

        if show_messagebox:
            self._show_messagebox('CRITICAL', message, "Critical Error")
    
    def success(self, message: str, component: str = None):
        """Log success message (special info level)."""
        # Use special formatting for success messages
        success_msg = f"✅ {message}"
        self._log_to_console('INFO', success_msg, component)
        self._log_to_gui('INFO', success_msg, component)
        self._log_to_file('INFO', success_msg, component)

    def progress(self, message: str, component: str = None):
        """Log progress message."""
        progress_msg = f"⏳ {message}"
        self._log_to_console('INFO', progress_msg, component)
        self._log_to_gui('INFO', progress_msg, component)
        self._log_to_file('INFO', progress_msg, component)

    def step(self, message: str, component: str = None):
        """Log step message."""
        step_msg = f"👉 {message}"
        self._log_to_console('INFO', step_msg, component)
        self._log_to_gui('INFO', step_msg, component)
        self._log_to_file('INFO', step_msg, component)

    def section(self, message: str, component: str = None):
        """Log section header."""
        section_msg = f"\n{'='*50}\n📋 {message}\n{'='*50}"
        self._log_to_console('INFO', section_msg, component)
        self._log_to_gui('INFO', section_msg, component)
        self._log_to_file('INFO', section_msg, component)

    def command(self, command: str, component: str = None):
        """Log command execution."""
        cmd_msg = f"💻 Command: {command}"
        self._log_to_console('INFO', cmd_msg, component)
        self._log_to_gui('INFO', cmd_msg, component)
        self._log_to_file('INFO', cmd_msg, component)

    def file_operation(self, operation: str, file_path: str, component: str = None):
        """Log file operation."""
        file_msg = f"📄 {operation}: {file_path}"
        self._log_to_console('INFO', file_msg, component)
        self._log_to_gui('INFO', file_msg, component)
        self._log_to_file('INFO', file_msg, component)
    
    def enable_destination(self, destination: str):
        """Enable logging destination."""
        self.enabled_destinations.add(destination)
    
    def disable_destination(self, destination: str):
        """Disable logging destination."""
        self.enabled_destinations.discard(destination)
    
    def set_level(self, level: str):
        """Set logging level."""
        if level in self.log_levels:
            self.log_level = self.log_levels[level]
            logging.getLogger().setLevel(self.log_level)


# Global logging manager instance
_logger_instance = None


def get_logger(config: Dict[str, Any] = None) -> LoggingManager:
    """Get or create global logging manager instance."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = LoggingManager(config)
    
    return _logger_instance


def setup_logging(config: Dict[str, Any] = None) -> LoggingManager:
    """Setup global logging configuration."""
    global _logger_instance
    _logger_instance = LoggingManager(config)
    return _logger_instance


# Convenience functions for direct use
def debug(message: str, component: str = None):
    """Log debug message."""
    get_logger().debug(message, component)


def info(message: str, component: str = None):
    """Log info message."""
    get_logger().info(message, component)


def warning(message: str, component: str = None, show_messagebox: bool = False):
    """Log warning message."""
    get_logger().warning(message, component, show_messagebox)


def error(message: str, component: str = None, show_messagebox: bool = False):
    """Log error message."""
    get_logger().error(message, component, show_messagebox)


def critical(message: str, component: str = None, show_messagebox: bool = True):
    """Log critical message."""
    get_logger().critical(message, component, show_messagebox)


def success(message: str, component: str = None):
    """Log success message."""
    get_logger().success(message, component)


def progress(message: str, component: str = None):
    """Log progress message."""
    get_logger().progress(message, component)


def step(message: str, component: str = None):
    """Log step message."""
    get_logger().step(message, component)


def section(message: str, component: str = None):
    """Log section header."""
    get_logger().section(message, component)


def command(command: str, component: str = None):
    """Log command execution."""
    get_logger().command(command, component)


def file_operation(operation: str, file_path: str, component: str = None):
    """Log file operation."""
    get_logger().file_operation(operation, file_path, component)