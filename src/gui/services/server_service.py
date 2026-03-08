"""
Server Service for TriliumPresenter GUI.
Handles HTTP server management.
"""

import http.server
import socketserver
import socket
import threading
import time
import os
from pathlib import Path
from typing import Optional, Callable


class ServerService:
    """Service for HTTP server management."""
    
    def __init__(self, output_dir: str = "created"):
        """Initialize server service."""
        self.output_dir = Path(output_dir)
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.current_port = 8800  # Starting port for presentations (less commonly used than 8080)
        self.status_callback = None
    
    def set_status_callback(self, callback: Callable[[bool, int], None]) -> None:
        """Set callback for status updates."""
        self.status_callback = callback
    
    def _notify_status_change(self) -> None:
        """Notify listeners of status change."""
        if self.status_callback:
            self.status_callback(self.is_running, self.current_port)
    
    def find_free_port(self, start_port: int = 8800) -> Optional[int]:
        """Find a free port starting from start_port.

        Searches up to 100 ports to find an available one.
        """
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return None
    
    def set_port(self, port: int) -> bool:
        """Set server port (only when stopped)."""
        if self.is_running:
            return False
        
        if 1024 <= port <= 65535:
            self.current_port = port
            return True
        return False
    
    def get_port(self) -> int:
        """Get current server port."""
        return self.current_port
    
    def get_url(self) -> str:
        """Get server URL."""
        return f"http://127.0.0.1:{self.current_port}"
    
    def is_output_dir_available(self) -> bool:
        """Check if output directory exists."""
        return self.output_dir.exists()
    
    def start_server(self) -> bool:
        """Start the HTTP server."""
        if self.is_running:
            return True
        
        # Check if output directory exists
        if not self.is_output_dir_available():
            return False
        
        # Find free port
        free_port = self.find_free_port(self.current_port)
        if free_port is None:
            return False
        
        self.current_port = free_port
        
        try:
            # Start server in thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            # Wait a moment for server to start
            time.sleep(0.5)
            
            return self.is_running
            
        except Exception:
            return False
    
    def _run_server(self) -> None:
        """Run the HTTP server (in separate thread)."""
        try:
            # Change to output directory
            original_cwd = os.getcwd()
            os.chdir(str(self.output_dir.absolute()))
            
            # Create server with SO_REUSEADDR to allow immediate port reuse
            handler = http.server.SimpleHTTPRequestHandler

            # Create a custom TCPServer class with allow_reuse_address
            class ReusableTCPServer(socketserver.TCPServer):
                allow_reuse_address = True

            self.server = ReusableTCPServer(("127.0.0.1", self.current_port), handler)
            self.is_running = True
            
            # Notify status change
            self._notify_status_change()
            
            # Serve forever
            self.server.serve_forever()
            
        except Exception:
            self.is_running = False
            self._notify_status_change()
        finally:
            try:
                os.chdir(original_cwd)
            except:
                pass
    
    def stop_server(self) -> bool:
        """Stop the HTTP server."""
        if not self.is_running:
            return True
        
        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
                self.server = None
            
            self.is_running = False
            self._notify_status_change()
            return True
            
        except Exception:
            return False
    
    def get_status(self) -> dict:
        """Get server status information."""
        return {
            'is_running': self.is_running,
            'port': self.current_port,
            'url': self.get_url() if self.is_running else "",
            'output_dir_exists': self.is_output_dir_available()
        }
    
    def is_presenter_available(self) -> bool:
        """Check if presenter mode is available."""
        return (Path(".") / "simple_presenter.html").exists()
    
    def get_presenter_url(self) -> str:
        """Get presenter mode URL."""
        return f"{self.get_url()}/simple_presenter.html"