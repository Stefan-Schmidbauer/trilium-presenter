"""
Service Container for dependency injection in TriliumPresenter GUI.
Centralizes service management and reduces coupling between components.
"""

import tkinter as tk
from typing import Optional, Any, Dict, Callable
from pathlib import Path

from .services import BrowserService, ServerService
from .error_handling import ErrorHandler, set_global_error_handler
from .logging_utils import initialize_logging, set_base_logger

# Import ConfigManager from utils
try:
    from utils.config_utils import ConfigManager
except ImportError:
    from src.utils.config_utils import ConfigManager

# Import API repository classes
try:
    # Import base classes first
    from api.repository import TriliumRepository, MockTriliumRepository
    _repository_available = True
    # Try importing the concrete implementation separately
    try:
        from api.trilium_api_repository import TriliumAPIRepository
    except ImportError:
        TriliumAPIRepository = None
except ImportError as e:
    print(f"Repository import failed: {e}")
    _repository_available = False
    TriliumRepository = None
    MockTriliumRepository = None
    TriliumAPIRepository = None


class ServiceContainer:
    """Container for managing services and their dependencies."""
    
    def __init__(self, root=None):
        """Initialize the service container."""
        # Store root for GUI operations
        self.root = root
        
        # Core services
        self.config_service = ConfigManager()
        self.browser_service = BrowserService()
        self.server_service = ServerService()
        
        # API-related services (initialized lazily)
        self._trilium_repository: Optional[TriliumRepository] = None
        
        # Error handling and logging
        self.logger_factory = initialize_logging()
        self.error_handler = None  # Will be set when logger is available
        
        # GUI-related variables and callbacks
        self.gui_callbacks: Dict[str, Callable] = {}
        
        # Trilium API variables
        self.trilium_server_var = tk.StringVar()
        self.trilium_token_var = tk.StringVar()
        
        # Workflow variables
        self.available_prefixes = {}
        self.selected_prefix = tk.StringVar()
        self.available_nodes = {}
        self.selected_node_id = tk.StringVar()
        self.available_categories = {}
        self.selected_category = tk.StringVar()
        
        # Directory sharing variables for tab workflow
        self.last_export_dir = tk.StringVar()  # Directory created by export
        self.last_creation_output_dir = tk.StringVar()  # Directory created by creation
        
        # Directory update callbacks
        self.directory_update_callbacks: Dict[str, list] = {
            'export_completed': [],  # Called when export creates a directory
            'creation_completed': []  # Called when creation creates output
        }
        
        # Configuration
        self.config_file = Path("config/presentation.yaml")
        
        # Initialize from configuration
        self._load_initial_config()
    
    def _load_initial_config(self):
        """Load initial configuration from config service."""
        # Load Trilium configuration
        trilium_config = self.config_service.get_trilium_config()
        self.trilium_server_var.set(trilium_config.get('server_url', ''))
        self.trilium_token_var.set(trilium_config.get('token', ''))
        
        # Configure browser service
        browser_config = self.config_service.get_browser_config()
        if browser_config:
            preferred = browser_config.get('preferred', 'auto')
            self.browser_service.set_preferred_browser(preferred)

        # Note: Server port is NOT configured from config anymore.
        # The server always starts with default port 8800 and auto-detects a free port.
        # This ensures the presentation server always works, regardless of saved config.
    
    @property
    def trilium_repository(self) -> Optional[TriliumRepository]:
        """Get the Trilium repository, creating it lazily if needed."""
        if self._trilium_repository is None:
            server_url = self.trilium_server_var.get().strip()
            token = self.trilium_token_var.get().strip()
            
            if _repository_available and TriliumAPIRepository and server_url and token:
                try:
                    self._trilium_repository = TriliumAPIRepository(server_url, token)
                except (ImportError, Exception) as e:
                    import traceback
                    traceback.print_exc()
                    # Fallback to mock repository for development
                    self._trilium_repository = MockTriliumRepository()
            elif _repository_available and MockTriliumRepository:
                # Use mock repository when no credentials available or TriliumAPIRepository failed
                self._trilium_repository = MockTriliumRepository()
            else:
                # Repository classes not available
                self._trilium_repository = None
        
        return self._trilium_repository
    
    @trilium_repository.setter
    def trilium_repository(self, value: TriliumRepository):
        """Set the Trilium repository."""
        self._trilium_repository = value
    
    
    def register_gui_callback(self, name: str, callback: Callable):
        """Register a GUI callback function."""
        self.gui_callbacks[name] = callback
    
    def get_gui_callback(self, name: str) -> Optional[Callable]:
        """Get a registered GUI callback function."""
        return self.gui_callbacks.get(name)
    
    def register_directory_callback(self, event_type: str, callback: Callable):
        """Register a callback for directory update events.
        
        Args:
            event_type: Either 'export_completed' or 'creation_completed'
            callback: Function to call when event occurs, takes directory path as argument
        """
        if event_type in self.directory_update_callbacks:
            self.directory_update_callbacks[event_type].append(callback)
    
    def notify_directory_event(self, event_type: str, directory_path: str):
        """Notify all registered callbacks about a directory event (thread-safe).

        Args:
            event_type: Either 'export_completed' or 'creation_completed'
            directory_path: Path to the directory that was created/updated
        """
        if event_type in self.directory_update_callbacks:
            # Schedule variable update and callbacks on GUI thread
            if self.root:
                self.root.after(0, self._notify_directory_event_gui, event_type, directory_path)
            else:
                # Fallback if no root available
                self._notify_directory_event_gui(event_type, directory_path)

    def _notify_directory_event_gui(self, event_type: str, directory_path: str):
        """Execute directory event notification in GUI thread.

        Args:
            event_type: Either 'export_completed' or 'creation_completed'
            directory_path: Path to the directory that was created/updated
        """
        if event_type not in self.directory_update_callbacks:
            return

        # Update shared variable (now thread-safe)
        if event_type == 'export_completed':
            self.last_export_dir.set(directory_path)
        elif event_type == 'creation_completed':
            self.last_creation_output_dir.set(directory_path)

        # Call all registered callbacks
        for callback in self.directory_update_callbacks[event_type]:
            try:
                callback(directory_path)
            except Exception as e:
                    print(f"Directory callback scheduling error: {e}")
                    # Continue with other callbacks even if one fails
    
    def setup_error_handling(self, logger):
        """Setup error handling system with logger."""
        # Update logger factory
        set_base_logger(logger)
        self.logger_factory.set_base_logger(logger)
        
        # Create and setup global error handler
        self.error_handler = ErrorHandler(logger, self)
        set_global_error_handler(self.error_handler)
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            # Save Trilium config
            self.config_service.set('trilium.server_url', self.trilium_server_var.get())
            self.config_service.set('trilium.token', self.trilium_token_var.get())
            
            # Save browser config
            browser_config = {
                'preferred': self.browser_service.get_preferred_browser()
            }
            self.config_service.set('browser', browser_config)

            # Note: Server port is NOT saved anymore.
            # The port is auto-detected on each startup and is irrelevant to the user.

            # Write to file
            self.config_service.save()
            
        except Exception as e:
            # Use callback if available, otherwise print
            error_callback = self.get_gui_callback('log_error')
            if error_callback:
                error_callback(f"Failed to save config: {e}")
            else:
                pass
    
    def cleanup(self):
        """Cleanup resources when shutting down."""
        # Stop server if running
        if self.server_service.is_running:
            self.server_service.stop_server()
        
        # Close repository connection
        if self._trilium_repository:
            try:
                self._trilium_repository.disconnect()
            except:
                pass
        
        # Save configuration
        self.save_config()