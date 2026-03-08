"""
Trilium Node Discovery for TriliumPresenter - Simplified Version.
Handles node discovery, prefix searching, and tree traversal operations.
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict

# Simplified imports
try:
    from .constants import TRILIUM_SYSTEM_TAGS
    from . import logging_manager
    from .trilium_connection import TriliumConnection
except ImportError:
    from constants import TRILIUM_SYSTEM_TAGS
    import logging_manager
    from trilium_connection import TriliumConnection


class TriliumNodeDiscovery:
    """Handles node discovery and tree operations in Trilium."""
    
    def __init__(self, connection: TriliumConnection):
        self.connection = connection
        self.logger = logging_manager.get_logger()
    
    def _search_all_notes(self) -> List[Dict[str, Any]]:
        """Helper function: Searches all notes and normalizes the result."""
        api = self.connection.get_api()
        all_notes = api.search_note("*")
        
        # Normalize different response formats
        if isinstance(all_notes, list):
            return all_notes
        elif isinstance(all_notes, dict):
            if 'status' in all_notes:
                self.logger.error(f"Search failed: {all_notes.get('message', 'Unknown error')}", "api")
                return []
            elif 'results' in all_notes:
                return all_notes['results']
        
        self.logger.warning(f"Unexpected search result format: {type(all_notes)}", "api")
        return []
    
    def _get_branch_prefix(self, branch_id: str) -> Optional[str]:
        """Helper function: Gets branch prefix via API."""
        try:
            api = self.connection.get_api()
            branch = api.get_branch(branch_id)
            return branch.get('prefix') if branch else None
        except:
            return None
    
    def get_all_tags(self, user_only: bool = True) -> Dict[str, int]:
        """Retrieves all available labels via API - simplified version."""
        api = self.connection.get_api()
        tag_counts = defaultdict(int)
        
        try:
            # Simplified approach: Search directly for notes with labels
            all_notes = self._search_all_notes()
            
            for note in all_notes:
                note_id = note.get('noteId')
                if not note_id:
                    continue
                
                # Batch API Call for attributes
                try:
                    attributes = api.get_note_attributes(note_id)
                    for attr in attributes:
                        if attr.get('type') == 'label':
                            tag_name = attr.get('name', '').strip()
                            if tag_name and (not user_only or tag_name not in TRILIUM_SYSTEM_TAGS):
                                tag_counts[tag_name] += 1
                except:
                    continue
            
            return dict(tag_counts)
            
        except Exception as e:
            self.logger.error(f"Failed to get all tags: {e}", "api")
            return {}
    
    def get_available_prefixes(self) -> Dict[str, int]:
        """Retrieves all available branch prefixes - simplified version."""
        prefix_counts = defaultdict(int)
        
        try:
            all_notes = self._search_all_notes()
            self.logger.info(f"Processing {len(all_notes)} notes for prefix detection", "api")
            
            # Iterate through all notes for Branch Prefixes
            for note in all_notes:
                parent_branch_ids = note.get('parentBranchIds', [])
                if not parent_branch_ids:
                    continue
                
                # Check all branches for prefixes
                for branch_id in parent_branch_ids:
                    prefix = self._get_branch_prefix(branch_id)
                    if prefix and prefix.strip():
                        prefix_counts[prefix] += 1
            
            self.logger.info(f"Found {len(prefix_counts)} unique prefixes", "api")
            return dict(prefix_counts)
            
        except Exception as e:
            self.logger.error(f"Failed to get prefixes: {e}", "api")
            return {}
    
    def get_nodes_by_prefix(self, prefix: str) -> Dict[str, str]:
        """Retrieves all nodes with a specific branch prefix - simplified."""
        matching_nodes = {}
        
        try:
            self.logger.info(f"Searching for nodes with prefix '{prefix}'", "api")
            all_notes = self._search_all_notes()
            
            # Search all notes for the desired prefix
            for note in all_notes:
                note_id = note.get('noteId')
                title = note.get('title', 'Unknown').strip()
                parent_branch_ids = note.get('parentBranchIds', [])
                
                if not note_id or not parent_branch_ids:
                    continue
                
                # Check all branches of this note
                for branch_id in parent_branch_ids:
                    branch_prefix = self._get_branch_prefix(branch_id)
                    if branch_prefix == prefix:
                        matching_nodes[note_id] = title
                        self.logger.info(f"Found node with prefix '{prefix}': '{title}'", "api")
                        break  # Prefix found, no further searching
            
            self.logger.info(f"Found {len(matching_nodes)} nodes with prefix '{prefix}'", "api")
            return matching_nodes
            
        except Exception as e:
            self.logger.error(f"Failed to get nodes by prefix '{prefix}': {e}", "api")
            return {}
    
    def get_child_notes_recursive(self, parent_note_id: str, visited: set = None) -> List[str]:
        """Retrieves all child nodes recursively via API with cycle detection."""
        if visited is None:
            visited = set()
        
        # Cycle detection - prevents infinite loops
        if parent_note_id in visited:
            self.logger.warning(f"Cyclic reference detected at node {parent_note_id}", "api")
            return []
        
        visited.add(parent_note_id)
        api = self.connection.get_api()
        
        try:
            # Get the parent note to access its childNoteIds
            parent_note = api.get_note(parent_note_id)
            if not parent_note or 'childNoteIds' not in parent_note:
                visited.remove(parent_note_id)
                return []
            
            child_ids = parent_note['childNoteIds']
            if not child_ids:
                visited.remove(parent_note_id)
                return []
            
            all_children = []
            
            for child_id in child_ids:
                if child_id and child_id not in visited:
                    all_children.append(child_id)
                    # Recursively get children of this child
                    grandchildren = self.get_child_notes_recursive(child_id, visited)
                    all_children.extend(grandchildren)
            
            visited.remove(parent_note_id)
            return all_children
            
        except Exception as e:
            self.logger.error(f"Recursion error for {parent_note_id}: {e}", "api")
            if parent_note_id in visited:
                visited.remove(parent_note_id)
            return []
    
    def get_direct_child_nodes(self, parent_note_id: str) -> List[str]:
        """Retrieves only the direct child nodes (no recursion) in correct order."""
        api = self.connection.get_api()

        try:
            parent_note = api.get_note(parent_note_id)

            # Check for API error responses (authentication, authorization, etc.)
            if parent_note and isinstance(parent_note, dict):
                if 'status' in parent_note or 'code' in parent_note or 'message' in parent_note:
                    error_code = parent_note.get('code', 'UNKNOWN')
                    error_msg = parent_note.get('message', 'Unknown error')
                    status = parent_note.get('status', 0)

                    # Raise specific exception for authentication errors
                    if status == 401 or error_code == 'NOT_AUTHENTICATED':
                        raise Exception(f"Authentication failed: {error_msg}. Please check your ETAPI token in .env file")
                    else:
                        raise Exception(f"API Error ({status}): {error_msg}")

            if not parent_note or 'childNoteIds' not in parent_note:
                return []

            child_ids = parent_note['childNoteIds']
            if not child_ids:
                return []

            # Get parent branches to find notePosition for each child
            # parentBranchIds contains the branches where this note is a child
            # We need to find the branches where parent_note_id is the PARENT
            # Use search to find all branches and extract positions
            child_branches = []

            for child_id in child_ids:
                if not child_id:
                    continue

                # Get the child note to access its parent branches
                try:
                    child_note = api.get_note(child_id)
                    if not child_note:
                        continue

                    parent_branch_ids = child_note.get('parentBranchIds', [])

                    # Find the branch that connects this child to our parent
                    note_position = 10  # Default position if not found
                    for branch_id in parent_branch_ids:
                        try:
                            branch = api.get_branch(branch_id)
                            if branch and branch.get('parentNoteId') == parent_note_id:
                                # Found the correct branch!
                                note_position = branch.get('notePosition', 10)
                                break
                        except:
                            continue

                    child_branches.append({
                        'noteId': child_id,
                        'notePosition': note_position
                    })

                except Exception as e:
                    # If we can't get position, add with default
                    self.logger.debug(f"Could not get position for child {child_id}: {e}", "api")
                    child_branches.append({
                        'noteId': child_id,
                        'notePosition': 10
                    })

            # Sort by notePosition (Trilium uses 10, 20, 30, etc. for ordering)
            child_branches.sort(key=lambda x: x['notePosition'])

            # Return sorted child IDs
            return [branch['noteId'] for branch in child_branches]

        except Exception as e:
            self.logger.error(f"Error getting direct child notes for {parent_note_id}: {e}", "api")
            return []
    
    def get_child_node_prefixes(self, parent_node_id: str) -> Dict[str, int]:
        """Retrieves branch prefixes of child nodes - simplified."""
        prefix_counts = defaultdict(int)
        
        try:
            # Get all child nodes recursively
            child_note_ids = self.get_child_notes_recursive(parent_node_id)
            if not child_note_ids:
                return {}
            
            # Get all notes once for efficient searching
            all_notes = self._search_all_notes()
            notes_map = {note.get('noteId'): note for note in all_notes if note.get('noteId')}
            
            # Check each child for prefixes
            for child_id in child_note_ids:
                target_note = notes_map.get(child_id)
                if not target_note:
                    continue
                
                parent_branch_ids = target_note.get('parentBranchIds', [])
                for branch_id in parent_branch_ids:
                    prefix = self._get_branch_prefix(branch_id)
                    if prefix:
                        prefix_counts[prefix] += 1
            
            result = dict(prefix_counts)
            self.logger.info(f"Found {len(result)} prefixes in {len(child_note_ids)} child nodes", "api")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get child node prefixes for {parent_node_id}: {e}", "api")
            return {}

    def search_notes_with_tags(self, tags: List[str]) -> List[str]:
        """Searches for notes with specific tags/labels."""
        api = self.connection.get_api()
        
        try:
            matching_note_ids = []
            
            for tag in tags:
                # Search for notes with this specific tag
                search_query = f"#{tag}"
                results = api.search_note(search_query)
                
                if isinstance(results, list):
                    for note in results:
                        note_id = note.get('noteId')
                        if note_id and note_id not in matching_note_ids:
                            matching_note_ids.append(note_id)
            
            return matching_note_ids
            
        except Exception as e:
            self.logger.error(f"Failed to search notes with tags {tags}: {e}", "api")
            return []