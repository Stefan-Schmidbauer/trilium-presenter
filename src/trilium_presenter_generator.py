#!/usr/bin/env python3
"""
TriliumPresenter Generator
Simplified version using external templates for maintainability.
"""

import os
import shutil
import argparse
import yaml
import markdown
import json
from pathlib import Path
from typing import List, Dict, Any
import re

# Import unified logging system
try:
    from . import logging_manager
except ImportError:
    import logging_manager

class TriliumPresenterGenerator:
    def __init__(self, config_file: str = None, presenter_mode: bool = False, 
                 input_dir: str = None, output_dir: str = None):
        """Initialize the HTML presentation generator."""
        self.config = self.load_config(config_file)
        
        # Use flexible input/output directories or fall back to config/defaults
        self.md_dir = Path(input_dir) if input_dir else Path(self.config.get('export', {}).get('output', {}).get('text', 'export'))
        # Attachments are now integrated in the export tree - no separate attachments dir needed
        self.output_dir = Path(output_dir) if output_dir else Path('created')
        
        self.presenter_mode = presenter_mode
        self.notes_data = {}  # Store extracted notes
        self.attachment_registry = {}  # Map filename → relative path from slides
        self.logger = logging_manager.get_logger()
        
        # Markdown processor with extensions
        self.md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'toc'
        ])
    
    def load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        default_config = {
            'export': {
                'output': {
                    'text': 'md',
                    'images': 'attachments'
                }
            },
            'templates': {
                'source_dir': 'config/html_templates',
                'output_dir': 'created',
                'files': {
                    'css': ['base.css', 'content-slides.css', 'navigation.css', 'title-slide.css'],
                    'js': ['navigation.js', 'sync.js', 'simple_presenter.js'],
                    'html': ['slide_template.html', 'simple_presenter.html']
                }
            },
            'presentation': {
                'title': 'HTML Presentation',
                'author': 'Author',
                'background': '/assets/title-background.svg'
            }
        }
        
        # Use new default config file if none specified
        if config_file is None:
            config_file = 'config/presentation.yaml'
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                # Merge user config with defaults
                self._deep_merge(default_config, user_config)
        
        return default_config
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge two dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def setup_output_structure(self):
        """Create the output directory structure."""
        self.logger.step(f"Setting up HTML output structure in {self.output_dir}", "presentation")
        
        # Remove existing output directory to ensure clean rebuild
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        # Create main directories
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / 'slides').mkdir(exist_ok=True)
        (self.output_dir / 'css').mkdir(exist_ok=True)
        (self.output_dir / 'js').mkdir(exist_ok=True)
        (self.output_dir / 'assets').mkdir(exist_ok=True)
        (self.output_dir / 'attachments').mkdir(exist_ok=True)
        
        # Copy templates from config/html_templates
        self.copy_templates()
        
        # Copy all exported directories from export tree to maintain structure
        for item in self.md_dir.iterdir():
            if item.is_dir():
                target_dir = self.output_dir / item.name
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(item, target_dir, dirs_exist_ok=True)
                self.logger.info(f"📁 Copied directory: {item.name}", "presentation")
    
    def copy_templates(self):
        """Copy template files from config/html_templates to output directory."""
        template_config = self.config.get('templates', {})
        source_dir = Path(template_config.get('source_dir', 'config/html_templates'))
        
        if not source_dir.exists():
            self.logger.warning(f"Template directory {source_dir} does not exist", "presentation")
            return
        
        # Copy CSS files
        css_files = template_config.get('files', {}).get('css', [])
        for css_file in css_files:
            src_path = source_dir / 'css' / css_file
            dest_path = self.output_dir / 'css' / css_file
            if src_path.exists():
                shutil.copy2(src_path, dest_path)
                self.logger.file_operation("Copied CSS template", css_file, "presentation")
            else:
                self.logger.warning(f"CSS template {css_file} not found", "presentation")
        
        # Copy JS files (base templates, will be customized later)
        js_files = []  # All JS files are now templated
        for js_file in js_files:
            src_path = source_dir / 'js' / js_file
            dest_path = self.output_dir / 'js' / js_file
            if src_path.exists():
                shutil.copy2(src_path, dest_path)
                self.logger.file_operation("Copied JS template", js_file, "presentation")
            else:
                self.logger.warning(f"JS template {js_file} not found", "presentation")
        
        # Copy all assets from assets directory
        assets_source = source_dir / 'assets'
        if assets_source.exists():
            for asset_file in assets_source.iterdir():
                if asset_file.is_file():
                    dest_path = self.output_dir / 'assets' / asset_file.name
                    shutil.copy2(asset_file, dest_path)
                    self.logger.file_operation("Copied asset", asset_file.name, "presentation")
    
    def load_template(self, template_name: str) -> str:
        """Load a template file and return its content."""
        template_config = self.config.get('templates', {})
        source_dir = Path(template_config.get('source_dir', 'config/html_templates'))
        
        # Handle different template types
        if template_name.endswith('.html'):
            template_path = source_dir / 'html' / template_name
        elif template_name.endswith('.js'):
            template_path = source_dir / 'js' / template_name
        elif template_name.endswith('.css'):
            template_path = source_dir / 'css' / template_name
        else:
            template_path = source_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found at {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render_template(self, template_content: str, **kwargs) -> str:
        """Simple template rendering with {{VARIABLE}} substitution."""
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))
        return template_content
    
    def get_markdown_files(self) -> List[Path]:
        """Get all markdown files sorted by name."""
        if not self.md_dir.exists():
            self.logger.warning(f"Markdown directory {self.md_dir} does not exist", "presentation")
            return []
        
        md_files = list(self.md_dir.glob("*.md"))
        md_files.sort()  # Sort alphabetically
        self.logger.info(f"Found {len(md_files)} markdown files", "presentation")
        return md_files
    
    def process_markdown_content(self, content: str, is_title_slide: bool = False) -> str:
        """Process markdown content and handle image sizing."""
        # Remove notes section from content (already extracted separately)
        # Pandoc syntax only: ::: {.notes}
        content = re.sub(r':::+\s*\{\.notes\}.*?:::+', '', content, flags=re.DOTALL | re.MULTILINE)

        # Remove page breaks (not needed in HTML presentations)
        # Pandoc syntax: ::: {.page-break} or ::: {.pagebreak}
        content = re.sub(r':::+\s*\{\.page-?break\}\s*:::+', '', content, flags=re.MULTILINE)

        # First, extract column content and process it separately
        column_content = self.extract_and_process_columns(content)

        # Apply markdown processing
        html_content = self.md.convert(column_content)

        # Resolve attachment paths (filename.png → ../attachments/filename.png)
        html_content = self.resolve_attachment_paths(html_content)

        # Additional processing for images
        html_content = self.process_image_attributes(html_content)

        # Clean up any remaining <p> tags around column divs
        html_content = self.clean_column_markup(html_content)

        return html_content
    
    def build_attachment_registry(self):
        """Build registry mapping attachment filenames to relative paths from slides."""
        if not (self.output_dir / 'attachments').exists():
            return
        
        attachment_dir = self.output_dir / 'attachments'
        for file_path in attachment_dir.rglob('*'):
            if file_path.is_file():
                filename = file_path.name
                # Use filename directly (path will be handled in markdown)
                relative_path = filename
                self.attachment_registry[filename] = relative_path
    
    def resolve_attachment_paths(self, content: str) -> str:
        """Resolve image paths - images are now integrated in export tree."""
        import re
        
        # Pattern 1: src="filename.ext" (bare filenames)
        pattern1 = r'src="([^/"\\]+\.(png|jpg|jpeg|gif|svg|webp|bmp|tiff))"'
        
        # Pattern 2: src="Folder/filename.ext" (folder paths from export tree)
        pattern2 = r'src="([A-Za-z][^/"\\]*)/([^/"\\]+\.(png|jpg|jpeg|gif|svg|webp|bmp|tiff))"'
        
        def replace_bare_filename(match):
            filename = match.group(1)
            if filename in self.attachment_registry:
                resolved_path = self.attachment_registry[filename]
                return f'src="{resolved_path}"'
            else:
                return match.group(0)  # Images are in export tree - use as-is
        
        def replace_folder_path(match):
            folder = match.group(1)
            filename = match.group(2)
            # Images are copied directly to output directory, reference them relative to slides/
            target_path = self.output_dir / folder / filename
            if target_path.exists():
                resolved_path = f"../{folder}/{filename}"
                self.logger.debug(f"Resolved {folder}/{filename} → {resolved_path}", "presentation")
                return f'src="{resolved_path}"'
            else:
                # Image not found - log clear error with available files for debugging
                target_folder = self.output_dir / folder
                if target_folder.exists():
                    available_files = [f.name for f in target_folder.iterdir() if f.is_file()]
                    self.logger.error(
                        f"Image not found: {folder}/{filename}\n"
                        f"  Available files in {folder}/: {', '.join(available_files) if available_files else 'none'}",
                        "presentation"
                    )
                else:
                    self.logger.error(f"Image not found: {folder}/{filename} (folder does not exist)", "presentation")
                return match.group(0)  # Return unchanged
        
        # Apply both patterns
        content = re.sub(pattern1, replace_bare_filename, content, flags=re.IGNORECASE)
        content = re.sub(pattern2, replace_folder_path, content, flags=re.IGNORECASE)
        
        return content
    
    def process_image_attributes(self, content: str) -> str:
        """Process image attributes like {.class}."""
        # Simple processing - can be extended as needed
        return content
    
    def extract_and_process_columns(self, content: str) -> str:
        """Extract column sections and process them with markdown placeholders.

        Supports Pandoc syntax only: ::: {.columns} with nested ::: {.column}.
        """
        # Pandoc syntax - ::: {.columns} with nested :::: {.column}
        # Use non-greedy match and ensure we stop at the correct closing :::
        # The pattern matches until we find ::: at start of line (not ::::)
        pandoc_column_pattern = r'::: \{\.columns\}(.*?)\n:::(?!:)(?!\s*\{)'

        def process_pandoc_column_section(match):
            column_content = match.group(1)

            # Split by column markers
            column_parts = re.split(r':::+\s*\{\.column\}', column_content)

            # Process each part
            processed_parts = []
            for i, part in enumerate(column_parts):
                if i == 0:
                    # Content before first column marker (usually just whitespace)
                    continue
                else:
                    # This is column content
                    # Remove closing colons from end (handles any nesting depth)
                    col_content = re.sub(r'\n:::+\s*$', '', part, flags=re.MULTILINE)
                    if col_content.strip():
                        temp_md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
                        processed_part = temp_md.convert(col_content.strip())
                        processed_parts.append(f'<div class="column column-{i}">{processed_part}</div>')

            # Count columns automatically
            column_count = len(processed_parts)
            processed_content = ''.join(processed_parts)

            return f'<div class="columns columns-{column_count}">{processed_content}</div>'

        # Process Pandoc syntax
        content = re.sub(pandoc_column_pattern, process_pandoc_column_section, content, flags=re.DOTALL)

        return content
    
    def clean_column_markup(self, content: str) -> str:
        """Clean up markdown-generated <p> tags around column divs."""
        # Remove <p> tags that wrap column divs
        content = re.sub(r'<p><div class="columns', '<div class="columns', content)
        content = re.sub(r'<p><div class="column', '<div class="column', content)
        content = re.sub(r'</div></div></p>', '</div></div>', content)
        content = re.sub(r'</div></p>', '</div>', content)
        
        return content
    
    def create_slide_html(self, content: str, slide_num: int, total_slides: int, is_title_slide: bool = False) -> str:
        """Create HTML for a single slide using template."""
        slide_class = "title-slide" if is_title_slide else "content-slide"
        
        # Create navigation based on configuration
        nav_html = ""
        nav_config = self.config.get('navigation', {})
        
        if nav_config.get('show_nav_buttons', True):
            if slide_num > 1:
                nav_html += f'<a href="slide{slide_num-1}.html" class="nav-btn prev-btn">‹ Zurück</a>'
            if slide_num < total_slides:
                nav_html += f'<a href="slide{slide_num+1}.html" class="nav-btn next-btn">Weiter ›</a>'
        
        # Slide counter based on configuration
        counter_html = ""
        if nav_config.get('show_slide_counter', True):
            counter_html = f'<div class="slide-counter">{slide_num} / {total_slides}</div>'
        
        title = self.config.get('presentation', {}).get('title', 'TriliumPresenter')
        
        slide_css = "title-slide.css" if is_title_slide else "content-slides.css"
        
        # Load and render template
        template_content = self.load_template('slide_template.html')
        
        # Create navigation config for JavaScript
        import json
        nav_config_js = {
            'showKeyboardHints': nav_config.get('show_keyboard_hints', True),
            'showPresenterLink': nav_config.get('show_presenter_link', False)
        }
        
        import time
        timestamp = str(int(time.time()))
        
        return self.render_template(
            template_content,
            TITLE=title,
            SLIDE_CLASS=slide_class,
            SLIDE_CSS=slide_css,
            CONTENT=content,
            NAVIGATION=nav_html,
            COUNTER=counter_html,
            NAV_CONFIG=json.dumps(nav_config_js),
            TIMESTAMP=timestamp
        )
    
    def extract_notes(self, content: str) -> str:
        """Extract notes from markdown content.

        Pandoc syntax: ::: {.notes} ... :::
        """
        # Pandoc syntax - ::: {.notes} ... :::
        pandoc_notes_match = re.search(r':::+\s*\{\.notes\}(.*?):::+', content, re.DOTALL | re.MULTILINE)
        if pandoc_notes_match:
            notes_content = pandoc_notes_match.group(1).strip()
            return notes_content

        return ""
    
    def generate_presentation(self):
        """Generate the complete HTML presentation."""
        self.logger.section("Starting TriliumPresenter presentation generation", "presentation")
        
        # Setup output structure
        self.setup_output_structure()
        
        # Get markdown files
        md_files = self.get_markdown_files()
        if not md_files:
            self.logger.error("No markdown files found!", "presentation")
            return
        
        total_slides = len(md_files)
        self.logger.info(f"Generating {total_slides} slides...", "presentation")
        
        # Process each markdown file
        for i, md_file in enumerate(md_files, 1):
            self.logger.progress(f"Processing slide {i}: {md_file.name}", "presentation")
            
            # Read markdown content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract notes
            notes = self.extract_notes(content)
            if notes:
                self.notes_data[str(i)] = notes
            
            # Process markdown to HTML
            is_title_slide = i == 1  # First slide is title slide
            html_content = self.process_markdown_content(content, is_title_slide)
            
            # Create slide HTML
            slide_html = self.create_slide_html(html_content, i, total_slides, is_title_slide)
            
            # Write slide file
            slide_filename = 'index.html' if i == 1 else f'slide{i}.html'
            slide_path = self.output_dir / 'slides' / slide_filename
            with open(slide_path, 'w', encoding='utf-8') as f:
                f.write(slide_html)
        
        # Create main index.html
        self.create_main_index()
        
        # Create notes.json
        self.create_notes_json()
        
        # Create simple presenter only
        self.create_simple_presenter(total_slides)
        
        # Create navigation.js from template
        self.create_navigation_js(total_slides)
        
        # Create sync.js from template
        self.create_sync_js(total_slides)
        
        self.logger.success(f"TriliumPresenter presentation generated successfully in {self.output_dir}", "presentation")
    
    def create_main_index(self):
        """Create main index.html that redirects to first slide."""
        index_html = '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TriliumPresenter</title>
    <script>
        // Redirect to first slide
        window.location.href = 'slides/index.html';
    </script>
