"""
Concrete implementation of TriliumRepository using TriliumAPIExporter.
Bridges the repository interface with the actual Trilium API.
"""

import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from .repository import TriliumRepository
from .models import (
    TriliumNode, TriliumAttachment, NodePrefix, NodeCategory,
    ExportResult, FileExportResult, ConnectionInfo, SearchCriteria,
    NodeList, AttachmentList, PrefixDict, CategoryDict, ExportStatus
)

# Import error handling and logging
try:
    from gui.error_handling import handle_api_errors, safe_operation
    from gui.logging_utils import get_api_logger
except ImportError:
    # Fallback - create dummy decorators if imports fail
    def handle_api_errors(operation, message="Operation failed"):
        def decorator(func):
            return func
        return decorator
    
    def safe_operation(func):
        return func
        
    class DummyLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def debug(self, msg): print(f"DEBUG: {msg}")
    
    def get_api_logger():
        return DummyLogger()

# Import the actual API components directly
try:
    # Try relative imports first
    try:
        from ..trilium_connection import TriliumConnection
        from ..trilium_node_discovery import TriliumNodeDiscovery
        from ..trilium_content_exporter import TriliumContentExporter
        from ..trilium_file_exporter import TriliumFileExporter
    except ImportError:
        # Fall back to absolute imports
        import sys
        import os
        src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from trilium_connection import TriliumConnection
        from trilium_node_discovery import TriliumNodeDiscovery
        from trilium_content_exporter import TriliumContentExporter
        from trilium_file_exporter import TriliumFileExporter
    
    _api_available = True
except ImportError as e:
    print(f"Failed to import Trilium API components: {e}")
    import traceback
    traceback.print_exc()
    _api_available = False
    TriliumConnection = None
    TriliumNodeDiscovery = None
    TriliumContentExporter = None
    TriliumFileExporter = None


