#!/usr/bin/env python3
"""
TriliumPresenter - New Modular GUI Entry Point
Uses the refactored modular GUI architecture.
"""

import sys
from pathlib import Path

# Add current directory (src) to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the modular GUI
try:
    import tkinter as tk
    from gui.main_window import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Error importing GUI components: {e}")
    print("Make sure all required modules are installed.")
    sys.exit(1)
except Exception as e:
    print(f"Error starting TriliumPresenter: {e}")
    sys.exit(1)