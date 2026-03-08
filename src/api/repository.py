"""
Repository interface and implementations for Trilium API operations.
Provides abstraction layer between GUI and API implementation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
from collections import defaultdict

from .models import (
    TriliumNode, TriliumAttachment, NodePrefix, NodeCategory,
    ExportResult, FileExportResult, ConnectionInfo, SearchCriteria,
    NodeList, AttachmentList, PrefixDict, CategoryDict
)


class TriliumRepository(ABC):
    """Abstract repository interface for Trilium operations."""
    
    # Connection Management
    @abstractmethod
    def connect(self) -> ConnectionInfo:
        """Connect to Trilium server and return connection info."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from Trilium server."""
        pass
    
    @abstractmethod
    def test_connection(self) -> ConnectionInfo:
        """Test connection to Trilium server."""
        pass
    
    @abstractmethod
    def get_connection_info(self) -> ConnectionInfo:
        """Get current connection information."""
        pass
    
    # Node Discovery
    @abstractmethod
    def get_all_prefixes(self) -> PrefixDict:
        """Get all available node prefixes with counts."""
        pass
    
    @abstractmethod
    def get_nodes_by_prefix(self, prefix: str) -> NodeList:
        """Get all nodes with specified prefix."""
        pass
    
    @abstractmethod
    def get_nodes_by_criteria(self, criteria: SearchCriteria) -> NodeList:
        """Search nodes by multiple criteria."""
        pass
    
    @abstractmethod
    def get_node_by_id(self, node_id: str) -> Optional[TriliumNode]:
        """Get single node by ID."""
        pass
    
    @abstractmethod
    def get_child_nodes(self, parent_id: str) -> NodeList:
        """Get direct child nodes of a parent."""
        pass
    
    @abstractmethod
    def get_child_categories(self, parent_id: str) -> CategoryDict:
        """Get child nodes grouped as categories."""
        pass
    
    @abstractmethod
    def get_child_node_prefixes(self, parent_id: str) -> Dict[str, int]:
        """Get all unique prefixes used in child nodes of a parent node."""
        pass
    
    # Content Export
    @abstractmethod
    def export_node_content(self, node: TriliumNode, output_dir: Path) -> bool:
        """Export single node content to markdown."""
        pass
    
    @abstractmethod
    def export_subtree(self, root_node_id: str, output_dir: Path) -> ExportResult:
        """Export entire subtree starting from root node."""
        pass
    
    @abstractmethod
    def export_nodes_by_prefix(self, prefix: str, output_dir: Path) -> ExportResult:
        """Export all nodes with specified prefix."""
        pass
    
    @abstractmethod
    def export_nodes_by_criteria(self, criteria: SearchCriteria, output_dir: Path) -> ExportResult:
        """Export nodes matching search criteria."""
        pass
    
    # File/Attachment Operations
    @abstractmethod
    def get_node_attachments(self, node_id: str) -> AttachmentList:
        """Get all attachments for a node."""
        pass
    
    @abstractmethod
    def download_attachment(self, attachment: TriliumAttachment, output_path: Path) -> bool:
        """Download attachment to specified path."""
        pass
    
    @abstractmethod
    def export_files_by_prefix(self, prefix: str, base_output_dir: Path) -> FileExportResult:
        """Export all files from nodes with specified prefix."""
        pass
    
    @abstractmethod
    def export_node_files(self, node_id: str, output_dir: Path) -> FileExportResult:
        """Export all files from a specific node and its children."""
        pass
    
    # Utility Methods
    @abstractmethod
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities."""
        pass
    
    @abstractmethod
    def validate_node_access(self, node_id: str) -> bool:
        """Check if node exists and is accessible."""
        pass


class MockTriliumRepository(TriliumRepository):
    """Mock repository implementation for testing."""
    
    def __init__(self):
        self._connected = False
        self._connection_info = ConnectionInfo("mock://localhost", False)
        self._mock_nodes = {}
        self._mock_prefixes = {}  # Will be loaded from real API
        self._load_real_prefixes()
    
    def _load_real_prefixes(self):
        """Load only the 5 actual branch prefixes (not title word analysis)."""
        # Use the actual 5 prefixes that were working before
        self._mock_prefixes = {
            "Abschluss": NodePrefix("Conclusion", 1, "Conclusion slides"),
            "Anhänge": NodePrefix("Attachments", 2, "Attachments"),
            "Folie": NodePrefix("Slide", 69, "Presentation slides"),
            "Präsentation": NodePrefix("Presentation", 1, "Presentation content"),
            "Themenblatt": NodePrefix("Topic Sheet", 2, "Topic sheets")
        }
        print(f"✅ MockTriliumRepository loaded {len(self._mock_prefixes)} hardcoded branch prefixes")
    
    def connect(self) -> ConnectionInfo:
        """Mock connection."""
        self._connected = True
        self._connection_info = ConnectionInfo(
            "mock://localhost", 
            True, 
            "mock-1.0", 
            0.1
        )
        return self._connection_info
    
    def disconnect(self) -> None:
        """Mock disconnection."""
        self._connected = False
        self._connection_info.is_connected = False
    
    def test_connection(self) -> ConnectionInfo:
        """Mock connection test."""
        return self.connect()
    
    def get_connection_info(self) -> ConnectionInfo:
        """Get mock connection info."""
        return self._connection_info
    
    def get_all_prefixes(self) -> PrefixDict:
        """Return mock prefixes (loaded from real API)."""
        print(f"🔹 MOCK: Using MockTriliumRepository - returning {len(self._mock_prefixes)} prefixes")
        return self._mock_prefixes
    
    def get_nodes_by_prefix(self, prefix: str) -> NodeList:
        """Return mock nodes for prefix."""
        if prefix not in self._mock_prefixes:
            return []
        
        count = self._mock_prefixes[prefix].count
        return [
            TriliumNode(f"node_{i}", f"{prefix} {i}", f"Content for {prefix} {i}")
            for i in range(1, min(count + 1, 6))  # Return max 5 for demo
        ]
    
    def get_nodes_by_criteria(self, criteria: SearchCriteria) -> NodeList:
        """Mock search by criteria."""
        return []
    
    def get_node_by_id(self, node_id: str) -> Optional[TriliumNode]:
        """Mock get node by ID."""
        return TriliumNode(node_id, f"Mock Node {node_id}", "Mock content")
    
    def get_child_nodes(self, parent_id: str) -> NodeList:
        """Mock get child nodes."""
        return []
    
    def get_child_categories(self, parent_id: str) -> CategoryDict:
        """Mock get child categories."""
        return {}
    
    def get_child_node_prefixes(self, parent_id: str) -> Dict[str, int]:
        """Mock get child node prefixes."""
        # Return some mock prefixes for testing
        return {
            "Folie": 5,
            "Anhänge": 2,
            "Themenblatt": 1
        }
    
    def export_node_content(self, node: TriliumNode, output_dir: Path) -> bool:
        """Mock export node content."""
        return True
    
    def export_subtree(self, root_node_id: str, output_dir: Path) -> ExportResult:
        """Mock export subtree."""
        from .models import ExportStatus
        return ExportResult(ExportStatus.SUCCESS, exported_count=5)
    
    def export_nodes_by_prefix(self, prefix: str, output_dir: Path) -> ExportResult:
        """Mock export by prefix."""
        from .models import ExportStatus
        count = self._mock_prefixes.get(prefix, NodePrefix(prefix, 0)).count
        return ExportResult(ExportStatus.SUCCESS, exported_count=count)
    
    def export_nodes_by_criteria(self, criteria: SearchCriteria, output_dir: Path) -> ExportResult:
        """Mock export by criteria."""
        from .models import ExportStatus
        return ExportResult(ExportStatus.SUCCESS, exported_count=0)
    
    def get_node_attachments(self, node_id: str) -> AttachmentList:
        """Mock get attachments."""
        return []
    
    def download_attachment(self, attachment: TriliumAttachment, output_path: Path) -> bool:
        """Mock download attachment."""
        return True
    
    def export_files_by_prefix(self, prefix: str, base_output_dir: Path) -> FileExportResult:
        """Mock file export."""
        from .models import ExportStatus
        return FileExportResult(ExportStatus.SUCCESS)
    
    def export_node_files(self, node_id: str, output_dir: Path) -> FileExportResult:
        """Mock node file export."""
        from .models import ExportStatus
        return FileExportResult(ExportStatus.SUCCESS)
    
    def get_server_info(self) -> Dict[str, Any]:
        """Mock server info."""
        return {"version": "mock-1.0", "type": "mock"}
    
    def validate_node_access(self, node_id: str) -> bool:
        """Mock node validation."""
        return True