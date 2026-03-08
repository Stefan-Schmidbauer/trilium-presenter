"""
Server Tab for TriliumPresenter GUI.
Updated for flexible directory selection and modern structure.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import threading
import http.server
import socketserver
import webbrowser
import socket
import os
import time
from pathlib import Path

from gui.base_tab import BaseTab


class ServerTab(BaseTab):
    """Tab for HTTP Server with flexible directory selection."""
    
    def __init__(self, parent, services, logger=None):
        """Initialize the server tab."""
        # Server variables (before super init)
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.current_port = 8800  # Starting port for presentations (less commonly used than 8080)

        # Directory variables (before super init)
        # Use absolute paths relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        self.serve_dir_var = tk.StringVar(value=str((project_root / "created").absolute()))
        self.current_serve_dir = None
        
        # Browser variables - will be initialized from service
        self.available_browsers = {}
        self.selected_browser = tk.StringVar(value="auto")
        self.browser_config = {"preferred": "auto", "fallback": "auto"}
        
        # UI elements (MUST be before super().__init__!)
        self.serve_dir_entry = None
        self.server_status_label = None
        self.url_label = None
        self.port_var = None
        self.port_entry = None
        self.start_button = None
        self.stop_button = None
        self.presentation_button = None
        self.presenter_button = None
        self.browser_combo = None
        self.browser_info_label = None
        self.presenter_status_label = None
        
        super().__init__(parent, services, logger)
        
        # Load configuration and detect browsers (after logger is set)
        self.load_config()
        self.setup_browser_from_service()
        self.setup_port_from_service()
        self.auto_detect_free_port_on_startup()
        
        # Store references in services for compatibility
        self.services.current_port = self.current_port
        self.services.is_running = self.is_running
        self.services.server = self.server
        self.services.server_thread = self.server_thread
        self.services.available_browsers = self.available_browsers
        self.services.selected_browser = self.selected_browser
        self.services.browser_config = self.browser_config
        
        # Register for creation completion events
        if hasattr(self.services, 'register_directory_callback'):
            self.services.register_directory_callback('creation_completed', self.on_creation_completed)
        
        # Check if there's already a creation output directory available
        self.check_for_available_creation_dir()
        
    def get_tab_title(self) -> str:
        """Return the title for this tab."""
        return "🌐 3. Present"
    
    def setup_tab(self):
        """Setup the server tab content."""
        # Directory selection section
        self.create_directory_section()

        # Server configuration section
        self.create_server_section()

        # Browser section
        self.create_browser_section()

        # Server controls section
        self.create_controls_section()

        # Server status section
        self.create_status_section()

        # Update initial status
        self.update_server_status()

        # Configure grid weights for consistent tab height
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(5, weight=1)  # Status section expands
    
    def create_directory_section(self):
        """Create directory selection section."""
        dir_frame = self.create_section_frame("Select Directory", 1, columnspan=2)
        
        # Description
        desc_label = ttk.Label(dir_frame, 
                              text="Select the directory containing the HTML presentation", 
                              font=self.FONTS['description'], foreground="gray")
        desc_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Directory selection
        dir_label = ttk.Label(dir_frame, text="Directory:")
        dir_label.grid(row=1, column=0, sticky=tk.W, padx=5)
        
        self.serve_dir_entry = ttk.Entry(dir_frame, textvariable=self.serve_dir_var, width=50)
        self.serve_dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.serve_dir_var.trace_add("write", lambda *args: self.update_server_status())
        
        browse_dir_button = ttk.Button(dir_frame, text="Browse...", command=self.browse_serve_dir)
        browse_dir_button.grid(row=1, column=2, padx=5)
        
        # Quick select buttons
        quick_frame = ttk.Frame(dir_frame)
        quick_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))

        project_root = Path(__file__).parent.parent.parent.parent
        ttk.Button(quick_frame, text="created/",
                   command=lambda: self.serve_dir_var.set(str((project_root / "created").absolute()))).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="export/",
                   command=lambda: self.serve_dir_var.set(str((project_root / "export").absolute()))).pack(side=tk.LEFT, padx=2)
        
        # Configure grid
        dir_frame.columnconfigure(1, weight=1)
    
    def create_server_section(self):
        """Create server configuration section."""
        server_frame = self.create_section_frame("Server Configuration", 2, columnspan=2)

        # Port configuration
        port_label = ttk.Label(server_frame, text="Port:")
        port_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.port_var = tk.StringVar(value=str(self.current_port))
        self.port_entry = ttk.Entry(server_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.port_var.trace_add("write", lambda *args: self.update_server_status())

        # Manual port search button
        auto_port_button = ttk.Button(server_frame, text="🔍 Find New Port", command=self.auto_detect_port)
        auto_port_button.grid(row=0, column=2, padx=5, pady=5)
    
    def create_browser_section(self):
        """Create browser selection section."""
        browser_frame = self.create_section_frame("Browser Selection", 3, columnspan=2)
        
        # Browser selection
        browser_label = ttk.Label(browser_frame, text="Browser:")
        browser_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Browser values will be set by setup_browser_from_service()
        self.browser_combo = ttk.Combobox(browser_frame, textvariable=self.selected_browser, 
                                         state="readonly", width=30)
        self.browser_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.browser_combo.bind("<<ComboboxSelected>>", self.on_browser_changed)
        
        # Refresh browsers button
        refresh_button = ttk.Button(browser_frame, text="🔄 Refresh Browsers", command=self.refresh_browsers)
        refresh_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Browser info
        self.browser_info_label = ttk.Label(browser_frame, text="", 
                                           font=self.FONTS['description'], foreground="gray")
        self.browser_info_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        self.update_browser_info()
    
    def create_controls_section(self):
        """Create server control buttons."""
        controls_frame = ttk.Frame(self.frame)
        controls_frame.grid(row=4, column=0, columnspan=2, pady=self.SPACING['section_margin'])
        
        # Server controls
        self.start_button = ttk.Button(controls_frame, text="🚀 Start Server", 
                                      command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(controls_frame, text="⏹️ Stop Server", 
                                     command=self.stop_server, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Presentation controls
        separator = ttk.Separator(controls_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill='y', padx=10)
        
        self.presentation_button = ttk.Button(controls_frame, text="🎬 Open Presentation", 
                                             command=self.open_presentation, state="disabled")
        self.presentation_button.pack(side=tk.LEFT, padx=5)
        
        self.presenter_button = ttk.Button(controls_frame, text="🎯 Presenter Mode",
                                          command=self.open_presenter_view, state="disabled")
        self.presenter_button.pack(side=tk.LEFT, padx=5)

    def create_status_section(self):
        """Create a compact and informative server status bar."""
        status_frame = self.create_section_frame("Status", 5, columnspan=2)
        status_frame.columnconfigure(1, weight=1)

        # Main status bar frame (ohne schwarzen Rahmen)
        bar_frame = ttk.Frame(status_frame, padding=5)
        bar_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        # Configure grid for the bar
        bar_frame.columnconfigure(1, weight=0)
        bar_frame.columnconfigure(3, weight=0)
        bar_frame.columnconfigure(5, weight=0)
        bar_frame.columnconfigure(7, weight=1)

        # --- Server Status ---
        ttk.Label(bar_frame, text="Server:", font=self.FONTS['label_bold']).grid(row=0, column=0, padx=(5, 2), sticky="w")
        self.server_status_label = ttk.Label(bar_frame, text="Stopped", foreground="gray", font=self.FONTS['label'])
        self.server_status_label.grid(row=0, column=1, sticky="w")

        # --- Port Status ---
        ttk.Label(bar_frame, text="Port:", font=self.FONTS['label_bold']).grid(row=0, column=2, padx=(15, 2), sticky="w")
        self.port_status_label = ttk.Label(bar_frame, text="Checking...", foreground="gray", font=self.FONTS['label'])
        self.port_status_label.grid(row=0, column=3, sticky="w")

        # --- Directory/File Status ---
        ttk.Label(bar_frame, text="Directory:", font=self.FONTS['label_bold']).grid(row=0, column=4, padx=(15, 2), sticky="w")
        self.presenter_status_label = ttk.Label(bar_frame, text="Checking...", foreground="gray", font=self.FONTS['label'])
        self.presenter_status_label.grid(row=0, column=5, sticky="w")

        # --- URL Display (integriert in die Status-Bar) ---
        ttk.Label(bar_frame, text="URL:", font=self.FONTS['label_bold']).grid(row=0, column=6, padx=(15, 2), sticky="w")
        self.url_label = ttk.Label(bar_frame, text="---", foreground="gray", font=self.FONTS['label'])
        self.url_label.grid(row=0, column=7, sticky="w")


    def browse_serve_dir(self):
        """Browse for directory to serve."""
        directory = filedialog.askdirectory(title="Select Directory to Serve",
                                          initialdir=self.serve_dir_var.get())
        if directory:
            self.serve_dir_var.set(directory)

    def update_server_status(self):
        """Update the compact server status display."""
        if not self.presenter_status_label:
            return  # Widgets not ready

        serve_dir = Path(self.serve_dir_var.get())
        port_str = self.port_var.get() if hasattr(self, 'port_var') else str(self.current_port)

        # 1. Update Server Status
        if self.is_running:
            self.server_status_label.config(text="Running", foreground="green")
            self.url_label.config(text=f"http://localhost:{port_str}", foreground="blue")
        else:
            self.server_status_label.config(text="Stopped", foreground="gray")
            self.url_label.config(text="---", foreground="gray")

        # 2. Update Port Status
        try:
            port_num = int(port_str)
            if self.is_running and port_num == self.current_port:
                self.port_status_label.config(text=f"{port_num} (In Use)", foreground="blue")
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    if s.connect_ex(('127.0.0.1', port_num)) == 0:
                        self.port_status_label.config(text=f"{port_num} (In Use)", foreground="orange")
                    else:
                        self.port_status_label.config(text=f"{port_num} (Available)", foreground="green")
        except (ValueError, TypeError):
            self.port_status_label.config(text="Invalid", foreground="red")
        except Exception:
            self.port_status_label.config(text="Error", foreground="red")

        # 3. Update Directory/File Status
        if not serve_dir.is_absolute():
             serve_dir = Path.cwd() / serve_dir
        
        if not serve_dir.exists():
            self.presenter_status_label.config(text="Directory not found", foreground="red")
            return

        if not serve_dir.is_dir():
            self.presenter_status_label.config(text="Path is not a directory", foreground="red")
            return

        html_files = list(serve_dir.glob("**/*.html"))
        if not html_files:
            self.presenter_status_label.config(text="No HTML files found", foreground="orange")
        else:
            self.presenter_status_label.config(
                text=f"{len(html_files)} HTML file{'s' if len(html_files) != 1 else ''} ready",
                foreground="blue"
            )
    
    def start_server(self):
        """Start the HTTP server."""
        try:
            serve_dir_str = self.serve_dir_var.get()
            serve_dir = Path(serve_dir_str)
            self.log(f"🔍 Checking directory: '{serve_dir_str}' -> {serve_dir.absolute()}")
            if not serve_dir.exists():
                self.log(f"❌ Directory not found: {serve_dir.absolute()}")
                return
            
            port = int(self.port_var.get())
            self.current_port = port
            
            # Change to serve directory (MUST remain during server operation)
            original_dir = os.getcwd()
            os.chdir(serve_dir)
            self.current_serve_dir = serve_dir
            self.original_dir = original_dir  # Store for cleanup
            
            # Create server with SO_REUSEADDR to allow immediate port reuse
            # This prevents "Address already in use" errors after stopping the server
            handler = http.server.SimpleHTTPRequestHandler

            # Create a custom TCPServer class with allow_reuse_address
            class ReusableTCPServer(socketserver.TCPServer):
                allow_reuse_address = True

            self.server = ReusableTCPServer(("", port), handler)

            # Start server in background thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.is_running = True
            
            # Update UI
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.presentation_button.config(state="normal")
            self.presenter_button.config(state="normal")

            self.log(f"✅ Server started on http://localhost:{port}")
            self.log(f"📁 Serving: {serve_dir.absolute()}")

            self.update_server_status()
            
        except Exception as e:
            self.log(f"❌ Error starting server: {e}")
            self.is_running = False
    
    def stop_server(self):
        """Stop the HTTP server."""
        try:
            if self.server:
                # Shutdown server gracefully
                self.server.shutdown()
                # Close the socket properly to release the port
                self.server.server_close()
                self.server = None

            if self.server_thread:
                # Wait a moment for thread to finish
                self.server_thread.join(timeout=1.0)
                self.server_thread = None

            self.is_running = False
            
            # Restore original working directory 
            if hasattr(self, 'original_dir') and self.original_dir:
                try:
                    os.chdir(self.original_dir)
                    self.log(f"🔄 Working directory restored to {self.original_dir}")
                except Exception as e:
                    self.log(f"⚠️ Could not restore working directory: {e}")
            
            # Update UI
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.presentation_button.config(state="disabled")
            self.presenter_button.config(state="disabled")

            self.log("⏹️ Server stopped")

            self.update_server_status()
            
        except Exception as e:
            self.log(f"❌ Error stopping server: {e}")
    
    def open_presentation(self):
        """Open presentation in browser."""
        if not self.is_running:
            self.log("❌ Server is not running!")
            return
        
        # Look for main presentation files
        serve_dir = Path(self.serve_dir_var.get())
        presentation_files = [
            "index.html",
            "presentation.html",
            "main.html"
        ]
        
        self.log(f"🔍 Searching presentation files in: {serve_dir}")
        url = None
        for filename in presentation_files:
            presentation_file = serve_dir / filename
            if presentation_file.exists():
                url = f"http://localhost:{self.current_port}/{filename}"
                self.log(f"✅ Found {filename}")
                break
        
        if not url:
            # Fallback to root directory
            url = f"http://localhost:{self.current_port}/"
            self.log(f"⚠️ No presentation file found, using Root-URL")
        
        self.open_url_in_browser(url)
        self.log(f"🎬 Presentation opened: {url}")
    
    def open_presenter_view(self):
        """Open presenter view in browser."""
        if not self.is_running:
            self.log("❌ Server is not running!")
            return
        
        # Look for presenter files in order of preference
        serve_dir = Path(self.serve_dir_var.get())
        presenter_files = [
            "simple_presenter.html",
            "presenter.html", 
            "index.html"
        ]
        
        self.log(f"🔍 Searching presenter files in: {serve_dir}")
        url = None
        for filename in presenter_files:
            presenter_file = serve_dir / filename
            if presenter_file.exists():
                url = f"http://localhost:{self.current_port}/{filename}"
                self.log(f"✅ Found {filename}")
                break
        
        if not url:
            url = f"http://localhost:{self.current_port}/?presenter"
            self.log(f"⚠️ No presenter file found, using ?presenter parameter")
        
        self.log(f"🌐 Trying to open browser: {url}")
        self.open_url_in_browser(url)
        self.log(f"🎯 Presenter Mode opened: {url}")
    
    def open_url_in_browser(self, url: str):
        """Open URL in selected browser."""
        try:
            if self.services and hasattr(self.services, 'browser_service'):
                # Use browser service to open URL
                success = self.services.browser_service.open_url(url)
                if not success:
                    self.log(f"⚠️ Browser service failed, using fallback")
                    webbrowser.open(url)
            else:
                # Fallback to system default
                webbrowser.open(url)
                
        except Exception as e:
            self.log(f"❌ Error opening browser: {e}")
            # Ultimate fallback to default browser
            try:
                webbrowser.open(url)
            except:
                self.log(f"❌ Even default browser could not be opened!")
    
    def setup_browser_from_service(self):
        """Setup browser selection using the browser service."""
        if self.services and hasattr(self.services, 'browser_service'):
            # Get browsers from service
            self.available_browsers = self.services.browser_service.get_available_browsers()
            preferred = self.services.browser_service.get_preferred_browser()
            
            # Set selected browser
            self.selected_browser.set(preferred)
            
            # Update combobox values if it exists
            if hasattr(self, 'browser_combo') and self.browser_combo:
                browser_values = list(self.available_browsers.values())
                self.browser_combo['values'] = browser_values
                # Set the display value
                if preferred in self.available_browsers:
                    self.selected_browser.set(self.available_browsers[preferred])
                else:
                    self.selected_browser.set('System Default')
            
            if self.logger:
                self.logger.info(f"Browsers loaded from service: {len(self.available_browsers)} found", "server")
        else:
            if self.logger:
                self.logger.warning("Browser service not available", "server")
    
    def setup_port_from_service(self):
        """Setup port using the server service."""
        if self.services and hasattr(self.services, 'server_service'):
            # Get current port from service
            self.current_port = self.services.server_service.get_port()
            if hasattr(self, 'port_var'):
                self.port_var.set(str(self.current_port))
            
            if self.logger:
                self.logger.info(f"Port loaded from service: {self.current_port}", "server")
    
    def auto_detect_free_port_on_startup(self):
        """Automatically find and set a free port during startup."""
        if self.services and hasattr(self.services, 'server_service'):
            original_port = self.current_port
            free_port = self.services.server_service.find_free_port(original_port)

            if free_port and free_port != original_port:
                self.current_port = free_port
                if hasattr(self, 'port_var'):
                    self.port_var.set(str(free_port))
                # Sync with service (but don't save to config)
                self.services.server_service.current_port = free_port

                if self.logger:
                    self.logger.info(f"🔍 Free port automatically found: {original_port} → {free_port}", "server")
            elif free_port == original_port:
                if self.logger:
                    self.logger.info(f"✅ Port {original_port} is already free", "server")
            else:
                if self.logger:
                    self.logger.warning(f"⚠️ No free port found, using {original_port}", "server")
    
    def auto_detect_port(self):
        """Manually search for a new free port."""
        if self.services and hasattr(self.services, 'server_service'):
            # Start searching from next port
            search_start = self.current_port + 1
            free_port = self.services.server_service.find_free_port(search_start)
            if free_port:
                self.current_port = free_port
                self.port_var.set(str(free_port))
                # Sync with service (but don't save to config)
                self.services.server_service.current_port = free_port
                self.port_status_label.config(text=f"🔍 Port {free_port}", foreground="green")
                self.log(f"✅ New free port found: {free_port}")
            else:
                self.log(f"❌ No free port found!")
        else:
            self.log(f"❌ Server service not available!")
    
    def refresh_browsers(self):
        """Refresh browser detection."""
        if self.services and hasattr(self.services, 'browser_service'):
            # Re-detect browsers
            self.services.browser_service._detect_browsers()
            self.setup_browser_from_service()
            self.update_browser_info()
            self.log("🔄 Browser list updated")
        else:
            self.log("❌ Browser service not available!")
    
    def on_browser_changed(self, event):
        """Handle browser selection change."""
        # Get the selected display value and find corresponding browser ID
        selected_display = self.selected_browser.get()
        
        # Find browser ID from display value
        browser_id = 'auto'
        for bid, bname in self.available_browsers.items():
            if bname == selected_display:
                browser_id = bid
                break
        
        # Update service preference
        if self.services and hasattr(self.services, 'browser_service'):
            self.services.browser_service.set_preferred_browser(browser_id)
        
        self.update_browser_info()
        self.save_config()
    
    def update_browser_info(self):
        """Update browser info display."""
        if not self.browser_info_label:
            return
            
        selected_display = self.selected_browser.get()
        
        # Find browser ID from display name
        browser_id = 'auto'
        for bid, bname in self.available_browsers.items():
            if bname == selected_display:
                browser_id = bid
                break
        
        if browser_id == "auto":
            self.browser_info_label.config(text="Uses system default browser")
        elif browser_id in self.available_browsers:
            self.browser_info_label.config(text=f"Browser: {selected_display} (ID: {browser_id})")
        else:
            self.browser_info_label.config(text="Browser not available")
    
    def load_config(self):
        """Load configuration."""
        # Note: Port is NOT loaded from config anymore.
        # We always start fresh with port 8800 and auto-detect a free port.
        # This ensures the presentation server always finds a working port,
        # since the actual port number is irrelevant to the user.
        try:
            if hasattr(self.services, 'config_service'):
                # Browser config is still handled by browser service
                if self.logger:
                    self.logger.info(f"Configuration loaded (port auto-detected: {self.current_port})", "server")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not load server configuration: {e}", "server")
    
    def save_config(self):
        """Save configuration."""
        try:
            # Save through service container
            if self.services:
                self.services.save_config()
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not save server configuration: {e}", "server")
    
    def on_creation_completed(self, creation_output_dir: str):
        """Called when creation is completed - update serve directory."""
        try:
            # Check if this is an HTML output directory
            creation_path = Path(creation_output_dir).absolute()
            if creation_path.exists() and any(creation_path.glob("*.html")):
                # Set serve directory directly to the HTML output directory (absolute path)
                # This allows serving the HTML files directly from their location
                self.serve_dir_var.set(str(creation_path))
                self.log(f"📁 Serve directory automatically set: {creation_path}")
                
                # Update status display (safe async)
                try:
                    self.update_server_status()
                except Exception as e:
                    self.log(f"⚠️ Status update failed: {e}")
            else:
                # PDF or non-HTML output - don't auto-select
                self.log(f"ℹ️ Created: {creation_output_dir} (no HTML directory)")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update serve directory: {e}", "server")
    
    def check_for_available_creation_dir(self):
        """Check if there's already a creation output directory available from previous creation."""
        try:
            if hasattr(self.services, 'last_creation_output_dir'):
                last_creation = self.services.last_creation_output_dir.get()
                if last_creation and Path(last_creation).exists():
                    # Check if it contains HTML files
                    creation_path = Path(last_creation)
                    if any(creation_path.glob("*.html")):
                        # Only set if current serve directory is default or doesn't exist
                        current_serve = Path(self.serve_dir_var.get())
                        project_root = Path(__file__).parent.parent.parent.parent
                        default_paths = [str(project_root / "created"), str(project_root / "export")]
                        if not current_serve.exists() or self.serve_dir_var.get() in default_paths:
                            self.serve_dir_var.set(str(Path(last_creation).absolute()))
                            self.log(f"📁 Existing HTML directory automatically loaded: {Path(last_creation).absolute()}")
                            self.update_server_status()
                            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not check for available creation directory: {e}", "server")
    
    def log(self, message: str):
        """Log message to console only (no GUI output)."""
        # Print to console for debugging
        print(f"[Server] {message}")

        # Optional: Log to file logger
        if self.logger:
            self.logger.info(message, "server")