"""
Modern styled MessageBox widgets for TriliumPresenter.
Provides better-looking alternatives to standard tkinter messageboxes.
"""

import tkinter as tk
from tkinter import ttk


class ModernMessageBox:
    """Modern styled message box with better typography."""

    # Use system colors for a more native look
    COLORS = {
        'bg': '#f0f0f0',  # Standard gray background (system default)
        'fg': '#000000',
        'icon_info': '#1976d2',
        'icon_success': '#388e3c',
        'icon_warning': '#f57c00',
        'icon_error': '#d32f2f'
    }

    @staticmethod
    def _create_dialog(parent, title, message, icon, icon_color, buttons=None):
        """Create a styled dialog window with better typography."""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.configure(bg=ModernMessageBox.COLORS['bg'])

        # Make dialog modal
        dialog.transient(parent)
        dialog.grab_set()

        # Center dialog on parent
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")

        # Main frame with system gray background
        main_frame = tk.Frame(dialog, bg=ModernMessageBox.COLORS['bg'],
                             padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Icon and message frame
        content_frame = tk.Frame(main_frame, bg=ModernMessageBox.COLORS['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Icon label (smaller, colored)
        icon_label = tk.Label(content_frame, text=icon,
                             font=("Segoe UI", 20),
                             bg=ModernMessageBox.COLORS['bg'],
                             fg=icon_color)
        icon_label.pack(side=tk.LEFT, padx=(0, 15))

        # Message label with better font (larger, clearer)
        msg_label = tk.Label(content_frame, text=message,
                           font=("Segoe UI", 10),
                           bg=ModernMessageBox.COLORS['bg'],
                           fg=ModernMessageBox.COLORS['fg'],
                           justify=tk.LEFT,
                           wraplength=350)
        msg_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button frame
        button_frame = tk.Frame(main_frame, bg=ModernMessageBox.COLORS['bg'])
        button_frame.pack(pady=(20, 0))

        # Result variable for dialog
        result = {'value': None}

        def on_button_click(value):
            result['value'] = value
            dialog.destroy()

        # Create buttons (using standard ttk buttons)
        if buttons is None:
            buttons = [('OK', True)]

        for i, (btn_text, btn_value) in enumerate(buttons):
            btn = ttk.Button(button_frame, text=btn_text, width=10,
                           command=lambda v=btn_value: on_button_click(v))
            btn.pack(side=tk.LEFT, padx=5)

            # Make first button default (activated by Enter key)
            if i == 0:
                btn.focus_set()
                dialog.bind('<Return>', lambda e, v=btn_value: on_button_click(v))

        # ESC key closes dialog
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        # Wait for dialog to close
        dialog.wait_window()

        return result['value']

    @staticmethod
    def showinfo(title, message, parent=None):
        """Show info message box."""
        if parent is None:
            parent = tk._default_root

        ModernMessageBox._create_dialog(
            parent, title, message,
            icon="ℹ️",
            icon_color=ModernMessageBox.COLORS['icon_info']
        )

    @staticmethod
    def showsuccess(title, message, parent=None):
        """Show success message box."""
        if parent is None:
            parent = tk._default_root

        ModernMessageBox._create_dialog(
            parent, title, message,
            icon="✅",
            icon_color=ModernMessageBox.COLORS['icon_success']
        )

    @staticmethod
    def showwarning(title, message, parent=None):
        """Show warning message box."""
        if parent is None:
            parent = tk._default_root

        ModernMessageBox._create_dialog(
            parent, title, message,
            icon="⚠️",
            icon_color=ModernMessageBox.COLORS['icon_warning']
        )

    @staticmethod
    def showerror(title, message, parent=None):
        """Show error message box."""
        if parent is None:
            parent = tk._default_root

        ModernMessageBox._create_dialog(
            parent, title, message,
            icon="❌",
            icon_color=ModernMessageBox.COLORS['icon_error']
        )

    @staticmethod
    def askyesno(title, message, parent=None):
        """Show yes/no question dialog."""
        if parent is None:
            parent = tk._default_root

        result = ModernMessageBox._create_dialog(
            parent, title, message,
            icon="❓",
            icon_color=ModernMessageBox.COLORS['icon_info'],
            buttons=[('Yes', True), ('No', False)]
        )

        return result if result is not None else False

    @staticmethod
    def askokcancel(title, message, parent=None):
        """Show OK/Cancel question dialog."""
        if parent is None:
            parent = tk._default_root

        result = ModernMessageBox._create_dialog(
            parent, title, message,
            icon="❓",
            icon_color=ModernMessageBox.COLORS['icon_info'],
            buttons=[('OK', True), ('Cancel', False)]
        )

        return result if result is not None else False
