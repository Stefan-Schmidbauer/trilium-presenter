#!/usr/bin/env python3
"""
TriliumPresenter - Modular GUI for HTML Presentations
Refactored main window with tab-based architecture and service layer.
"""

import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path
from typing import Dict, Any

# Import unified logging system
try:
    from .. import logging_manager
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    import logging_manager

# Note: Repository-based approach, no direct API imports needed

# Import modular GUI components
from gui.services import BrowserService, ServerService
from gui.service_container import ServiceContainer

# Import tab classes
try:
    from gui.tabs.export_tab import ExportTab
    from gui.tabs.creation_tab import CreationTab
    from gui.tabs.server_tab import ServerTab
except ImportError as e:
    print(f"Warning: Could not import tab modules: {e}")
    ExportTab = CreationTab = ServerTab = None


class TriliumPresenterGUI:
    """Main GUI application for TriliumPresenter."""
    
    def __init__(self, root):
        """Initialize the main GUI."""
        self.root = root

        # Set application icon FIRST (before title/geometry)
        self._set_app_icon()

        self.root.title("TriliumPresenter - HTML Presentation Generator")
        self.root.geometry("1100x780")
        self.root.resizable(True, True)

        # Create service container
        self.services = ServiceContainer(root)
        
        # Tab storage
        self.tabs = {}
        
        # Setup logging
        self.setup_logging()
        
        # Setup GUI callbacks in service container
        self.setup_service_callbacks()
        
        # Setup GUI
        self.setup_gui()
        
        # Initialize API connection
        self.auto_connect_api()
        
        self.logger.info("TriliumPresenter GUI initialized", "gui")
    
    def _set_app_icon(self):
        """Set application window icon with multiple sizes for best display quality."""
        try:
            config_dir = Path(__file__).parent.parent.parent / "config"

            # Method 1: Try .ico file first (works best on Windows/some Linux WMs)
            ico_file = config_dir / "icon.ico"
            if ico_file.exists():
                try:
                    self.root.iconbitmap(str(ico_file))
                    return  # Success, no need to try PNG method
                except Exception:
                    pass  # Fall through to PNG method

            # Method 2: Load multiple PNG sizes (works on most modern systems)
            icon_sizes = ['16', '32', '48', '64']
            icons = []

            for size in icon_sizes:
                icon_file = config_dir / f"icon-{size}.png"
                if not icon_file.exists() and size == '64':
                    # Fallback to icon.png for 64x64
                    icon_file = config_dir / "icon.png"

                if icon_file.exists():
                    try:
                        icon = tk.PhotoImage(file=str(icon_file))
                        icons.append(icon)
                    except Exception:
                        pass

            if icons:
                # Set all icon sizes (iconphoto True = use for all toplevels)
                self.root.iconphoto(True, *icons)
                # Store reference to prevent garbage collection
                self._icons = icons

        except Exception:
            # Silently fail - icon is optional
            pass

    def setup_logging(self):
        """Setup logging system."""
        try:
            logging_config = {}
            logging_config_file = Path("config/logging.yaml")
            
            if logging_config_file.exists():
                import yaml
                with open(logging_config_file, 'r', encoding='utf-8') as f:
                    logging_config = yaml.safe_load(f) or {}
            
            self.logger = logging_manager.setup_logging(logging_config)
            self.logger.set_gui_callback(self._gui_log_callback)
            self.logger.set_gui_root(self.root)  # Set root window for thread-safe messageboxes
            self.logger.enable_destination('gui')
            self.logger.enable_destination('messagebox')

            # Store logger in services for tabs
            self.services.logger = self.logger
            
            # Setup error handling system
            self.services.setup_error_handling(self.logger)
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
    
    def setup_service_callbacks(self):
        """Setup GUI callbacks in the service container."""
        self.services.register_gui_callback('log_error', lambda msg: self.logger.error(msg, 'gui'))
        self.services.register_gui_callback('show_status', self._show_status)
        self.services.register_gui_callback('update_server_status', self.update_server_status)
        self.services.register_gui_callback('stop_server', self._stop_server_from_callback)
    
    def setup_gui(self):
        """Create the main GUI layout."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title and status frame
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky=(tk.W, tk.E))

        # Title
        title_label = ttk.Label(title_frame, text="TriliumPresenter",
                               font=("Arial", 14, "bold"))
        title_label.pack(side=tk.LEFT)

        # Status label (right side)
        self.status_label = ttk.Label(title_frame, text="⏳ Initializing...",
                                      foreground="gray")
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create all tabs
        self.create_tabs()

        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=self.on_closing)
        close_button.grid(row=2, column=0, pady=(10, 0), sticky=tk.E)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        title_frame.columnconfigure(0, weight=1)
    
    def create_tabs(self):
        """Create all GUI tabs."""
        tab_classes = [
            ("export", ExportTab),
            ("creation", CreationTab),
            ("server", ServerTab)
        ]

        for tab_name, tab_class in tab_classes:
            if tab_class:
                try:
                    self.tabs[tab_name] = tab_class(self.notebook, self.services, self.logger)
                    self.logger.info(f"✅ Tab '{tab_name}' created successfully", "gui")

                    # Store tab references in service container for inter-tab communication
                    if tab_name == "export":
                        self.services.export_tab = self.tabs[tab_name]
                    elif tab_name == "creation":
                        self.services.creation_tab = self.tabs[tab_name]
                    elif tab_name == "server":
                        self.services.server_tab = self.tabs[tab_name]

                except Exception as e:
                    import traceback
                    self.logger.error(f"Failed to create {tab_name} tab: {e}", "gui")
                    self.logger.error(f"Traceback: {traceback.format_exc()}", "gui")
            else:
                self.logger.warning(f"Tab class for {tab_name} not available", "gui")
    
    def auto_connect_api(self):
        """Auto-connect to Trilium API if configuration is available."""
        try:
            server_url = self.services.trilium_server_var.get().strip()
            token = self.services.trilium_token_var.get().strip()

            if server_url and token:
                # Update status
                self._update_status("⏳ Connecting to Trilium...", "gray")

                def connect():
                    try:
                        # Repository connection is handled in service container
                        # Use quick_test=True for fast startup (skips prefix scan)
                        if self.services.trilium_repository:
                            self.services.trilium_repository.test_connection(quick_test=True)
                            self.logger.info("Repository auto-connection successful", "gui")

                            # Update status in main thread
                            self.root.after(0, lambda: self._update_status("✅ Ready", "green"))
                    except Exception as e:
                        self.logger.warning(f"Repository auto-connection failed: {e}", "gui")

                        # Update status in main thread
                        self.root.after(0, lambda: self._update_status("⚠️ No Connection", "orange"))

                import threading
                threading.Thread(target=connect, daemon=True).start()
            else:
                # No credentials configured
                self._update_status("⚠️ Not Configured", "orange")

        except Exception as e:
            self.logger.error(f"Error in auto-connection thread: {e}", "gui")
            self._update_status("❌ Error", "red")

    def _update_status(self, message: str, color: str = "gray"):
        """Update the status label."""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message, foreground=color)
    
    def update_server_status(self):
        """Update server status (called by creation tab)."""
        if 'server' in self.tabs and hasattr(self.tabs['server'], 'update_server_status'):
            self.tabs['server'].update_server_status()
    
    def save_config(self):
        """Save current configuration."""
        self.services.save_config()
    
    def _show_status(self, message: str, level: str = "info"):
        """Show status message callback for services."""
        getattr(self.logger, level)(message, "gui")
    
    def _gui_log_callback(self, message: str):
        """Callback for GUI logging - writes to all available text widgets."""
        try:
            # Check if the main loop is running
            try:
                self.root.tk.call('info', 'exists', '.')
            except tk.TclError:
                return
                
            # Filter verbose messages
            if self._should_filter_message(message):
                return
                
            # List of text widgets that should receive log messages
            text_widgets = []
            
            # Collect text widgets from all tabs
            for tab_name, tab in self.tabs.items():
                if hasattr(tab, 'output_text') and tab.output_text:
                    text_widgets.append(tab.output_text)
                
                # Tab-specific output widgets (updated for new tab structure)
                if hasattr(tab, 'server_output_text') and tab.server_output_text:
                    text_widgets.append(tab.server_output_text)
            
            # Update all text widgets
            for widget in text_widgets:
                try:
                    widget.insert(tk.END, message + "\n")
                    widget.see(tk.END)
                except tk.TclError:
                    pass  # Widget was destroyed
            
            self.root.update()
            
        except Exception:
            pass  # Ignore GUI errors
    
    def _stop_server_from_callback(self):
        """Stop the server via callback from another tab."""
        try:
            if 'server' in self.tabs and self.tabs['server']:
                self.tabs['server'].stop_server()
        except Exception as e:
            self.logger.error(f"Failed to stop server via callback: {e}", "gui")

    def _should_filter_message(self, message: str) -> bool:
        """Filter out verbose technical messages."""
        filter_patterns = [
            "Browser gefunden:",
            "Found X active",
            "Registered attachment:",
            "Extracted file:",
            "Resolved filename",
            "Output directory:",
            "SQL:",
            "DEBUG:",
            "Filtered out X deleted",
            "Setting up HTML output structure in /",
            "Individual file processing",
            "Database query:",
            "Path resolution:",
            "Auto-selection:",
            "Available browsers:",
        ]
        
        for pattern in filter_patterns:
            if pattern.lower() in message.lower():
                return True
                
        if message.strip().startswith("python3 ") and "src/" in message:
            return True
            
        return False
    
    def on_closing(self):
        """Handle window closing."""
        self.logger.info("Closing TriliumPresenter GUI", "gui")
        
        # Cleanup services
        self.services.cleanup()
        
        # Destroy window
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = TriliumPresenterGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start GUI
    root.mainloop()


if __name__ == "__main__":
    main()