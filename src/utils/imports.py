"""
Unified import system for TriliumPresenter modules.
Eliminates duplicate try/except imports across all modules.
"""

import importlib
from typing import Any, Optional


def import_module(relative_module: str, package: str, fallback_module: str) -> Any:
    """
    Unified import function that handles relative/absolute imports.
    
    Args:
        relative_module: Relative module name (e.g. '.constants')
        package: Current package name (__name__)
        fallback_module: Fallback module name without dots (e.g. 'constants')
    
    Returns:
        Imported module
    """
    try:
        return importlib.import_module(relative_module, package)
    except ImportError:
        return importlib.import_module(fallback_module)


def get_standard_imports(package_name: str) -> tuple:
    """
    Get standard imports for trilium modules.
    
    Args:
        package_name: Current package (__name__)
        
    Returns:
        Tuple of (constants, logging_manager, TriliumConnection)
    """
    constants = import_module('.constants', package_name, 'constants')
    logging_manager = import_module('.logging_manager', package_name, 'logging_manager') 
    
    # TriliumConnection import
    trilium_connection_module = import_module('.trilium_connection', package_name, 'trilium_connection')
    TriliumConnection = trilium_connection_module.TriliumConnection
    
    return constants, logging_manager, TriliumConnection