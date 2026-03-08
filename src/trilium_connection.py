"""
Trilium Connection Management for TriliumPresenter.
Handles API connections and basic operations.
"""

from typing import Optional, Dict, Any
from trilium_py.client import ETAPI

# Import unified logging system
try:
    from . import logging_manager
except ImportError:
    import logging_manager


class TriliumConnection:
    """Manages connection to Trilium API."""
    
    def __init__(self, server_url: str, token: str):
        self.server_url = server_url
        self.token = token
        self.api: Optional[ETAPI] = None
        self.logger = logging_manager.get_logger()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def connect(self):
        """Connects to the Trilium API."""
        try:
            self.api = ETAPI(self.server_url, self.token)
            # Test connection
            info = self.api.app_info()
            self.logger.info(f"Connected to Trilium {info.get('appVersion', 'unknown')} at {self.server_url}", "api")
        except Exception as e:
            raise Exception(f"Failed to connect to Trilium API: {e}")
    
    def close(self):
        """Closes the API connection."""
        if self.api:
            self.api.close()
            self.api = None
    
    def is_connected(self) -> bool:
        """Checks if a connection exists."""
        return self.api is not None
    
    def ensure_connected(self):
        """Ensures that a connection exists."""
        if not self.is_connected():
            self.connect()
    
    def get_api(self) -> ETAPI:
        """Gets the API instance, establishes connection if necessary."""
        self.ensure_connected()
        return self.api
    
    def test_connection(self) -> bool:
        """Tests the API connection."""
        try:
            self.ensure_connected()
            self.api.app_info()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}", "api")
            return False