class TriliumAPIRepository(TriliumRepository):
    """Repository implementation using TriliumAPIExporter."""
    
    def __init__(self, server_url: str, token: str):
        """
        Initialize repository with API connection details.
        
        Args:
            server_url: Trilium server URL
            token: ETAPI authentication token
        """
        self.server_url = server_url
        self.token = token
        self._connection_info = ConnectionInfo(server_url, False)
        self._logger = get_api_logger()
        
        if not _api_available:
            raise ImportError("Trilium API components not available. Install trilium-py dependency.")
        
        # Initialize modular components directly
        self._connection = TriliumConnection(server_url, token)
        self._node_discovery = TriliumNodeDiscovery(self._connection)
        self._content_exporter = TriliumContentExporter(self._connection, self._node_discovery)
        self._file_exporter = TriliumFileExporter(self._connection, self._node_discovery)
    
    @property
    def connection(self) -> Optional['TriliumConnection']:
        """Get the connection component."""
        return self._connection
    
    @handle_api_errors("Connect to Trilium", "Verbindung zu Trilium fehlgeschlagen")
    def connect(self) -> ConnectionInfo:
        """Connect to Trilium server and return connection info."""
        start_time = time.time()
        
        self._logger.operation_start("Connecting to Trilium")
        self._connection.connect()
        
        # Get server info
        api = self._connection.get_api()
        server_info = api.app_info() if hasattr(api, 'app_info') else {}
        server_version = server_info.get('appVersion', 'unknown')
        
        connection_time = time.time() - start_time
        self._connection_info = ConnectionInfo(
            self.server_url,
            True,
            server_version,
            connection_time
        )
        
        self._logger.success(f"Connected to Trilium {server_version} in {connection_time:.2f}s")
        return self._connection_info
    
    def disconnect(self) -> None:
        """Disconnect from Trilium server."""
        if self._connection:
            try:
                self._connection.close()
                self._logger.info("Disconnected from Trilium")
            except Exception as e:
                self._logger.warning(f"Error during disconnect: {e}")
            finally:
                self._connection_info.is_connected = False
    
    @handle_api_errors("Test connection", "Verbindungstest fehlgeschlagen")
    def test_connection(self, quick_test: bool = True) -> ConnectionInfo:
        """
        Test connection to Trilium server.

        Args:
            quick_test: If True, only test basic connectivity (fast).
                       If False, also test prefix loading (slow, 10-20s).
        """
        try:
            # Test with new connection
            connection_info = self.connect()

            # Optional: Test a more complex API call
            # This is SLOW (10-20s) so skip by default for faster GUI startup
            if not quick_test and self._connection:
                self._logger.info("Running full connection test (loading prefixes)...")
                self._node_discovery.get_available_prefixes()

            return connection_info
        except Exception as e:
            # If connection fails, reset connection info
            self._connection_info.is_connected = False
            raise
    
    def get_connection_info(self) -> ConnectionInfo:
        """Get current connection information."""
        return self._connection_info
    
    @handle_api_errors("Get prefixes", "Prefixe konnten nicht geladen werden")
    def get_all_prefixes(self) -> PrefixDict:
        """Get all available node prefixes with counts."""
        if not self._connection:
            return {}
        
        self._logger.operation_start("🔍 REAL API: Loading prefixes")
        raw_prefixes = self._node_discovery.get_available_prefixes()
        
        prefixes = {}
        for prefix_name, count in raw_prefixes.items():
            prefixes[prefix_name] = NodePrefix(prefix_name, count)
        
        self._logger.success(f"Loaded {len(prefixes)} prefixes")
        return prefixes
    
    @handle_api_errors("Get nodes by prefix", "Nodes konnten nicht geladen werden")
    def get_nodes_by_prefix(self, prefix: str) -> NodeList:
        """Get all nodes with specified prefix."""
        if not self._connection:
            return []
        
        self._logger.operation_start(f"Loading nodes with prefix '{prefix}'")
        raw_nodes = self._node_discovery.get_nodes_by_prefix(prefix)
        
        nodes = []
        for node_id, title in raw_nodes.items():
            node = TriliumNode(
                node_id=node_id,
                title=title,
                prefix=prefix
            )
            nodes.append(node)
        
        self._logger.success(f"Loaded {len(nodes)} nodes with prefix '{prefix}'")
        return nodes
    
    @handle_api_errors("Search nodes", "Suche fehlgeschlagen")
    def get_nodes_by_criteria(self, criteria: SearchCriteria) -> NodeList:
        """Search nodes by multiple criteria."""
        if not self._connection:
            return []
        
        self._logger.operation_start("Searching nodes by criteria")
        
        # For now, implement prefix-based search
        # Can be extended for more complex criteria
        nodes = []
        for prefix in criteria.prefixes:
            prefix_nodes = self.get_nodes_by_prefix(prefix)
            nodes.extend(prefix_nodes)
        
        self._logger.success(f"Found {len(nodes)} nodes matching criteria")
        return nodes
    
    @handle_api_errors("Get node by ID", "Node konnte nicht geladen werden")
    def get_node_by_id(self, node_id: str) -> Optional[TriliumNode]:
        """Get single node by ID."""
        if not self._connection:
            return None
        
        # Use the connection's API directly
        api = self._connection.get_api()
        node_info = api.get_note(node_id)
        if not node_info:
            return None
        
        return TriliumNode(
            node_id=node_id,
            title=node_info.get('title', 'Unknown'),
            content=node_info.get('content', ''),
            created_date=node_info.get('dateCreated'),
            modified_date=node_info.get('dateModified')
        )
    
    @handle_api_errors("Get child nodes", "Child-Nodes konnten nicht geladen werden")
    def get_child_nodes(self, parent_id: str) -> NodeList:
        """Get direct child nodes of a parent (no recursion)."""
        if not self._connection:
            return []

        # Use new direct child method instead of recursive
        child_ids = self._node_discovery.get_direct_child_nodes(parent_id)
        nodes = []
        for child_id in child_ids:
            try:
                api = self._connection.get_api()
                note = api.get_note(child_id)
                if note:
                    node = TriliumNode(
                        node_id=child_id,
                        title=note.get('title', 'Unknown')
                    )
                    nodes.append(node)
            except Exception:
                continue
        return nodes
    
    @handle_api_errors("Get recursive child nodes", "Rekursive Child-Nodes konnten nicht geladen werden")
    def get_recursive_child_nodes(self, parent_id: str) -> NodeList:
        """Get all child nodes recursively."""
        if not self._connection:
            return []
        
        child_ids = self._node_discovery.get_child_notes_recursive(parent_id)
        nodes = []
        for child_id in child_ids:
            try:
                api = self._connection.get_api()
                note = api.get_note(child_id)
                if note:
                    node = TriliumNode(
                        node_id=child_id,
                        title=note.get('title', 'Unknown')
                    )
                    nodes.append(node)
            except Exception:
                continue
        return nodes
    
    @handle_api_errors("Get child categories", "Kategorien konnten nicht geladen werden")
    def get_child_categories(self, parent_id: str) -> CategoryDict:
        """Get child nodes grouped as categories."""
        if not self._connection:
            return {}
        
        self._logger.operation_start(f"Loading categories for node {parent_id}")
        # Categories are just child nodes grouped by type
        child_nodes = self.get_child_nodes(parent_id)
        raw_categories = [(node.node_id, node.title) for node in child_nodes]
        
        categories = {}
        for node_id, title in raw_categories:
            category = NodeCategory(
                node_id=node_id,
                title=title,
                parent_id=parent_id
            )
            categories[title] = category
        
        self._logger.success(f"Loaded {len(categories)} categories")
        return categories
    
    @handle_api_errors("Get child node prefixes", "Child-Node-Prefixe konnten nicht geladen werden")
    def get_child_node_prefixes(self, parent_id: str) -> Dict[str, int]:
        """Get all unique prefixes used in child nodes of a parent node."""
        if not self._connection:
            return {}
        
        self._logger.operation_start(f"Loading child node prefixes for parent {parent_id}")
        
        try:
            prefixes = self._node_discovery.get_child_node_prefixes(parent_id)
            self._logger.success(f"Loaded {len(prefixes)} unique child node prefixes: {list(prefixes.keys())}")
            return prefixes
        except Exception as e:
            self._logger.error(f"Failed to get child node prefixes for {parent_id}: {e}")
            return {}
    
    @handle_api_errors("Export node content", "Node-Export fehlgeschlagen")
    def export_node_content(self, node: TriliumNode, output_dir: Path) -> bool:
        """Export single node content to markdown."""
        if not self._connection:
            return False
        
        # Use content exporter component
        try:
            success = self._content_exporter.export_node_content(node.node_id, str(output_dir))
            self._logger.info(f"Exporting node {node.node_id} to {output_dir}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to export node {node.node_id}: {e}")
            return False
    
    @handle_api_errors("Export subtree", "Subtree-Export fehlgeschlagen")
    def export_subtree(self, root_node_id: str, output_dir: Path) -> ExportResult:
        """Export entire subtree starting from root node."""
        if not self._connection:
            return ExportResult(ExportStatus.FAILED, error_message="No API connection")
        
        self._logger.operation_start(f"Exporting subtree from node {root_node_id}")
        
        try:
            # Get node info first to find prefix
            api = self._connection.get_api()
            note = api.get_note(root_node_id)
            if not note:
                raise Exception("Node not found")
            
            # Use content exporter for subtree export
            title = note.get('title', '')
            # Extract potential prefix from title
            prefix = title.split()[0] if title else 'export'
            success = self._content_exporter.export_by_subtree_discovery(prefix, str(output_dir))
            
            if success:
                self._logger.success("Subtree export completed")
                return ExportResult(
                    ExportStatus.SUCCESS,
                    exported_count=1,  # Would need actual count from API
                    output_directory=output_dir
                )
            else:
                return ExportResult(
                    ExportStatus.FAILED,
                    error_message="Export failed"
                )
        except Exception as e:
            return ExportResult(
                ExportStatus.FAILED,
                error_message=str(e)
            )
    
    @handle_api_errors("Export by prefix", "Prefix-Export fehlgeschlagen")
    def export_nodes_by_prefix(self, prefix: str, output_dir: Path) -> ExportResult:
        """Export all nodes with specified prefix."""
        if not self._connection:
            return ExportResult(ExportStatus.FAILED, error_message="No API connection")
        
        self._logger.operation_start(f"Exporting nodes with prefix '{prefix}'")
        
        try:
            # Use the content exporter for prefix-based export
            success = self._content_exporter.export_by_subtree_discovery(prefix, str(output_dir))
            
            if success:
                self._logger.success(f"Export completed for prefix '{prefix}'")
                return ExportResult(
                    ExportStatus.SUCCESS,
                    exported_count=1,  # Would need actual count
                    output_directory=output_dir
                )
            else:
                return ExportResult(
                    ExportStatus.FAILED,
                    error_message="Export failed"
                )
        except Exception as e:
            return ExportResult(
                ExportStatus.FAILED,
                error_message=str(e)
            )
    
    def export_nodes_by_criteria(self, criteria: SearchCriteria, output_dir: Path) -> ExportResult:
        """Export nodes matching search criteria."""
        # For now, implement prefix-based export
        if criteria.prefixes:
            return self.export_nodes_by_prefix(criteria.prefixes[0], output_dir)
        
        return ExportResult(
            ExportStatus.FAILED,
            error_message="No export criteria specified"
        )
    
    @handle_api_errors("Get attachments", "Attachments konnten nicht geladen werden")
    def get_node_attachments(self, node_id: str) -> AttachmentList:
        """Get all attachments for a node."""
        if not self._connection:
            return []
        
        # Use file exporter for attachment handling
        try:
            # This would need implementation in file exporter
            self._logger.warning("get_node_attachments not yet fully implemented")
            return []
        except Exception as e:
            self._logger.error(f"Failed to get attachments for node {node_id}: {e}")
            return []
    
    def download_attachment(self, attachment: TriliumAttachment, output_path: Path) -> bool:
        """Download attachment to specified path."""
        if not self._connection:
            return False
        
        # Use file exporter for attachment download
        try:
            # This would need implementation in file exporter
            self._logger.warning("download_attachment not yet fully implemented")
            return False
        except Exception as e:
            self._logger.error(f"Failed to download attachment {attachment.file_name}: {e}")
            return False
    
    @handle_api_errors("Export files by prefix", "Datei-Export fehlgeschlagen")
    def export_files_by_prefix(self, prefix: str, base_output_dir: Path) -> FileExportResult:
        """Export all files from nodes with specified prefix."""
        if not self._connection:
            return FileExportResult(ExportStatus.FAILED, error_message="No API connection")
        
        self._logger.operation_start(f"Exporting files with prefix '{prefix}'")
        
        try:
            success = self._file_exporter.export_files_by_prefix_to_folders(prefix, str(base_output_dir))
            
            if success:
                self._logger.success(f"File export completed for prefix '{prefix}'")
                return FileExportResult(ExportStatus.SUCCESS)
            else:
                return FileExportResult(
                    ExportStatus.FAILED,
                    error_message="File export failed"
                )
        except Exception as e:
            return FileExportResult(
                ExportStatus.FAILED,
                error_message=str(e)
            )
    
    def export_node_files(self, node_id: str, output_dir: Path) -> FileExportResult:
        """Export all files from a specific node and its children."""
        if not self._connection:
            return FileExportResult(ExportStatus.FAILED, error_message="No API connection")
        
        # Use file exporter for node-specific file export
        try:
            # This would need implementation in file exporter
            self._logger.warning("export_node_files not yet fully implemented")
            return FileExportResult(ExportStatus.FAILED, error_message="Not implemented")
        except Exception as e:
            return FileExportResult(
                ExportStatus.FAILED,
                error_message=str(e)
            )
    
    @handle_api_errors("Get server info", "Server-Infos konnten nicht geladen werden")
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities."""
        if not self._connection:
            return {}
        
        try:
            api = self._connection.get_api()
            return api.app_info() if hasattr(api, 'app_info') else {"status": "connected"}
        except Exception as e:
            self._logger.error(f"Failed to get server info: {e}")
            return {"status": "connected", "client": "TriliumAPIRepository"}
    
    @handle_api_errors("Validate node access", "Node-Validierung fehlgeschlagen")
    def validate_node_access(self, node_id: str) -> bool:
        """Check if node exists and is accessible."""
        if not self._connection:
            return False
        
        try:
            api = self._connection.get_api()
            note = api.get_note(node_id)
            return note is not None
        except Exception:
            return False