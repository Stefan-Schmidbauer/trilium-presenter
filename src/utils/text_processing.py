"""
Text processing utilities for TriliumPresenter.
Handles HTML to Markdown conversion and title processing.
"""

import html
import re
from typing import List


def html_to_markdown(html_content: str) -> str:
    """
    Converts HTML to Markdown (simple implementation).
    
    Args:
        html_content: HTML content as string
        
    Returns:
        Converted Markdown text
    """
    if not html_content:
        return ""
    
    # Remove HTML tags and convert to plain text
    text = html.unescape(html_content)
    text = re.sub(r'<p[^>]*>', '', text)
    text = re.sub(r'</p>', '\n\n', text)
    text = re.sub(r'<br[^>]*>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()


def process_title_with_prefix(title: str, prefix: str, remove_prefixes: List[str]) -> str:
    """
    Processes the title with prefix removal.
    
    Args:
        title: Original title
        prefix: Current prefix (unused in current implementation)
        remove_prefixes: List of prefixes to remove
        
    Returns:
        Processed title without specified prefixes
    """
    if not title:
        return ""
    
    # Remove specified prefixes from the title
    processed_title = title
    for remove_prefix in remove_prefixes:
        if processed_title.startswith(remove_prefix):
            processed_title = processed_title[len(remove_prefix):].lstrip()
            break
    
    return processed_title