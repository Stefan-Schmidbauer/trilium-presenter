"""
Constants for TriliumPresenter application.
Centralizes commonly used constants to avoid duplication and magic strings.
"""

# Trilium System Tags - tags that should be filtered out during export
TRILIUM_SYSTEM_TAGS = {
    'archived', 'autoReadSize', 'calendarRoot', 'child', 'clipperInbox',
    'cssClass', 'customRequestHandler', 'customResourceProvider', 'dateCreated',
    'dateModified', 'disableVersioning', 'displayRelations', 'etapiTokens',
    'eventLog', 'excludeFromExport', 'fullContentWidth', 'growthFactor',
    'hideChildrenOverview', 'hidePromotedAttributes', 'mapRootNoteId', 'monthNote',
    'searchMonthNote', 'template', 'textSnippet', 'todoDate',
    'viewType', 'widget', 'wordCount', 'yearNote', 'weight',
    'taskDoneRoot', 'taskLocationNote', 'taskLocationRoot',
    'taskTagNote', 'taskTagRoot', 'taskTodoRoot',
    # Additional system tags from the actual code
    'iconClass', 'docName', 'originalFileName', 'builtinWidget',
    'fileSize', 'dateNote', 'command', 'location',
    'geolocation', 'keepCurrentHoisting', 'sorted', 'doneDate',
    'launcherType', 'searchString', 'webViewSrc', 'action',
    'appCss', 'appTheme', 'baseSize', 'bookZoomLevel',
    'bookmarkFolder', 'bookmarked', 'desktopOnly',
    'excludeFromNoteMap', 'executeButton', 'executeDescription'
}

# GUI Configuration
GUI_WINDOW_SIZE = "1440x920"
GUI_PADDING = "10"

# File Extensions
MARKDOWN_EXTENSIONS = {'.md', '.markdown'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}

# Default Paths
DEFAULT_OUTPUT_DIR = "md"
DEFAULT_ATTACHMENTS_DIR = "attachments"
DEFAULT_CONFIG_DIR = "config"
