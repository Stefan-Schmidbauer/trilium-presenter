"""
GUI utilities for TriliumPresenter.
Common utility functions used across GUI components.
"""

import tkinter as tk
import webbrowser
import subprocess
import shutil
from pathlib import Path
from gui.widgets.modern_messagebox import ModernMessageBox


def detect_browsers():
    """
    Detect available browsers on the system.
    
    Returns:
        dict: Dictionary mapping browser names to their availability
    """
    browsers = {
        "auto": True,  # Always available
        "firefox": False,
        "chrome": False,
        "chromium": False,
        "edge": False,
        "safari": False,
        "opera": False
    }
    
    # Check for browser executables
    browser_commands = {
        "firefox": ["firefox", "firefox-esr"],
        "chrome": ["google-chrome", "google-chrome-stable", "chrome"],
        "chromium": ["chromium", "chromium-browser"],
        "edge": ["microsoft-edge", "edge"],
        "safari": ["safari"],
        "opera": ["opera"]
    }
    
    for browser, commands in browser_commands.items():
        for cmd in commands:
            if shutil.which(cmd):
                browsers[browser] = True
                break
    
    return browsers


def open_in_browser(url: str, browser_preference: str = "auto"):
    """
    Open URL in specified browser.
    
    Args:
        url: URL to open
        browser_preference: Preferred browser ("auto", "firefox", "chrome", etc.)
    """
    try:
        if browser_preference == "auto":
            webbrowser.open(url)
        else:
            # Try to open with specific browser
            browser_map = {
                "firefox": "firefox",
                "chrome": "google-chrome",
                "chromium": "chromium",
                "edge": "microsoft-edge",
                "safari": "safari",
                "opera": "opera"
            }
            
            browser_cmd = browser_map.get(browser_preference)
            if browser_cmd and shutil.which(browser_cmd):
                subprocess.Popen([browser_cmd, url])
            else:
                # Fallback to default browser
                webbrowser.open(url)
                
    except Exception as e:
        ModernMessageBox.showerror("Browser Error", f"Could not open browser: {e}")


def show_error_dialog(title: str, message: str, details: str = None):
    """
    Show error dialog with optional details.

    Args:
        title: Dialog title
        message: Main error message
        details: Optional detailed error information
    """
    if details:
        full_message = f"{message}\n\nDetails:\n{details}"
    else:
        full_message = message

    ModernMessageBox.showerror(title, full_message)


def show_info_dialog(title: str, message: str):
    """
    Show information dialog.

    Args:
        title: Dialog title
        message: Information message
    """
    ModernMessageBox.showinfo(title, message)


def show_warning_dialog(title: str, message: str):
    """
    Show warning dialog.

    Args:
        title: Dialog title
        message: Warning message
    """
    ModernMessageBox.showwarning(title, message)


def ask_yes_no(title: str, message: str) -> bool:
    """
    Show yes/no question dialog.

    Args:
        title: Dialog title
        message: Question message

    Returns:
        bool: True if yes, False if no
    """
    return ModernMessageBox.askyesno(title, message)


def validate_path(path_str: str, must_exist: bool = True) -> bool:
    """
    Validate a file/directory path.
    
    Args:
        path_str: Path string to validate
        must_exist: Whether the path must exist
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not path_str or not path_str.strip():
        return False
        
    try:
        path = Path(path_str)
        if must_exist:
            return path.exists()
        else:
            # Check if parent directory exists
            return path.parent.exists()
    except Exception:
        return False




def find_free_port(start_port: int = 8080, max_attempts: int = 100) -> int:
    """
    Find a free port starting from start_port.
    
    Args:
        start_port: Starting port number
        max_attempts: Maximum number of ports to try
        
    Returns:
        int: Free port number, or -1 if none found
    """
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    
    return -1  # No free port found