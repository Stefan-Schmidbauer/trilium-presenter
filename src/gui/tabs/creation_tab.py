"""
Combined Create Tab for TriliumPresenter GUI.
Unifies HTML presentation and PDF document creation with flexible path selection.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import os
import sys
from pathlib import Path

from gui.base_tab import BaseTab
from gui.widgets.modern_messagebox import ModernMessageBox


class CreationTab(BaseTab):
    """Combined tab for HTML and PDF creation with flexible path selection."""
    
    def __init__(self, parent, services, logger=None):
        """Initialize the creation tab."""
        # Format selection variable (before super init)
        self.format_var = tk.StringVar(value="html")

        # Input/Output path variables (before super init)
        # Use absolute paths relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir_var = tk.StringVar(value=str((project_root / "export").absolute()))
        self.output_base_dir = (project_root / "created").absolute()

        # Track if trace callback is already registered
        self._trace_registered = False
        
        # Navigation options for HTML (before super init)
        self.nav_buttons_var = tk.BooleanVar(value=True)
        self.slide_counter_var = tk.BooleanVar(value=True)
        self.presenter_link_var = tk.BooleanVar(value=False)
        self.keyboard_hints_var = tk.BooleanVar(value=True)
        
        # PDF options (before super init)
        self.no_background_var = tk.BooleanVar(value=False)
        
        # UI elements (MUST be before super().__init__!)
        self.input_dir_entry = None
        self.format_html_radio = None
        self.format_pdf_radio = None
        self.html_options_frame = None
        self.pdf_options_frame = None
        self.status_label = None
        self.create_button = None
        
        super().__init__(parent, services, logger)
        
        # Load configuration
        self.load_config()
        
        # Store reference to variables in services for compatibility
        self.services.nav_buttons_var = self.nav_buttons_var
        self.services.slide_counter_var = self.slide_counter_var
        self.services.presenter_link_var = self.presenter_link_var
        self.services.keyboard_hints_var = self.keyboard_hints_var
        
        # Register for export completion events
        if hasattr(self.services, 'register_directory_callback'):
            self.services.register_directory_callback('export_completed', self.on_export_completed)
        
        # Check if there's already an export directory available
        self.check_for_available_export_dir()
        
    def get_tab_title(self) -> str:
        """Return the title for this tab."""
        return "🔧 2. Create"
    
    def setup_tab(self):
        """Setup the creation tab content."""
        # Input directory section
        self.create_input_section()

        # Format selection section
        self.create_format_section()

        # Format-specific options
        self.create_options_sections()

        # Create button
        self.create_button = ttk.Button(self.frame, text="🚀 Create",
                                       command=self.start_creation)
        self.create_button.grid(row=4, column=0, columnspan=2, pady=self.SPACING['large_pady'])

        # Configure grid weights for consistent tab height
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)  # Options sections row expands
    
    def create_input_section(self):
        """Create input directory selection section."""
        input_frame = self.create_section_frame("Input Directory", 0, columnspan=2)
        
        # Description
        desc_label = ttk.Label(input_frame, 
                              text="Select a directory with Markdown files (e.g., from an export)", 
                              font=self.FONTS['description'], foreground="gray")
        desc_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Input directory selection
        input_label = ttk.Label(input_frame, text="Directory:")
        input_label.grid(row=1, column=0, sticky=tk.W, padx=5)
        
        self.input_dir_entry = ttk.Entry(input_frame, textvariable=self.input_dir_var, width=50)
        self.input_dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        browse_button = ttk.Button(input_frame, text="Browse...", command=self.browse_input_dir)
        browse_button.grid(row=1, column=2, padx=5)
        
        # Configure grid
        input_frame.columnconfigure(1, weight=1)
    
    def create_format_section(self):
        """Create format selection section."""
        format_frame = self.create_section_frame("Format", 1, columnspan=2)
        
        # Format selection
        self.format_html_radio = ttk.Radiobutton(format_frame, text="🌐 Slides (HTML)",
                                                variable=self.format_var, value="html",
                                                command=self.update_format_options)
        self.format_html_radio.grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)

        self.format_pdf_radio = ttk.Radiobutton(format_frame, text="📄 Handouts (PDF A4)",
                                               variable=self.format_var, value="pdf",
                                               command=self.update_format_options)
        self.format_pdf_radio.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)

        # Format descriptions
        html_desc = ttk.Label(format_frame,
                             text="Interactive presentations for browsers",
                             font=self.FONTS['description'], foreground="gray")
        html_desc.grid(row=0, column=1, sticky=tk.W, padx=20)

        pdf_desc = ttk.Label(format_frame,
                            text="Printable handouts for participants",
                            font=self.FONTS['description'], foreground="gray")
        pdf_desc.grid(row=1, column=1, sticky=tk.W, padx=20)
    
    def create_options_sections(self):
        """Create format-specific options in a side-by-side layout."""
        options_container = ttk.Frame(self.frame)
        options_container.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=self.SPACING['section_margin'])
        options_container.columnconfigure(0, weight=1)
        options_container.columnconfigure(1, weight=1)

        # Slide Options
        self.html_options_frame = self.create_section_frame("Slide Options", 0, parent=options_container)
        self.html_options_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ttk.Checkbutton(self.html_options_frame, text="Show Next/Prev buttons",
                        variable=self.nav_buttons_var, command=self.save_config).pack(anchor="w", padx=10, pady=2)
        ttk.Checkbutton(self.html_options_frame, text="Show slide counter",
                        variable=self.slide_counter_var, command=self.save_config).pack(anchor="w", padx=10, pady=2)
        ttk.Checkbutton(self.html_options_frame, text="Presenter link on slides",
                        variable=self.presenter_link_var, command=self.save_config).pack(anchor="w", padx=10, pady=2)
        ttk.Checkbutton(self.html_options_frame, text="Show keyboard hints",
                        variable=self.keyboard_hints_var, command=self.save_config).pack(anchor="w", padx=10, pady=2)

        # Handout Options
        self.pdf_options_frame = self.create_section_frame("Handout Options", 0, parent=options_container)
        self.pdf_options_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        ttk.Checkbutton(self.pdf_options_frame, text="Create without background image",
                        variable=self.no_background_var).pack(anchor="w", padx=10, pady=5)
    
    def create_status_section(self):
        """Removed: Status section is no longer needed."""
        pass
    
    def update_format_options(self):
        """Update the state of format-specific options based on selection."""
        is_html = self.format_var.get() == "html"
        
        # Function to recursively enable/disable widgets
        def set_state(widget, state):
            try:
                widget.configure(state=state)
                for child in widget.winfo_children():
                    set_state(child, state)
            except tk.TclError:
                pass  # Ignore errors for widgets without a 'state' option

        # Update HTML options
        html_state = "normal" if is_html else "disabled"
        set_state(self.html_options_frame, html_state)
        # Manually set the LabelFrame title color
        html_title_color = "black" if is_html else "gray"
        self.html_options_frame.config(foreground=html_title_color)


        # Update PDF options
        pdf_state = "normal" if not is_html else "disabled"
        set_state(self.pdf_options_frame, pdf_state)
        # Manually set the LabelFrame title color
        pdf_title_color = "black" if not is_html else "gray"
        self.pdf_options_frame.config(foreground=pdf_title_color)

    
    def browse_input_dir(self):
        """Browse for input directory."""
        current_dir = self.input_dir_var.get()

        # Convert to absolute path for dialog
        initial_dir = Path(current_dir)
        if not initial_dir.is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            initial_dir = project_root / initial_dir
        if not initial_dir.exists():
            initial_dir = Path.home()

        directory = filedialog.askdirectory(title="Select Input Directory",
                                          initialdir=str(initial_dir))
        if directory:
            self.input_dir_var.set(directory)
    
    def start_creation(self):
        """Start the creation process with modal progress dialog."""
        input_path = self.input_dir_var.get()

        # Convert to absolute path if relative
        input_dir = Path(input_path)
        if not input_dir.is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            input_dir = project_root / input_dir

        # Resolve to absolute path
        input_dir = input_dir.resolve()
        format_type = self.format_var.get()

        # Validate input
        if not input_dir.exists():
            ModernMessageBox.showerror("Error", f"Input directory not found!\n\nPath: {input_dir}",
                                      parent=self.services.root)
            return

        md_files = list(input_dir.glob("*.md"))
        if not md_files:
            ModernMessageBox.showerror("Error", f"No Markdown files found!\n\nPath: {input_dir}",
                                      parent=self.services.root)
            return

        # Determine output directory (1:1 without format suffix)
        input_name = input_dir.name
        output_dir = self.output_base_dir / input_name

        # Always stop server if running (simplifies recreation)
        if hasattr(self.services, 'is_running') and self.services.is_running:
            self.log("⏹️ Stopping server before creation...")
            stop_server_callback = self.services.get_gui_callback('stop_server')
            if stop_server_callback:
                stop_server_callback()
                self.log("✅ Server stopped")

        # Disable button during creation
        self.create_button.config(state="disabled")

        # Create modal progress dialog
        progress = tk.Toplevel(self.services.root)
        progress.title("Creating")
        progress.transient(self.services.root)
        progress.grab_set()
        ttk.Label(progress, text=f"⏳ Creating {format_type.upper()}...",
                 font=("Arial", 11)).pack(pady=30, padx=50)
        progress.update()

        try:
            # Perform creation (blocking - no threading)
            success = self.perform_creation(input_dir, output_dir, format_type)
            progress.destroy()

            if success:
                ModernMessageBox.showsuccess("Creation Complete",
                                           f"{format_type.upper()} created successfully!\n\nTo: {output_dir}",
                                           parent=self.services.root)
            else:
                ModernMessageBox.showerror("Creation Failed", "Creation failed",
                                          parent=self.services.root)

        except Exception as e:
            progress.destroy()
            ModernMessageBox.showerror("Creation Failed", str(e),
                                      parent=self.services.root)

        finally:
            # Re-enable button
            self.create_button.config(state="normal")
    
    def perform_creation(self, input_dir: Path, output_dir: Path, format_type: str) -> bool:
        """Perform the actual creation.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Note: Directory cleanup is handled by the generators themselves
            # (trilium_presenter_generator.py and document_pdf_generator.py)
            # to ensure proper cleanup before creation

            self.log(f"Starting {format_type.upper()} creation...")
            self.log(f"Input: {input_dir}")
            self.log(f"Output: {output_dir}")

            if format_type == "html":
                success = self.create_html_presentation(input_dir, output_dir)
            else:
                success = self.create_pdf_documents(input_dir, output_dir)

            if success:
                self.log(f"✅ {format_type.upper()} creation completed successfully!")

                # Notify service container about successful creation
                if self.services and hasattr(self.services, 'notify_directory_event'):
                    self.services.notify_directory_event('creation_completed', str(output_dir))
                    self.log(f"🔄 Made output directory available for subsequent tabs")

                # Update server status if HTML was created
                if format_type == "html":
                    update_server_status = self.services.get_gui_callback('update_server_status')
                    if update_server_status:
                        update_server_status()

            return success

        except Exception as e:
            self.log(f"❌ Error during creation: {e}")
            if self.logger:
                self.logger.error(f"Creation failed: {e}", "creation")
            return False
    
    def create_html_presentation(self, input_dir: Path, output_dir: Path) -> bool:
        """Create HTML presentation using trilium_presenter_generator."""
        try:
            # Get project root (4 levels up: tabs -> gui -> src -> workspace)
            project_root = Path(__file__).parent.parent.parent.parent
            venv_python = project_root / "venv" / "bin" / "python3"
            script_path = project_root / "src" / "trilium_presenter_generator.py"

            if not venv_python.exists():
                python_executable = sys.executable
            else:
                python_executable = str(venv_python)

            if not script_path.exists():
                self.log(f"Script not found: {script_path}")
                return False

            # Run generator with flexible input path
            result = subprocess.run([
                python_executable, str(script_path),
                "--presenter",
                "--input-dir", str(input_dir),
                "--output-dir", str(output_dir)
            ], capture_output=True, text=True, cwd=str(project_root))
            
            if result.returncode == 0:
                return True
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                self.log(f"Generator error: {error_msg}")
                return False
                
        except Exception as e:
            self.log(f"HTML generator error: {e}")
            return False
    
    def create_pdf_documents(self, input_dir: Path, output_dir: Path) -> bool:
        """Create PDF documents using document_pdf_generator."""
        try:
            # Get project root (4 levels up: tabs -> gui -> src -> workspace)
            project_root = Path(__file__).parent.parent.parent.parent
            venv_python = project_root / "venv" / "bin" / "python3"
            script_path = project_root / "src" / "document_pdf_generator.py"

            if not venv_python.exists():
                python_executable = sys.executable
            else:
                python_executable = str(venv_python)

            if not script_path.exists():
                self.log(f"Script not found: {script_path}")
                return False
            
            # Prepare arguments
            args = [
                python_executable, str(script_path),
                "--input-dir", str(input_dir),
                "--output-dir", str(output_dir)
            ]
            
            if self.no_background_var.get():
                args.append("--no-background")

            # Run generator with flexible input path
            result = subprocess.run(args, capture_output=True, text=True, cwd=str(project_root))
            
            if result.returncode == 0:
                return True
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                self.log(f"Generator error: {error_msg}")
                return False
                
        except Exception as e:
            self.log(f"PDF generator error: {e}")
            return False
    
    def load_config(self):
        """Load configuration."""
        try:
            if hasattr(self.services, 'config_file') and self.services.config_file.exists():
                import yaml
                with open(self.services.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}

                nav_config = config.get('navigation', {})
                self.nav_buttons_var.set(nav_config.get('show_nav_buttons', True))
                self.slide_counter_var.set(nav_config.get('show_slide_counter', True))
                self.presenter_link_var.set(nav_config.get('show_presenter_link', False))
                self.keyboard_hints_var.set(nav_config.get('show_keyboard_hints', True))

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not load configuration: {e}", "creation")
    
    def save_config(self):
        """Save configuration."""
        try:
            if not hasattr(self.services, 'config_file'):
                return
                
            self.services.config_file.parent.mkdir(exist_ok=True)
            
            # Load existing config
            existing_config = {}
            if self.services.config_file.exists():
                import yaml
                with open(self.services.config_file, 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f) or {}
            
            # Update navigation config
            existing_config['navigation'] = {
                'show_nav_buttons': self.nav_buttons_var.get(),
                'show_slide_counter': self.slide_counter_var.get(),
                'show_presenter_link': self.presenter_link_var.get(),
                'show_keyboard_hints': self.keyboard_hints_var.get()
            }
            
            import yaml
            with open(self.services.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(existing_config, f, default_flow_style=False)
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not save configuration: {e}", "creation")
    
    def on_export_completed(self, export_dir: str):
        """Called when export is completed - update input directory."""
        try:
            # Update input directory to the newly exported directory
            self.input_dir_var.set(export_dir)
            self.log(f"📁 Input directory automatically set: {export_dir}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update input directory: {e}", "creation")
    
    def check_for_available_export_dir(self):
        """Check if there's already an export directory available from previous export."""
        try:
            if hasattr(self.services, 'last_export_dir'):
                last_export = self.services.last_export_dir.get()
                if last_export and Path(last_export).exists():
                    # Only set if current input directory is default or doesn't exist
                    current_input = Path(self.input_dir_var.get())
                    project_root = Path(__file__).parent.parent.parent.parent
                    default_export_path = str(project_root / "export")
                    if not current_input.exists() or self.input_dir_var.get() == default_export_path:
                        self.input_dir_var.set(last_export)
                        self.log(f"📁 Existing export directory automatically loaded: {last_export}")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not check for available export directory: {e}", "creation")
    
    def log(self, message: str):
        """Log message to console only (no GUI output)."""
        # Print to console for debugging
        print(f"[Creation] {message}")

        # Optional: Log to file logger
        if self.logger:
            self.logger.info(message, "creation")