</head>
<body>
    <p>Redirecting to presentation...</p>
    <p>If you are not redirected automatically, <a href="slides/index.html">click here</a>.</p>
</body>
</html>'''
        
        with open(self.output_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(index_html)
    
    def create_notes_json(self):
        """Create notes.json file."""
        notes_file = self.output_dir / 'notes.json'
        with open(notes_file, 'w', encoding='utf-8') as f:
            json.dump(self.notes_data, f, indent=2, ensure_ascii=False)
    
    
    def create_simple_presenter(self, total_slides: int):
        """Create simple presenter HTML file using template."""
        self.logger.step(f"Creating simple presenter with {total_slides} slides...", "presentation")
        
        # Load and render template
        template_content = self.load_template('simple_presenter.html')
        title = self.config.get('presentation', {}).get('title', 'TriliumPresenter')
        
        # Render JavaScript template
        js_template = self.load_template('simple_presenter.js')
        js_content = self.render_template(js_template, TOTAL_SLIDES=total_slides)
        
        # Write rendered JS to output
        js_file = self.output_dir / 'js' / 'simple_presenter.js'
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        # Render HTML template
        html_content = self.render_template(
            template_content,
            TITLE=title
        )
        
        simple_presenter_file = self.output_dir / 'simple_presenter.html'
        with open(simple_presenter_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def create_navigation_js(self, total_slides: int):
        """Create navigation.js from template with correct total slides count."""
        self.logger.step(f"Creating navigation.js with {total_slides} slides...", "presentation")
        
        # Load and render template
        js_template = self.load_template('navigation.js')
        js_content = self.render_template(js_template, TOTAL_SLIDES=total_slides)
        
        # Write rendered JS to output
        js_file = self.output_dir / 'js' / 'navigation.js'
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        self.logger.info(f"Created navigation.js with total slides: {total_slides}", "presentation")
    
    def create_sync_js(self, total_slides: int):
        """Create sync.js from template with correct total slides count."""
        self.logger.step(f"Creating sync.js with {total_slides} slides...", "presentation")
        
        # Load and render template
        js_template = self.load_template('sync.js')
        js_content = self.render_template(js_template, TOTAL_SLIDES=total_slides)
        
        # Write rendered JS to output
        js_file = self.output_dir / 'js' / 'sync.js'
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        self.logger.info(f"Created sync.js with total slides: {total_slides}", "presentation")


def main():
    """Main function to generate TriliumPresenter presentation."""
    parser = argparse.ArgumentParser(description='Generate TriliumPresenter presentation from markdown files')
    parser.add_argument('--config', '-c', help='Configuration file path', 
                       default='config/presentation.yaml')
    parser.add_argument('--presenter', '-p', action='store_true', help='Enable presenter mode with notes and dual-window support')
    parser.add_argument('--input-dir', '-i', help='Input directory containing markdown files', 
                       default=None)
    parser.add_argument('--output-dir', '-o', help='Output directory for generated presentation (default: created/)', 
                       default=None)
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Setup logging
        logging_config = {}
        if Path("config/logging.yaml").exists():
            with open("config/logging.yaml", 'r', encoding='utf-8') as f:
                logging_config = yaml.safe_load(f) or {}
        
        logger = logging_manager.setup_logging(logging_config)
        
        # Create generator and run
        generator = TriliumPresenterGenerator(
            config_file=args.config, 
            presenter_mode=args.presenter,
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        generator.generate_presentation()
        logger.success("TriliumPresenter presentation generated successfully!", "presentation")
        
    except Exception as e:
        logger = logging_manager.get_logger()
        logger.error(f"Error generating presentation: {e}", "presentation")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    main()