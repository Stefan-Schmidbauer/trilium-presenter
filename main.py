#!/usr/bin/env python3
"""
Trilium-Presenter - Main Entry Point
Launches the Trilium Presenter GUI application.
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the GUI
from gui.main_window import main

if __name__ == "__main__":
    main()
