"""
Simplified Export Tab for TriliumPresenter GUI.
Combines MD export + file export with tree navigation.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Optional, Dict, Any

from gui.base_tab import BaseTab
from gui.widgets.trilium_tree import TriliumTreeWidget
from gui.widgets.modern_messagebox import ModernMessageBox
from utils.file_utils import clear_directory


class ExportTab(BaseTab):
    """Simplified tab for unified Trilium export with tree navigation."""
    
    def __init__(self, parent, services, logger=None):
        """Initialize the export tab."""
        # UI elements (MUST be before super().__init__!)
        self.tree_widget = None
        self.selected_node_label = None
        self.output_dir_var = None
        self.output_dir_entry = None
        self.include_root_var = None
        self.export_button = None

        # Export configuration (MUST be before super().__init__!)
        # IMPORTANT: Use absolute path to avoid issues when server changes working directory
        project_root = Path(__file__).parent.parent.parent.parent
        self.default_export_dir = (project_root / "export").absolute()
        self.default_export_dir.mkdir(exist_ok=True)

        super().__init__(parent, services, logger)
        
    def get_tab_title(self) -> str:
        """Return the title for this tab."""
        return "📁 1. Export"
    
    def setup_tab(self):
        """Setup the export tab content."""
        # Main content area
        self.create_tree_section()
        self.create_output_section()
        self.create_export_controls()

        # Configure grid weights for the main frame
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)  # Tree section gets most space
    
    def create_tree_section(self):
        """Create the Trilium tree navigation section."""
        # Tree frame
        tree_frame = ttk.LabelFrame(self.frame, text="Trilium Nodes")
        tree_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                       padx=self.SPACING['standard_padx'], pady=self.SPACING['standard_pady'])
        
        # Header frame with refresh button
        header_frame = ttk.Frame(tree_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=(5, 0))
        
        # Refresh button in header
        refresh_button = ttk.Button(header_frame, text="🔄 Refresh Tree", 
                                   command=self._refresh_tree)
        refresh_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Create tree widget
        self.tree_widget = TriliumTreeWidget(tree_frame, self.services, self.logger)
        self.tree_widget.set_selection_callback(self._on_node_selected)
        self.tree_widget.get_widget().grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                                          padx=5, pady=(5, 5))
        
        # Configure tree frame grid
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(1, weight=1)
        header_frame.columnconfigure(0, weight=1)
        
        # Set tree repository
        if hasattr(self.services, 'trilium_repository') and self.services.trilium_repository:
            self.tree_widget.set_repository(self.services.trilium_repository)
    
    def create_details_section(self):
        """Removed: Node details section is no longer needed."""
        pass
    
    def create_output_section(self):
        """Create the output directory selection section."""
        output_frame = ttk.LabelFrame(self.frame, text="Export Settings")
        output_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E),
                         pady=self.SPACING['section_margin'])
        
        # Output directory
        dir_label = ttk.Label(output_frame, text="Output Directory:")
        dir_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.output_dir_var = tk.StringVar(value=str(self.default_export_dir))
        self.output_dir_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        browse_button = ttk.Button(output_frame, text="Browse...", command=self._browse_output_dir)
        browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Include root node checkbox
        self.include_root_var = tk.BooleanVar(value=False)  # Default: exclude root node
        include_root_checkbox = ttk.Checkbutton(output_frame, text="Export root node as well", 
                                               variable=self.include_root_var)
        include_root_checkbox.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=(5, 10))
        
        # Configure grid weights
        output_frame.columnconfigure(1, weight=1)
    
    def create_export_controls(self):
        """Create export control buttons."""
        controls_frame = ttk.Frame(self.frame)
        controls_frame.grid(row=2, column=0, columnspan=2, pady=self.SPACING['section_margin'])
        
        # Export button
        self.export_button = ttk.Button(controls_frame, text="🚀 Export Selected Subtree", 
                                       command=self._start_export, state='disabled')
        self.export_button.pack(side=tk.LEFT, padx=5)
    
    
    def _on_node_selected(self, node: Dict[str, Any]):
        """Handle node selection from tree."""
        if node:
            title = node.get('title', 'Unknown')
            node_id = node.get('noteId', '')
            
            self._log(f"Node selected: {title} (ID: {node_id})")
            self.export_button.config(state='normal')
            
            if self.logger:
                self.logger.info(f"Node selected: {title} (ID: {node_id})", "export")
        else:
            self._log("No node selected.")
            self.export_button.config(state='disabled')

    
    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Export Directory")
        if directory:
            self.output_dir_var.set(directory)
    
    def _refresh_tree(self):
        """Refresh the Trilium tree."""
        if self.tree_widget:
            self._log("🔄 Refreshing tree from Trilium...")
            try:
                self.tree_widget.refresh()
                self._log("✅ Tree refreshed successfully!")
                if self.logger:
                    self.logger.info("Tree refreshed from Trilium API", "export")
            except Exception as e:
                self._log(f"❌ Tree refresh failed: {str(e)}")
                if self.logger:
                    self.logger.error(f"Tree refresh failed: {e}", "export")
    
    def _start_export(self):
        """Start the export process with modal progress dialog."""
        selected_node = self.tree_widget.get_selected_node()
        if not selected_node:
            ModernMessageBox.showwarning("No Selection", "Please select a node to export.",
                                        parent=self.services.root)
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            ModernMessageBox.showwarning("No Output Directory", "Please specify an output directory.",
                                        parent=self.services.root)
            return

        include_root = self.include_root_var.get()
        node_title = selected_node.get('title', 'Unknown')

        # Disable export button during export
        self.export_button.config(state='disabled')

        # Create modal progress dialog
        progress = tk.Toplevel(self.services.root)
        progress.title("Export")
        progress.transient(self.services.root)
        progress.grab_set()
        ttk.Label(progress, text=f"⏳ Exporting '{node_title}'...",
                 font=("Arial", 11)).pack(pady=30, padx=50)
        progress.update()

        try:
            # Perform export (blocking)
            result = self._perform_export(selected_node, output_dir, include_root)
            progress.destroy()

            if result['success']:
                exported_count = result['count']
                output_path = result['output_dir']

                # Success message
                success_msg = f"Successfully exported {exported_count} nodes\n\nTo: {output_path}"

                # Check if server is running and add hint
                if self.services and hasattr(self.services, 'server_tab'):
                    server_tab = self.services.server_tab
                    if hasattr(server_tab, 'is_running') and server_tab.is_running:
                        success_msg += (
                            "\n\n"
                            "ℹ️ Hinweis: Der Präsentations-Server läuft noch.\n\n"
                            "Damit nach dem Erstellen die aktuellen Daten verwendet werden,\n"
                            "bitte Server stoppen und neu starten (Tab 3)."
                        )

                ModernMessageBox.showsuccess("Export Complete", success_msg,
                                           parent=self.services.root)
            else:
                ModernMessageBox.showerror("Export Failed", result['error'],
                                          parent=self.services.root)

        except Exception as e:
            progress.destroy()
            ModernMessageBox.showerror("Export Failed", str(e),
                                      parent=self.services.root)

        finally:
            # Re-enable export button
            self.export_button.config(state='normal')
    
    def _perform_export(self, node: Dict[str, Any], output_dir: str, include_root: bool) -> dict:
        """Perform the actual export.

        Args:
            node: Node dictionary with noteId and title
            output_dir: Output directory path
            include_root: Whether to include root node in export

        Returns:
            dict: {'success': bool, 'count': int, 'output_dir': str, 'error': str}
        """
        try:
            node_id = node['noteId']
            node_title = node['title']

            # Create node-specific output directory
            safe_title = self._make_safe_filename(node_title)
            node_output_dir = Path(output_dir) / safe_title

            # Clear existing directory if it exists
            if node_output_dir.exists():
                self._log(f"Clearing existing directory: {node_output_dir}")
                if clear_directory(node_output_dir):
                    self._log("✅ Existing directory cleared successfully")
                else:
                    self._log("⚠️ Warning: Could not fully clear existing directory")

            # Ensure directory exists (will be empty if cleared above)
            node_output_dir.mkdir(parents=True, exist_ok=True)

            self._log(f"Starting export of '{node_title}' to {node_output_dir}")

            # Get repository
            repository = self.services.trilium_repository
            if not repository:
                return {'success': False, 'count': 0, 'output_dir': '',
                       'error': 'Trilium repository not available'}

            # Simple subtree traversal - start with selected node
            if include_root:
                self._log("Exporting complete subtree (including root node)...")
            else:
                self._log("Exporting subtree children (excluding root node)...")

            # Export the selected node and all its children recursively
            exported_count = self._export_subtree_recursive(repository, node_id,
                                                           node_output_dir, "", include_root)

            self._log(f"✅ Export completed successfully!")
            self._log(f"Exported {exported_count} nodes to {node_output_dir}")

            # Notify service container about successful export
            if self.services and exported_count > 0:
                self.services.notify_directory_event('export_completed', str(node_output_dir))
                self._log(f"🔄 Export directory made available for subsequent tabs")

            return {'success': True, 'count': exported_count,
                   'output_dir': str(node_output_dir), 'error': ''}

        except Exception as e:
            self._log(f"❌ Export failed: {str(e)}")
            if self.logger:
                self.logger.error(f"Export failed: {e}", "export")
            return {'success': False, 'count': 0, 'output_dir': '',
                   'error': str(e)}
    
    def _export_subtree_recursive(self, repository, node_id: str, output_dir: Path, prefix: str, include_root: bool = True) -> int:
        """Recursively export a node and all its children."""
        exported_count = 0
        
        try:
            # Get the node info
            node_info = repository.get_node_by_id(node_id)
            if not node_info:
                self._log(f"⚠️ Could not get node info for ID: {node_id}")
                return 0
            
            node_title = node_info.title or "Untitled"
            
            # Export root node content only if include_root is True
            if include_root:
                # Check if this node should be exported as markdown
                if self._should_export_as_markdown(repository, node_info, node_id):
                    # Create filename with prefix + node title
                    if prefix:
                        filename = f"{prefix}_{self._make_safe_filename(node_title)}.md"
                    else:
                        filename = f"{self._make_safe_filename(node_title)}.md"
                    
                    # Export node content directly
                    self._log(f"Exporting: {filename}")
                    success = self._export_node_to_file(repository, node_info, output_dir, filename)
                else:
                    success = False  # Skipped, not an error
                
                if success:
                    exported_count += 1
                
                # Export attachments/files from this node
                self._export_node_attachments(node_id, output_dir, node_title)
            
            # Get child nodes
            children = repository.get_child_nodes(node_id)
            
            # Export each child recursively (depth-first, top-to-bottom)
            # Always include child nodes (even if root is excluded)
            # Use a separate counter for numbering to avoid gaps from skipped nodes
            export_number = 0
            for child in children:
                export_number += 1
                child_prefix = f"{prefix}_{export_number:02d}" if prefix else f"{export_number:02d}"
                old_count = exported_count
                child_count = self._export_subtree_recursive(repository, child.node_id, output_dir, child_prefix, True)  # Always include children
                exported_count += child_count
                # If this child produced no exports, reclaim the number
                if child_count == 0:
                    export_number -= 1
                
        except Exception as e:
            self._log(f"Error exporting node {node_id}: {e}")
        
        return exported_count
    
    def _export_node_to_file(self, repository, node_info, output_dir: Path, filename: str) -> bool:
        """Export node content to specific filename."""
        try:
            # Get the raw content from the API connection
            api = repository._connection.get_api()
            content = api.get_note_content(node_info.node_id)

            # Log content fetch at debug level only
            if self.logger and hasattr(self.logger, 'debug'):
                content_preview = (content[:50] if content else "NONE")
                self.logger.debug(f"Content fetched for {filename}: {len(content) if content else 0} bytes (preview: {content_preview}...)", "export")

            if not content:
                self._log(f"  ⚠️ WARNING: Empty content for {filename} - NOT writing file")
                return True  # Empty content is still successful
            
            # Convert HTML to proper Markdown using markdownify
            from markdownify import markdownify as md
            markdown_content = md(content, heading_style="ATX", bullets="-",
                                  code_language="", strip=['script', 'style'])
            
            # Write markdown content as-is (don't add title header - it's already in the filename)
            # Write to file
            file_path = output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return True
            
        except Exception as e:
            self._log(f"Error exporting node to {filename}: {e}")
            return False
    
    def _make_safe_filename(self, title: str) -> str:
        """Convert title to safe filename."""
        # Replace problematic characters
        safe_chars = []
        for char in title:
            if char.isalnum() or char in '.- _()[]':
                safe_chars.append(char)
            elif char in ' /\\:':
                safe_chars.append('_')
        
        result = ''.join(safe_chars).strip('_')
        return result[:50]  # Limit length
    
    def _node_has_attachments(self, node_id: str) -> bool:
        """Check if a node has any attachments without creating directories."""
        try:
            repository = self.services.trilium_repository
            if not repository:
                return False
            
            # Get the API connection
            api = repository._connection.get_api()
            
            # Get the node info
            note = api.get_note(node_id)
            if not note:
                return False
            
            note_type = note.get('type', '')
            
            # File/image nodes themselves should NOT create separate attachment folders
            # They are already attachments and are exported from the parent node
            if note_type in ['file', 'image']:
                return False  # Changed from True to False!
            
            # Check for file/image child nodes (only for normal nodes)
            child_ids = note.get('childNoteIds', [])
            if child_ids:
                for child_id in child_ids:
                    try:
                        child_note = api.get_note(child_id)
                        if child_note and child_note.get('type') in ['file', 'image']:
                            return True
                    except:
                        continue
            
            return False
            
        except Exception:
            return False
    
    def _export_node_attachments(self, node_id: str, output_dir: Path, node_title: str):
        """Export attachments/files from a node.

        Uses the Trilium child container node title as the folder name
        (e.g. a child node titled 'Bilder' creates a 'Bilder/' subfolder).
        Falls back to the parent node title if images are direct children.
        """
        try:
            repository = self.services.trilium_repository
            if not repository:
                return

            api = repository._connection.get_api()
            note = api.get_note(node_id)
            if not note:
                return

            child_ids = note.get('childNoteIds', [])
            if not child_ids:
                return

            for child_id in child_ids:
                try:
                    child_note = api.get_note(child_id)
                    if not child_note:
                        continue

                    child_type = child_note.get('type', '')
                    child_title = child_note.get('title', '')

                    if child_type in ['file', 'image']:
                        # Direct image/file child — use parent node title as folder
                        safe_folder = self._make_safe_filename(node_title)
                        folder_dir = output_dir / safe_folder
                        folder_dir.mkdir(parents=True, exist_ok=True)
                        if self._extract_single_file_directly(api, child_id, child_note, folder_dir):
                            self._log(f"📎 Extracted '{child_title}' to {safe_folder}/")

                    elif child_type == 'text':
                        # Check if this text node is a container for images (e.g. "Bilder")
                        grandchild_ids = child_note.get('childNoteIds', [])
                        has_image_children = False
                        for gc_id in grandchild_ids:
                            gc_note = api.get_note(gc_id)
                            if gc_note and gc_note.get('type') in ['file', 'image']:
                                has_image_children = True
                                break

                        if has_image_children:
                            # Use the container node's title as folder name
                            safe_folder = self._make_safe_filename(child_title)
                            folder_dir = output_dir / safe_folder
                            folder_dir.mkdir(parents=True, exist_ok=True)
                            extracted = self._extract_files_directly(child_id, folder_dir)
                            if extracted > 0:
                                self._log(f"📎 Extracted {extracted} attachments to {safe_folder}/")
                            else:
                                try:
                                    folder_dir.rmdir()
                                except OSError:
                                    pass

                except Exception:
                    continue

        except Exception as e:
            pass
    
    def _extract_files_directly(self, node_id: str, target_dir: Path) -> int:
        """Extract files from a node directly to target directory without creating subdirs."""
        extracted_count = 0
        
        try:
            repository = self.services.trilium_repository
            api = repository._connection.get_api()
            
            # Get the node info
            note = api.get_note(node_id)
            if not note:
                return 0
            
            note_type = note.get('type', '')
            
            # Extract if this is a file/image node itself
            if note_type in ['file', 'image']:
                if self._extract_single_file_directly(api, node_id, note, target_dir):
                    extracted_count += 1
            
            # Extract from child file/image nodes
            child_ids = note.get('childNoteIds', [])
            if child_ids:
                for child_id in child_ids:
                    try:
                        child_note = api.get_note(child_id)
                        if child_note and child_note.get('type') in ['file', 'image']:
                            if self._extract_single_file_directly(api, child_id, child_note, target_dir):
                                extracted_count += 1
                    except Exception:
                        continue
                        
        except Exception as e:
            self._log(f"Error extracting files from node {node_id}: {e}")
            
        return extracted_count
    
    def _extract_single_file_directly(self, api, node_id: str, note: dict, target_dir: Path) -> bool:
        """Extract a single file directly to target directory."""
        try:
            filename = note.get('title', f'file_{node_id}')
            safe_filename = self._make_safe_filename(filename)

            # Ensure filename has proper extension
            if '.' not in safe_filename and note.get('type') == 'image':
                safe_filename += '.jpg'  # Default for images

            file_path = target_dir / safe_filename

            # Get file content - use direct ETAPI request for reliable binary support
            file_content = None
            try:
                file_content = api.get_note_content(node_id)
            except (UnicodeDecodeError, Exception):
                pass

            # Fallback: direct HTTP request via TriliumConnection attributes
            if file_content is None:
                try:
                    import requests
                    connection = self.services.trilium_repository._connection
                    headers = {"Authorization": connection.token}
                    response = requests.get(
                        f"{connection.server_url}/etapi/notes/{node_id}/content",
                        headers=headers
                    )
                    if response.status_code == 200:
                        file_content = response.content
                except Exception as e:
                    self._log(f"Binary fallback failed for {filename}: {e}")

            if file_content:
                # Write file
                with open(file_path, 'wb') as f:
                    if isinstance(file_content, bytes):
                        f.write(file_content)
                    elif isinstance(file_content, str):
                        f.write(file_content.encode('utf-8', errors='ignore'))
                    else:
                        f.write(bytes(file_content))

                return True

        except Exception as e:
            self._log(f"Error extracting file {filename}: {e}")

        return False

    def _log(self, message: str):
        """Log message to console only (no GUI output)."""
        # Print to console for debugging
        print(f"[Export] {message}")

        # Optional: Log to file logger
        if self.logger:
            self.logger.info(message, "export")
    
    def _get_parent_node_files(self, repository, node_id: str) -> set:
        """Get all filenames from parent node's file/image children."""
        try:
            api = repository._connection.get_api()
            
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
                    self._log(f"Debug: Error processing parent branch {parent_branch_id}: {e}")
                    continue
            
            return filenames
            
        except Exception as e:
            self._log(f"Debug: Error getting parent files for node {node_id}: {e}")
            return set()
    
    def _is_file_upload_text_node(self, repository, note_title: str, node_id: str) -> bool:
        """Check if this text node corresponds to an uploaded file by title matching."""
        try:
            # Get all filenames from parent nodes
            parent_files = self._get_parent_node_files(repository, node_id)
            
            # Check for exact title match
            if note_title in parent_files:
                self._log(f"🔍 Detected file-upload text node: '{note_title}' (exact match)")
                return True
            
            # Check for title match after removing prefixes (handles numbered prefixes)
            # Pattern: "04_02_filename.ext" should match "filename.ext"
            import re
            for filename in parent_files:
                # Remove common prefixes like "04_02_", "01_", etc.
                title_without_prefix = re.sub(r'^\d+_\d*_?', '', note_title)
                if title_without_prefix == filename:
                    self._log(f"🔍 Detected file-upload text node: '{note_title}' (matches '{filename}' after prefix removal)")
                    return True
            
            return False
            
        except Exception as e:
            self._log(f"Debug: Error checking file-upload status for '{note_title}': {e}")
            return False  # In case of error, don't skip the node
    
    def _should_export_as_markdown(self, repository, node_info, node_id: str) -> bool:
        """Determine if a node should be exported as markdown file."""
        try:
            # Get node details from API  
            api = repository._connection.get_api()
            note = api.get_note(node_id)
            if not note:
                return False
            
            note_type = note.get('type', '')
            note_title = node_info.title or ''
            
            # Skip file and image nodes - these should only be handled by file exporter
            if note_type in ['file', 'image']:
                if self.logger:
                    self.logger.debug(f"⏭️ Skipping file/image node: '{note_title}' (type: {note_type})", "export")
                return False

            # Also skip text nodes that correspond to uploaded files
            if self._is_file_upload_text_node(repository, note_title, node_id):
                if self.logger:
                    self.logger.debug(f"⏭️ Skipping file-upload text node: '{note_title}' (auto-generated from file)", "export")
                return False
            
            # Export all other nodes as markdown
            return True
            
        except Exception as e:
            self._log(f"Error checking export eligibility for node {node_id}: {e}")
            return True  # In case of error, export the node (safer default)