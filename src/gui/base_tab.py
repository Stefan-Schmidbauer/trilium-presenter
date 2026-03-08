"""
Base Tab class for TriliumPresenter GUI tabs.
Provides common interface and functionality for all tabs.
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .service_container import ServiceContainer


class BaseTab(ABC):
    """Abstract base class for GUI tabs."""
    
    # Design constants for consistent GUI appearance
    FONTS = {
        'title': ("Arial", 12, "bold"),
        'section': ("Arial", 10, "bold"),
        'label': ("Arial", 9),
        'label_bold': ("Arial", 9, "bold"),
        'description': ("Arial", 9),
        'main_title': ("Arial", 16, "bold"),
        'monospace': ("Courier", 9)
    }
    
    WIDGET_SIZES = {
        'output_text': {'height': 8, 'width': 70},
        'combobox_standard': {'width': 30},
        'combobox_small': {'width': 20},
        'entry_url': {'width': 40},
        'entry_port': {'width': 8},
        'listbox_standard': {'height': 8}
    }
    
    SPACING = {
        'section_padding': 5,
        'standard_padx': 5,
        'standard_pady': 5,
        'large_pady': 10,
        'small_pady': 2,
        'section_margin': (0, 10)
    }
    
    def __init__(self, parent, services: 'ServiceContainer', logger=None):
        """
        Initialize base tab.
        
        Args:
            parent: The parent widget (usually a Notebook)
            services: ServiceContainer with all required services
            logger: Logger instance (optional, will try to get from services)
        """
        self.parent = parent
        self.services = services
        self.logger = logger or getattr(services, 'logger', None)
        
        # Create the main frame for this tab
        self.frame = ttk.Frame(parent)
        
        # Setup the tab content
        self.setup_tab()
        
        # Add to notebook with tab title
        parent.add(self.frame, text=self.get_tab_title())
    
    @abstractmethod
    def get_tab_title(self) -> str:
        """Return the title for this tab."""
        pass
    
    @abstractmethod  
    def setup_tab(self):
        """Setup the tab content. Override in subclasses."""
        pass
    
    def create_section_frame(self, title: str, row: int, column: int = 0,
                           columnspan: int = 1, sticky: str = "ew", parent=None) -> ttk.LabelFrame:
        """
        Create a labeled section frame with consistent styling.

        Args:
            title: Section title
            row: Grid row
            column: Grid column
            columnspan: Grid column span
            sticky: Grid sticky option
            parent: Optional parent widget (defaults to self.frame)

        Returns:
            ttk.LabelFrame: The created section frame
        """
        parent_widget = parent if parent is not None else self.frame
        section_frame = ttk.LabelFrame(parent_widget, text=title,
                                     padding=str(self.SPACING['section_padding']))
        section_frame.grid(row=row, column=column, columnspan=columnspan,
                          sticky=sticky,
                          padx=self.SPACING['standard_padx'],
                          pady=self.SPACING['standard_pady'])
        return section_frame
    
    def create_button_frame(self, parent, buttons_config: list) -> ttk.Frame:
        """
        Create a frame with buttons.
        
        Args:
            parent: Parent widget
            buttons_config: List of dicts with button config
                           [{"text": "Button", "command": callback, "state": "normal"}]
        
        Returns:
            ttk.Frame: Frame containing the buttons
        """
        button_frame = ttk.Frame(parent)
        
        for i, config in enumerate(buttons_config):
            button = ttk.Button(button_frame, 
                              text=config["text"],
                              command=config["command"],
                              state=config.get("state", "normal"))
            button.grid(row=0, column=i, 
                       padx=self.SPACING['standard_padx'], 
                       pady=self.SPACING['standard_pady'])
        
        return button_frame
    
    def show_status(self, message: str, level: str = "info"):
        """
        Show status message.
        
        Args:
            message: Status message
            level: Message level (info, warning, error)
        """
        # Try GUI callback first
        show_status_callback = self.services.get_gui_callback('show_status')
        if show_status_callback:
            show_status_callback(message, level)
        elif self.logger:
            # Fallback to logger
            getattr(self.logger, level)(message, "gui")
    
    def get_config(self, key: str, default=None):
        """Get configuration value from services."""
        return self.services.config_service.get(key, default)
    
    def set_config(self, key: str, value):
        """Set configuration value in services."""
        self.services.config_service.set(key, value)
    
    def append_output(self, text: str, widget=None):
        """
        Thread-safe method to append text to output widget.
        
        Args:
            text: Text to append
            widget: Specific widget to append to, defaults to self.output_text
        """
        def update():
            try:
                target_widget = widget or getattr(self, 'output_text', None)
                if target_widget and target_widget.winfo_exists():
                    target_widget.insert(tk.END, text + "\n")
                    target_widget.see(tk.END)
            except tk.TclError:
                # Widget was destroyed
                pass
            except Exception as e:
                print(f"Error updating output: {e}")
        
        # Schedule update on main thread
        try:
            if hasattr(self.services, 'root') and self.services.root:
                self.services.root.after(0, update)
            else:
                update()  # Fallback for direct execution
        except Exception as e:
            print(f"Error scheduling output update: {e}")
            
    def create_log_frame(self, parent_frame: ttk.Frame, row: int, column: int, columnspan: int, sticky: str):
        """
        Create a standardized log output Text widget with a scrollbar.
        
        Args:
            parent_frame: The frame to place the log widget in.
            row: Grid row for the log frame.
            column: Grid column for the log frame.
            columnspan: Grid columnspan for the log frame.
            sticky: Grid sticky option for the log frame.
            
        Returns:
            tk.Text: The created Text widget for logging.
        """
        log_frame_container = ttk.Frame(parent_frame)
        log_frame_container.grid(row=row, column=column, columnspan=columnspan, sticky=sticky,
                                 padx=self.SPACING['standard_padx'], pady=self.SPACING['standard_pady'])
        
        text_widget = tk.Text(log_frame_container, **self.WIDGET_SIZES['output_text'],
                              wrap=tk.WORD, font=self.FONTS['monospace'])
        scrollbar = ttk.Scrollbar(log_frame_container, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        log_frame_container.columnconfigure(0, weight=1)
        log_frame_container.rowconfigure(0, weight=1)
        
        return text_widget