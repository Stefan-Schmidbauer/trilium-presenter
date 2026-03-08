"""
Data models for API responses and entities.
Provides clean data structures independent of API implementation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum


class ExportStatus(Enum):
    """Export operation status."""
    PENDING = "pending"
    RUNNING = "running" 
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class TriliumNode:
    """Represents a Trilium note/node."""
    node_id: str
    title: str
    content: str = ""
    parent_id: Optional[str] = None
    prefix: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    relations: Dict[str, str] = field(default_factory=dict)
    is_deleted: bool = False
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    
    @property
    def display_title(self) -> str:
        """Get display title with prefix if available."""
        if self.prefix:
            return f"{self.prefix}: {self.title}"
        return self.title


@dataclass
class TriliumAttachment:
    """Represents a file attachment in Trilium."""
    attachment_id: str
    title: str
    role: str
    mime_type: str
    file_size: int
    note_id: str
    content_length: Optional[int] = None
    
    @property
    def file_extension(self) -> str:
        """Get file extension from title."""
        return Path(self.title).suffix.lower()
    
    @property
    def is_image(self) -> bool:
        """Check if attachment is an image."""
        return self.mime_type.startswith('image/')
    
    @property
    def is_document(self) -> bool:
        """Check if attachment is a document."""
        doc_types = ['application/pdf', 'application/msword', 'text/plain']
        return any(self.mime_type.startswith(dtype) for dtype in doc_types)


@dataclass
class NodePrefix:
    """Represents a node prefix with count."""
    prefix: str
    count: int
    description: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.prefix} ({self.count} nodes)"


@dataclass
class NodeCategory:
    """Represents a node category (child nodes of a parent)."""
    node_id: str
    title: str
    parent_id: str
    child_count: int = 0
    
    def __str__(self) -> str:
        suffix = f" ({self.child_count} children)" if self.child_count > 0 else ""
        return f"{self.title}{suffix}"


@dataclass
class ExportResult:
    """Result of an export operation."""
    status: ExportStatus
    exported_count: int = 0
    failed_count: int = 0
    output_directory: Optional[Path] = None
    exported_files: List[Path] = field(default_factory=list)
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Check if export was successful."""
        return self.status == ExportStatus.SUCCESS
    
    @property
    def total_processed(self) -> int:
        """Total number of items processed."""
        return self.exported_count + self.failed_count


@dataclass
class FileExportResult:
    """Result of a file export operation."""
    status: ExportStatus
    exported_files: List[Path] = field(default_factory=list)
    output_directories: List[Path] = field(default_factory=list)
    total_size: int = 0
    error_message: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if file export was successful."""
        return self.status == ExportStatus.SUCCESS
    
    @property
    def file_count(self) -> int:
        """Number of files exported."""
        return len(self.exported_files)


@dataclass
class ConnectionInfo:
    """Information about API connection."""
    server_url: str
    is_connected: bool = False
    server_version: Optional[str] = None
    connection_test_time: Optional[float] = None
    last_error: Optional[str] = None
    
    @property
    def status_message(self) -> str:
        """Get human-readable status message."""
        if self.is_connected:
            version = f" (v{self.server_version})" if self.server_version else ""
            return f"Connected to {self.server_url}{version}"
        elif self.last_error:
            return f"Failed to connect: {self.last_error}"
        else:
            return f"Not connected to {self.server_url}"


@dataclass
class SearchCriteria:
    """Criteria for searching nodes."""
    prefixes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    include_deleted: bool = False
    parent_node_id: Optional[str] = None
    content_contains: Optional[str] = None
    title_pattern: Optional[str] = None
    
    def has_criteria(self) -> bool:
        """Check if any search criteria are specified."""
        return bool(
            self.prefixes or 
            self.tags or 
            self.parent_node_id or 
            self.content_contains or 
            self.title_pattern
        )


# Type aliases for common collections
NodeList = List[TriliumNode]
AttachmentList = List[TriliumAttachment]
PrefixDict = Dict[str, NodePrefix]
CategoryDict = Dict[str, NodeCategory]