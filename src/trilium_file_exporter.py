"""
Trilium File Exporter for TriliumPresenter.
Handles file and attachment export operations.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import utilities
try:
    from .utils import make_safe_filename, make_safe_dirname
    from .utils.file_utils import clear_directory
except ImportError:
    from utils import make_safe_filename, make_safe_dirname
    from utils.file_utils import clear_directory

# Import unified logging system
try:
    from . import logging_manager
except ImportError:
    import logging_manager

try:
    from .trilium_connection import TriliumConnection
    from .trilium_node_discovery import TriliumNodeDiscovery
except ImportError:
    from trilium_connection import TriliumConnection
    from trilium_node_discovery import TriliumNodeDiscovery


class TriliumFileExporter:
    """Handles file and attachment export from Trilium."""
    
    def __init__(self, connection: TriliumConnection, node_discovery: TriliumNodeDiscovery):
        self.connection = connection
        self.node_discovery = node_discovery
        self.logger = logging_manager.get_logger()
    
    def extract_attachments_from_nodes(self, node_ids: List[str], output_dir: str) -> bool:
        """Extracts attachments from the specified nodes via API."""
        if not node_ids:
            return True
            
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Delete old attachments
        for item in output_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        
        api = self.connection.get_api()
        extracted_count = [0]
        
        for node_id in node_ids:
            try:
                # Get the note details
                note = api.get_note(node_id)
                if not note:
                    continue
                
                note_type = note.get('type', '')
                
                # For file nodes: Export the file itself
                if note_type in ['file', 'image']:
                    self._extract_single_file(api, node_id, note, output_path, extracted_count)
                
                # Additionally: Search for file attachments in text notes
                # (These might be organized as child notes)
                try:
                    parent_note = api.get_note(node_id)
                    child_ids = parent_note.get('childNoteIds', []) if parent_note else []
                    
                    if child_ids:
                        for child_id in child_ids:
                            try:
                                child_note = api.get_note(child_id)
                                if child_note and child_note.get('type') in ['file', 'image']:
                                    self._extract_single_file(api, child_id, child_note, output_path, extracted_count)
                            except Exception as e:
                                pass
                                continue
                except Exception as e:
                    pass
                
            except Exception as e:
                self.logger.error(f"Error processing node {node_id}: {e}", "export")
                continue
        
        self.logger.info(f"Attachment extraction completed: {extracted_count[0]} files extracted to {output_dir}", "export")
        return extracted_count[0] > 0
    
    def export_files_by_prefix_to_folders(self, prefix: str, base_output_dir: str = ".") -> bool:
        """
        Exports files from nodes with a specific prefix into folders.
        Creates a folder for each node based on its title.
        """
        self.logger.info(f"Starting file export by prefix '{prefix}' to folders", "export")
        
        # Find all nodes with this prefix
        matching_nodes = self.node_discovery.get_nodes_by_prefix(prefix)
        
        if not matching_nodes:
            self.logger.warning(f"No nodes found with prefix '{prefix}'", "export")
            return False
        
        base_path = Path(base_output_dir)
        exported_folders = 0
        
        for node_id, node_title in matching_nodes.items():
            try:
                # Create safe folder name from node title
                safe_dirname = make_safe_dirname(node_title)
                
                # Remove prefix from folder name if present
                if safe_dirname.startswith(prefix):
                    safe_dirname = safe_dirname[len(prefix):].lstrip('_-: ')
                    if not safe_dirname:  # If empty after prefix removal
                        safe_dirname = f"files_from_{prefix}"
                
                folder_path = base_path / safe_dirname
                
                # Export all files from this node and its children
                all_node_ids = [node_id]
                child_ids = self.node_discovery.get_child_notes_recursive(node_id)
                all_node_ids.extend(child_ids)
                
                if self.extract_attachments_from_nodes(all_node_ids, str(folder_path)):
                    exported_folders += 1
                    self.logger.info(f"Created folder: {safe_dirname}", "export")
                else:
                    # Remove empty folder
                    if folder_path.exists() and not any(folder_path.iterdir()):
                        folder_path.rmdir()
                        
            except Exception as e:
                self.logger.error(f"Error exporting files for node {node_id} ('{node_title}'): {e}", "export")
                continue
        
        self.logger.info(f"File export by prefix completed: {exported_folders} folders created in {base_output_dir}", "export")
        return exported_folders > 0
    
    def _extract_single_file(self, api, node_id: str, note: Dict[str, Any], output_path: Path, extracted_count: list) -> None:
        """Extract a single file from a node, handling binary files properly."""
        filename = note.get('title', f'file_{node_id}')
        safe_filename = make_safe_filename(filename)
        file_path = output_path / safe_filename
        note_type = note.get('type', '')
        
        try:
            # For images, try attachment API first
            file_content = None
            if note_type == 'image':
                try:
                    attachments = api.get_attachments(node_id)
                    if attachments:
                        for attachment in attachments:
                            att_content = api.get_attachment_content(attachment['attachmentId'])
                            if att_content:
                                file_content = att_content
                                break
                except Exception:
                    pass
            
            # Fallback to note content - try different approaches for binary files
            if file_content is None:
                try:
                    file_content = api.get_note_content(node_id)
                except (UnicodeDecodeError, Exception):
                    # trilium-py may fail to decode binary content as text
                    # Use direct HTTP request via TriliumConnection for reliable binary access
                    try:
                        import requests
                        headers = {"Authorization": self.connection.token}
                        response = requests.get(
                            f"{self.connection.server_url}/etapi/notes/{node_id}/content",
                            headers=headers
                        )
                        if response.status_code == 200:
                            file_content = response.content
                    except Exception as e:
                        self.logger.error(f"Binary fallback failed for {node_id}: {e}", "export")
            
            if file_content:
                # Always write as binary for files/images
                with open(file_path, 'wb') as f:
                    if isinstance(file_content, bytes):
                        f.write(file_content)
                    elif isinstance(file_content, str):
                        # Try different encodings for string content
                        try:
                            f.write(file_content.encode('latin1'))
                        except:
                            try:
                                f.write(file_content.encode('utf-8'))
                            except:
                                f.write(file_content.encode('utf-8', errors='ignore'))
                    else:
                        f.write(bytes(file_content))
                
                if isinstance(extracted_count, list):
                    extracted_count[0] += 1
                else:
                    extracted_count += 1
                # Only log the first and last few files to reduce spam
                if extracted_count[0] <= 3 or extracted_count[0] % 50 == 0:
                    pass
                
        except Exception as e:
            self.logger.error(f"Error extracting file from node {node_id}: {e}", "export")