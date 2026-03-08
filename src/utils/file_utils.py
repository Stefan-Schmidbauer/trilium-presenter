"""
File and path utilities for TriliumPresenter.
Handles safe filename generation and path operations.
"""

import re
import shutil
from pathlib import Path


def make_safe_filename(filename: str) -> str:
    """
    Creates a safe filename.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename without problematic characters
    """
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = safe_name.replace(' ', '_')
    return safe_name


def make_safe_dirname(dirname: str) -> str:
    """
    Creates a safe directory name from node title.
    
    Args:
        dirname: Original directory name
        
    Returns:
        Safe directory name without problematic characters
    """
    # Remove dangerous characters for directory names
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', dirname)
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    # If empty, use fallback
    if not safe_name:
        safe_name = "unnamed_node"
    return safe_name


def clear_directory(directory_path: Path) -> bool:
    """
    Completely clears the contents of a directory.
    
    Args:
        directory_path: Path to the directory to be cleared
        
    Returns:
        True if successful, False on error
    """
    try:
        if directory_path.exists() and directory_path.is_dir():
            # Delete all contents of the directory
            shutil.rmtree(directory_path)
            # Recreate the directory as empty
            directory_path.mkdir(parents=True, exist_ok=True)
            return True
        return True  # Directory does not exist, so it is already "empty"
    except Exception:
        return False