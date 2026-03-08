"""
Trilium Content Exporter for TriliumPresenter.
Handles markdown export and content processing.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import utilities
try:
    from .utils import html_to_markdown, process_title_with_prefix, make_safe_filename
    from .utils.file_utils import clear_directory
except ImportError:
    from utils import html_to_markdown, process_title_with_prefix, make_safe_filename
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


class TriliumContentExporter:
    """Handles content export from Trilium to markdown files."""
    
    def __init__(self, connection: TriliumConnection, node_discovery: TriliumNodeDiscovery):
        self.connection = connection
        self.node_discovery = node_discovery
        self.logger = logging_manager.get_logger()
    
    def export_by_subtree_discovery(self, prefix: str, output_dir: str, 
                                  remove_prefixes: Optional[List[str]] = None, include_root_node: bool = True) -> bool:
        """Exports nodes via Subtree-Discovery Workflow (Prefix -> Selection -> Hierarchy)."""
        if remove_prefixes is None:
            remove_prefixes = [prefix]
        
        self.logger.info(f"Starting subtree discovery export with prefix '{prefix}'", "export")
        
        # 1. Find all nodes with this prefix
        matching_nodes = self.node_discovery.get_nodes_by_prefix(prefix)
        
        if not matching_nodes:
            self.logger.warning(f"No nodes found with prefix '{prefix}'", "export")
            return False
        
        self.logger.info(f"Found {len(matching_nodes)} nodes with prefix '{prefix}'", "export")
        
        # 2. For each found node: export it and all children
        output_path = Path(output_dir)
        
        # Clear existing directory if it exists
        if output_path.exists():
            self.logger.info(f"Clearing existing directory: {output_path}", "export")
            if clear_directory(output_path):
                self.logger.info("Existing directory cleared successfully", "export")
            else:
                self.logger.warning("Could not fully clear existing directory", "export")
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_count = 0
        
        for node_id, node_title in matching_nodes.items():
            try:
                # Export the main node only if include_root_node is True
                if include_root_node:
                    # Check node type - skip file and image nodes for root as well
                    root_note = self.connection.get_api().get_note(node_id)
                    if root_note and root_note.get('type', '') not in ['file', 'image']:
                        if self._export_single_note(node_id, node_title, prefix, remove_prefixes, output_path):
                            exported_count += 1
                
                # Export all child nodes recursively (always, even if root is excluded)
                child_node_ids = self.node_discovery.get_child_notes_recursive(node_id)
                
                for child_id in child_node_ids:
                    child_note = self.connection.get_api().get_note(child_id)
                    if child_note:
                        child_title = child_note.get('title', '')
                        child_type = child_note.get('type', '')
                        # Skip file and image nodes - these should only be handled by file exporter
                        if child_type in ['file', 'image']:
                            self.logger.debug(f"⏭️ Skipping file/image node: '{child_title}' (type: {child_type})", "export")
                        elif self._export_single_note(child_id, child_title, prefix, remove_prefixes, output_path):
                            exported_count += 1
                            
            except Exception as e:
                self.logger.error(f"Error exporting subtree for node {node_id} ('{node_title}'): {e}", "export")
                continue
        
        self.logger.info(f"Subtree export completed: {exported_count} files exported to {output_dir}", "export")
        return exported_count > 0
    
    def export_by_tags(self, tags: List[str], output_dir: str, 
                      remove_prefixes: Optional[List[str]] = None) -> bool:
        """Exports nodes based on tags/labels."""
        if remove_prefixes is None:
            remove_prefixes = []
        
        self.logger.info(f"Starting tag-based export for tags: {tags}", "export")
        
        # Find all nodes with the specified tags
        matching_note_ids = self.node_discovery.search_notes_with_tags(tags)
        
        if not matching_note_ids:
            self.logger.warning(f"No nodes found with tags: {tags}", "export")
            return False
        
        self.logger.info(f"Found {len(matching_note_ids)} nodes with specified tags", "export")
        
        # Export all found nodes
        output_path = Path(output_dir)
        
        # Clear existing directory if it exists
        if output_path.exists():
            self.logger.info(f"Clearing existing directory: {output_path}", "export")
            if clear_directory(output_path):
                self.logger.info("Existing directory cleared successfully", "export")
            else:
                self.logger.warning("Could not fully clear existing directory", "export")
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_count = 0
        
        for note_id in matching_note_ids:
            try:
                note = self.connection.get_api().get_note(note_id)
                if note:
                    title = note.get('title', '')
                    note_type = note.get('type', '')
                    # Skip file and image nodes - these should only be handled by file exporter
                    if note_type in ['file', 'image']:
                        self.logger.debug(f"⏭️ Skipping file/image node: '{title}' (type: {note_type})", "export")
                        continue

                    # Also skip text nodes that correspond to uploaded files
                    if self._is_file_upload_text_node(title, note_id):
                        self.logger.debug(f"⏭️ Skipping file-upload text node: '{title}'", "export")
                        continue

                    if self._export_single_note(note_id, title, "", remove_prefixes, output_path):
                        exported_count += 1
                        
            except Exception as e:
                self.logger.error(f"Error exporting note {note_id}: {e}", "export")
                continue
        
        self.logger.info(f"Tag-based export completed: {exported_count} files exported to {output_dir}", "export")
        return exported_count > 0
    
    def _export_single_note(self, note_id: str, title: str, prefix: str, 
                           remove_prefixes: List[str], output_path: Path) -> bool:
        """Exports a single note as a Markdown file."""
        try:
            api = self.connection.get_api()
            
            # Get the content of the note
            content = api.get_note_content(note_id)
            if content is None:
                return False
            
            # Convert HTML to Markdown
            markdown_content = html_to_markdown(content)

            if not markdown_content.strip():
                return False

            # Process the title for the filename
            processed_title = process_title_with_prefix(title, prefix, remove_prefixes)
            if not processed_title:
                processed_title = f"untitled-{note_id}"

            # Remove the first line if it is a # heading
            # (Trilium often adds the node title as the first line)
            lines = markdown_content.split('\n')
            if lines and lines[0].strip().startswith('#'):
                # Remove first line
                lines = lines[1:]
                # Remove subsequent blank lines
                while lines and not lines[0].strip():
                    lines = lines[1:]
                markdown_content = '\n'.join(lines)

            # Create safe filename
            safe_filename = make_safe_filename(processed_title) + ".md"
            file_path = output_path / safe_filename

            # Write Markdown file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
                f.write("\\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export note {note_id} ('{title}'): {e}", "export")
            return False
    
    def export_node_content(self, node_id: str, output_dir: str) -> bool:
        """Export single node content to markdown file."""
        try:
            # Get node details from API
            api = self.connection.get_api()
            note = api.get_note(node_id)
            if not note:
                self.logger.error(f"Note {node_id} not found", "export")
                return False
            
            title = note.get('title', 'Unknown')
            note_type = note.get('type', '')
            
            # Skip file and image nodes - these should only be handled by file exporter
            if note_type in ['file', 'image']:
                self.logger.debug(f"⏭️ Skipping file/image node {node_id} ('{title}') - use file exporter instead", "export")
                return False

            # Also skip text nodes that correspond to uploaded files
            if self._is_file_upload_text_node(title, node_id):
                self.logger.debug(f"⏭️ Skipping file-upload text node {node_id} ('{title}') - matches file in parent", "export")
                return False
            
            output_path = Path(output_dir)
            
            # Call _export_single_note with all required parameters
            return self._export_single_note(node_id, title, "", [], output_path)
        except Exception as e:
            self.logger.error(f"Failed to export node {node_id}: {e}", "export")
            return False
    
    def _get_parent_node_files(self, node_id: str) -> set:
        """Get all filenames from parent node's file/image children."""
        try:
            api = self.connection.get_api()
            
            # Get the current note to find its parent
            note = api.get_note(node_id)
            if not note:
                return set()
            
            # Get parent branch IDs
            parent_branch_ids = note.get('parentBranchIds', [])
            if not parent_branch_ids:
                return set()
            
            filenames = set()
            
            # Check all parents (a note can have multiple parents)
            for parent_branch_id in parent_branch_ids:
                # Get parent note from branch
                try:
                    branch_info = api.get_branch(parent_branch_id)
                    if not branch_info:
                        continue
                        
                    parent_note_id = branch_info.get('parentNoteId')
                    if not parent_note_id:
                        continue
                        
                    parent_note = api.get_note(parent_note_id)
                    if not parent_note:
                        continue
                    
                    # Get all child notes of the parent
                    child_note_ids = parent_note.get('childNoteIds', [])
                    
                    for child_id in child_note_ids:
                        child_note = api.get_note(child_id)
                        if child_note and child_note.get('type') in ['file', 'image']:
                            filename = child_note.get('title', '')
                            if filename:
                                filenames.add(filename)
                                
                except Exception as e:
                    self.logger.debug(f"Error processing parent branch {parent_branch_id}: {e}", "export")
                    continue
            
            return filenames
            
        except Exception as e:
            self.logger.debug(f"Error getting parent files for node {node_id}: {e}", "export")
            return set()
    
    def _is_file_upload_text_node(self, note_title: str, node_id: str) -> bool:
        """Check if this text node corresponds to an uploaded file by title matching."""
        try:
            # Get all filenames from parent nodes
            parent_files = self._get_parent_node_files(node_id)
            
            # Check for exact title match
            if note_title in parent_files:
                self.logger.info(f"Detected file-upload text node: '{note_title}' (exact match)", "export")
                return True
            
            # Check for title match after removing prefixes (handles numbered prefixes)
            # Pattern: "04_02_filename.ext" should match "filename.ext"
            import re
            for filename in parent_files:
                # Remove common prefixes like "04_02_", "01_", etc.
                title_without_prefix = re.sub(r'^\d+_\d*_?', '', note_title)
                if title_without_prefix == filename:
                    self.logger.info(f"Detected file-upload text node: '{note_title}' (matches '{filename}' after prefix removal)", "export")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error checking file-upload status for '{note_title}': {e}", "export")
            return False  # In case of error, don't skip the node