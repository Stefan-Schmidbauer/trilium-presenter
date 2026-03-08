"""
Browser Service for TriliumPresenter GUI.
Handles browser detection and management.
"""

import webbrowser
import platform
from typing import Dict, Optional


class BrowserService:
    """Service for browser detection and management."""
    
    def __init__(self):
        """Initialize browser service."""
        self.available_browsers = {}
        self.preferred_browser = 'auto'
        self._detect_browsers()
    
    def _detect_browsers(self) -> None:
        """Detect available browsers on the system."""
        # Common browser names to test
        browser_names = {
            'firefox': 'Firefox',
            'chrome': 'Google Chrome',
            'chromium': 'Chromium',
            'safari': 'Safari',
            'opera': 'Opera',
            'edge': 'Microsoft Edge'
        }
        
        # Platform-specific browser names
        system = platform.system().lower()
        if system == 'linux':
            browser_names.update({
                'chromium-browser': 'Chromium Browser',
                'google-chrome': 'Google Chrome',
                'firefox-esr': 'Firefox ESR',
                'epiphany': 'Epiphany'
            })
        elif system == 'windows':
            browser_names.update({
                'iexplore': 'Internet Explorer',
                'msedge': 'Microsoft Edge'
            })
        elif system == 'darwin':  # macOS
            browser_names.update({
                'open -a "Google Chrome"': 'Google Chrome',
                'open -a "Firefox"': 'Firefox',
                'open -a "Safari"': 'Safari'
            })
        
        self.available_browsers = {'auto': 'System Standard'}
        
        # Test each browser
        for browser_id, browser_name in browser_names.items():
            try:
                browser_obj = webbrowser.get(browser_id)
                if browser_obj:
                    self.available_browsers[browser_id] = browser_name
            except webbrowser.Error:
                pass
            except Exception:
                pass
    
    def get_available_browsers(self) -> Dict[str, str]:
        """Get dictionary of available browsers."""
        return self.available_browsers.copy()
    
    def get_browser_list(self) -> list:
        """Get list of browser display names for UI."""
        return [f"{name} ({key})" if key != 'auto' else name 
                for key, name in self.available_browsers.items()]
    
    def set_preferred_browser(self, browser_id: str) -> bool:
        """Set preferred browser."""
        if browser_id in self.available_browsers:
            self.preferred_browser = browser_id
            return True
        return False
    
    def get_preferred_browser(self) -> str:
        """Get preferred browser ID."""
        return self.preferred_browser
    
    def get_browser_object(self, browser_id: Optional[str] = None) -> webbrowser.BaseBrowser:
        """Get browser object for opening URLs."""
        if browser_id is None:
            browser_id = self.preferred_browser
        
        if browser_id == 'auto' or browser_id not in self.available_browsers:
            return webbrowser.get()
        
        try:
            return webbrowser.get(browser_id)
        except webbrowser.Error:
            return webbrowser.get()
    
    def open_url(self, url: str, browser_id: Optional[str] = None) -> bool:
        """Open URL in specified browser."""
        try:
            browser = self.get_browser_object(browser_id)
            browser.open(url)
            return True
        except Exception:
            return False
    
    def get_browser_name(self, browser_id: str) -> str:
        """Get display name for browser ID."""
        return self.available_browsers.get(browser_id, "Unknown Browser")
    
    def get_browser_id_from_display(self, display_value: str) -> str:
        """Extract browser ID from display value."""
        if "(" in display_value and ")" in display_value:
            return display_value.split("(")[-1].rstrip(")")
        return 'auto'