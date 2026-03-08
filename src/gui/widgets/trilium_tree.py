"""
Trilium Tree Widget for Node Navigation.
Simple lazy-loading tree view for Trilium node selection.
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Dict, Any, Callable


class TriliumTreeWidget:
    """Tree widget for Trilium node navigation with lazy loading."""
    
    def __init__(self, parent, services, logger=None):
        """Initialize the tree widget."""
        self.parent = parent
        self.services = services
        self.logger = logger

        # Repository reference
        self.repository = None

        # Currently selected node
        self.selected_node = None

        # Callbacks
        self.on_node_selected: Optional[Callable] = None

        # Loading state
        self.is_loading = False
        self._loading_placeholder = None

        # Create the tree widget
        self.create_widget()

        # Defer initial loading until after main loop starts
        # This prevents "main thread is not in main loop" errors
        self.parent.after(100, self.load_root_nodes_async)
    
    def create_widget(self):
        """Create the tree widget UI."""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Tree widget with hidden metadata column
        self.tree = ttk.Treeview(self.frame, selectmode='browse', columns=('#1',))
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure columns (only show the tree column, hide metadata)
        self.tree.configure(show='tree')
        self.tree.column('#1', width=0, stretch=False)  # Hidden column for node_id
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind('<<TreeviewOpen>>', self._on_tree_expand)  # Lazy load on expand
        
    def set_repository(self, repository):
        """Set the Trilium repository."""
        self.repository = repository
        # Defer loading to avoid "main thread is not in main loop" errors
        self.parent.after(100, self.load_root_nodes_async)
    
    def set_selection_callback(self, callback: Callable):
        """Set callback for node selection."""
        self.on_node_selected = callback
    
    def get_widget(self):
        """Get the tree widget frame."""
        return self.frame
    
    def load_root_nodes_async(self):
        """Load root level nodes asynchronously."""
        if self.is_loading:
            return

        if not self.repository:
            if hasattr(self.services, 'trilium_repository') and self.services.trilium_repository:
                self.repository = self.services.trilium_repository
            else:
                # Show loading placeholder
                self._show_loading_placeholder()
                return

        self.is_loading = True

        def load_in_background():
            try:
                # Load root children in background thread
                root_nodes = self.repository.get_child_nodes('root')

                # Update UI in main thread
                self.parent.after(0, lambda: self._populate_root_nodes(root_nodes))

            except Exception as e:
                # Handle error in main thread - capture 'e' immediately
                error_msg = f"Failed to load root nodes: {e}"
                self.parent.after(0, lambda msg=error_msg: self._on_load_error(msg))

        # Start background loading
        threading.Thread(target=load_in_background, daemon=True).start()

    def _show_loading_placeholder(self):
        """Show a loading placeholder in the tree."""
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add loading indicator
        self._loading_placeholder = self.tree.insert('', 'end',
                                                     text='⏳ Loading Trilium tree...',
                                                     tags=('loading',))

    def _populate_root_nodes(self, root_nodes):
        """Populate the tree with root nodes (called in main thread)."""
        try:
            # Clear existing tree (including loading placeholder)
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add root nodes with lazy children placeholders
            for node in root_nodes:
                node_id = node.node_id
                title = node.title or 'Untitled'

                # Add to tree with folder icon (assume all root nodes can have children)
                tree_item = self.tree.insert('', 'end', iid=node_id,
                                             text=f'📁 {title}',
                                             open=False)

                # Add dummy child to enable expand arrow (lazy loading)
                self.tree.insert(tree_item, 'end', text='⏳ Loading...', tags=('loading',))

            self.is_loading = False

            if self.logger:
                self.logger.info(f"Loaded {len(root_nodes)} root nodes", "tree")

        except Exception as e:
            self._on_load_error(f"Failed to populate tree: {e}")

    def _on_load_error(self, error_msg):
        """Handle loading errors (called in main thread)."""
        self.is_loading = False

        # Clear loading placeholder
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Check if this is an authentication error
        if 'Authentication failed' in error_msg or 'NOT_AUTHENTICATED' in error_msg:
            # Show prominent authentication error
            self.tree.insert('', 'end', text='🔒 Authentication Failed', tags=('error',))
            self.tree.insert('', 'end', text='   Please check your ETAPI token', tags=('error',))
            self.tree.insert('', 'end', text='   in .env file', tags=('error',))
        else:
            # Show generic error message
            self.tree.insert('', 'end', text=f'❌ {error_msg}', tags=('error',))

        if self.logger:
            self.logger.error(error_msg, "tree")
    
    def _on_tree_expand(self, event):
        """Handle tree expansion - lazy load children."""
        selection = self.tree.selection()
        if not selection:
            return

        tree_item_id = selection[0]

        # Check if this node has already been loaded (not dummy children)
        children = self.tree.get_children(tree_item_id)
        if children and len(children) == 1:
            first_child = children[0]
            child_text = self.tree.item(first_child, 'text')

            # If first child is loading placeholder, load real children
            if child_text == '⏳ Loading...':
                # Remove placeholder
                self.tree.delete(first_child)

                # Extract node_id
                try:
                    node_id = self.tree.set(tree_item_id, '#1')
                    if not node_id:
                        node_id = tree_item_id.split('_')[-1] if '_' in tree_item_id else tree_item_id
                except:
                    node_id = tree_item_id

                # Load children asynchronously
                self._load_children_async(tree_item_id, node_id)

    def _load_children_async(self, tree_item_id, node_id):
        """Load children for a node asynchronously."""
        def load_in_background():
            try:
                # Fetch children from repository
                child_nodes = self.repository.get_child_nodes(node_id)

                # Update UI in main thread
                self.parent.after(0, lambda: self._populate_children(tree_item_id, node_id, child_nodes))

            except Exception as e:
                # Handle error in main thread - capture variables immediately
                error_msg = str(e)
                self.parent.after(0, lambda item=tree_item_id, msg=error_msg: self._on_children_load_error(item, msg))

        # Start background loading
        threading.Thread(target=load_in_background, daemon=True).start()

    def _populate_children(self, tree_item_id, parent_node_id, child_nodes):
        """Populate children for a node (called in main thread)."""
        try:
            for node in child_nodes:
                node_id = node.node_id
                title = node.title or 'Untitled'

                # Create unique tree item ID
                child_tree_id = f"{tree_item_id}_{node_id}"

                # Skip if already exists
                if self.tree.exists(child_tree_id):
                    continue

                # Check if child has children (quick check only)
                icon = '📁'  # Assume folder by default

                # Add child to tree
                child_item = self.tree.insert(tree_item_id, 'end', iid=child_tree_id,
                                             text=f'{icon} {title}', open=False)

                # Store actual node_id as metadata
                self.tree.set(child_tree_id, '#1', node_id)

                # Add dummy child for lazy loading
                self.tree.insert(child_item, 'end', text='⏳ Loading...', tags=('loading',))

            if self.logger:
                self.logger.debug(f"Loaded {len(child_nodes)} children for node {parent_node_id}", "tree")

        except Exception as e:
            self._on_children_load_error(tree_item_id, str(e))

    def _on_children_load_error(self, tree_item_id, error_msg):
        """Handle error loading children."""
        if self.logger:
            self.logger.error(f"Failed to load children for {tree_item_id}: {error_msg}", "tree")

        # Show error in tree
        self.tree.insert(tree_item_id, 'end', text=f'❌ Error loading', tags=('error',))

    def _on_tree_select(self, event):
        """Handle tree selection."""
        selection = self.tree.selection()
        if selection:
            tree_item_id = selection[0]

            # Skip loading placeholders and error messages
            item_text = self.tree.item(tree_item_id, 'text')
            if item_text.startswith('⏳') or item_text.startswith('❌'):
                return

            # Only process real nodes
            if tree_item_id:
                # Get node details
                try:
                    # Get title from tree display
                    title = item_text
                    # Remove icon from title
                    if title.startswith('📁 ') or title.startswith('📄 '):
                        title = title[2:]

                    # Get actual node_id from metadata or extract from tree_item_id
                    try:
                        # Try to get stored node_id from metadata
                        node_id = self.tree.set(tree_item_id, '#1')
                        if not node_id:
                            # Fallback: extract from tree_item_id (for root nodes)
                            if '_' in tree_item_id:
                                node_id = tree_item_id.split('_')[-1]
                            else:
                                node_id = tree_item_id
                    except:
                        # Fallback: use tree_item_id as node_id (for root nodes)
                        node_id = tree_item_id

                    # Create a node dict for backward compatibility
                    self.selected_node = {
                        'noteId': node_id,
                        'title': title
                    }

                    # Trigger callback
                    if self.on_node_selected:
                        self.on_node_selected(self.selected_node)

                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error selecting node: {e}", "tree")
    
    
    def get_selected_node(self) -> Optional[Dict[str, Any]]:
        """Get currently selected node."""
        return self.selected_node

    def refresh(self):
        """Refresh the tree from Trilium API."""
        # Clear any previous selection
        self.selected_node = None

        # Reload from API asynchronously
        self.load_root_nodes_async()