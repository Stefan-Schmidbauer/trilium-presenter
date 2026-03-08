"""
Trilium API Exporter - Facade for modular export components.
Used internally by the GUI via TriliumAPIRepository.
"""

from typing import Any, List, Optional

# Import modular components
try:
    from .trilium_connection import TriliumConnection
    from .trilium_node_discovery import TriliumNodeDiscovery
    from .trilium_content_exporter import TriliumContentExporter
    from .trilium_file_exporter import TriliumFileExporter
except ImportError:
    from trilium_connection import TriliumConnection
    from trilium_node_discovery import TriliumNodeDiscovery
    from trilium_content_exporter import TriliumContentExporter
    from trilium_file_exporter import TriliumFileExporter

# Import unified logging system
try:
    from . import logging_manager
except ImportError:
    import logging_manager


class TriliumAPIExporter:
    """
    Trilium API-based exporter for TriliumPresenter - Simplified Facade.
    Provides unified export interface with direct component access.
    """
    
    def __init__(self, server_url: str, token: str):
        self.server_url = server_url
        self.token = token
        self.logger = logging_manager.get_logger()
        
        # Initialize modular components - direct access encouraged
        self.connection = TriliumConnection(server_url, token)
        self.discovery = TriliumNodeDiscovery(self.connection)
        self.content = TriliumContentExporter(self.connection, self.discovery)
        self.files = TriliumFileExporter(self.connection, self.discovery)
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def connect(self):
        """Connects to the Trilium API."""
        self.connection.connect()
    
    def close(self):
        """Closes the API connection."""
        self.connection.close()
    
    # Unified Export Interface - Strategy Pattern
    
    def export(self, strategy: str, target: Any, output_dir: str, 
              remove_prefixes: Optional[List[str]] = None, include_root_node: bool = True) -> bool:
        """
        Unified export method using strategy pattern.
        
        Args:
            strategy: Export strategy ('prefix', 'subtree', 'tags', 'files')
            target: Target for export (string for prefix, list for tags, etc.)
            output_dir: Output directory
            remove_prefixes: Prefixes to remove from titles
            include_root_node: Whether to include root node content in export
            
        Returns:
            Success status
        """
        if strategy == 'prefix':
            return self.content.export_by_subtree_discovery(target, output_dir, remove_prefixes, include_root_node)
        elif strategy == 'subtree':
            return self.content.export_by_subtree_discovery(target, output_dir, remove_prefixes, include_root_node)
        elif strategy == 'tags':
            return self.content.export_by_tags(target, output_dir, remove_prefixes)
        elif strategy == 'files':
            return self.files.export_files_by_prefix_to_folders(target, output_dir)
        else:
            self.logger.error(f"Unknown export strategy: {strategy}", "export")
            return False
    
    def test_connection(self) -> bool:
        """Tests the API connection."""
        return self.connection.test_connection()