#!/usr/bin/env python3
"""
Document PDF Generator for A4 Papers
Generates A4 PDF documents from standard markdown files (Arbeitspapiere).
Simplified version without profile system.
"""

import os
import shutil
import argparse
import markdown
import subprocess
import tempfile
from pathlib import Path
from typing import List
import re

# Import unified logging system
try:
    from . import logging_manager
except ImportError:
    import logging_manager

# Import WeasyPrint for modern PDF generation
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class DocumentPDFGenerator:
    def __init__(self, config_file: str = None, input_dir: str = None, output_dir: str = None):
        """Initialize the document PDF generator with flexible configuration.

        Args:
            config_file: Path to YAML config file (for template_dir, etc.)
            input_dir: Input directory containing markdown files
            output_dir: Output directory for generated PDFs
        """
        self.config = self._load_config(config_file)
        # Use flexible input/output directories or fall back to defaults
        self.md_dir = Path(input_dir) if input_dir else Path('export')
        # Attachments are now integrated in the export tree - no separate attachments dir needed
        self.output_dir = Path(output_dir) if output_dir else Path('created')
        self.template_dir = Path(self.config.get('templates', {}).get('pdf_dir', 'config/pdf_templates'))
        self.temp_dir = None
        self.attachment_registry = {}
        self.logger = logging_manager.get_logger()
        
        # Markdown processor for documents
        self.md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'toc',
            'tables'
        ])
    
    def _load_config(self, config_file: str = None) -> dict:
        """Load configuration from YAML file."""
        if config_file is None:
            config_file = 'config/presentation.yaml'

        if config_file and os.path.exists(config_file):
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}

    def setup_temp_structure(self):
        """Create temporary directory structure for HTML generation."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix='pdf_temp_'))
        
        self.logger.step(f"Setting up temporary structure in {self.temp_dir}", "pdf")
        
        # Create directories
        (self.temp_dir / 'css').mkdir(exist_ok=True)
        (self.temp_dir / 'assets').mkdir(exist_ok=True)
        (self.temp_dir / 'attachments').mkdir(exist_ok=True)
        
        # Copy CSS template
        css_src = self.template_dir / 'css' / 'pdf_document.css'
        css_dest = self.temp_dir / 'css' / 'pdf_document.css'
        if css_src.exists():
            shutil.copy2(css_src, css_dest)
            self.logger.file_operation("Copied CSS template", "pdf_document.css", "pdf")
        
        # Copy assets directory (background SVG, etc.)
        assets_src = self.template_dir / 'assets'
        if assets_src.exists():
            shutil.copytree(assets_src, self.temp_dir / 'assets', dirs_exist_ok=True)
            self.logger.file_operation("Copied assets directory", str(assets_src), "pdf")

        # Note: Attachments are now integrated in the export tree (no separate dir needed)
    
    def load_template(self, template_name: str) -> str:
        """Load a template file and return its content."""
        template_path = self.template_dir / 'html' / template_name
        
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
            self.logger.warning(f"Markdown directory {self.md_dir} does not exist", "pdf")
            return []
        
        md_files = list(self.md_dir.glob("*.md"))
        md_files.sort()
        self.logger.info(f"Found {len(md_files)} markdown files", "pdf")
        return md_files
    
    def build_attachment_registry(self):
        """Build registry mapping attachment filenames to relative paths."""
        if not (self.temp_dir / 'attachments').exists():
            return
        
        attachment_dir = self.temp_dir / 'attachments'
        for file_path in attachment_dir.rglob('*'):
            if file_path.is_file():
                filename = file_path.name
                # Calculate relative path from HTML file
                relative_path = file_path.relative_to(self.temp_dir)
                self.attachment_registry[filename] = str(relative_path)
    
    def process_markdown_content(self, content: str) -> str:
        """Process markdown content for A4 document output."""
        # Remove notes sections (not needed in PDF documents)
        # Pandoc syntax: ::: {.notes}
        content = re.sub(r':::+\s*\{\.notes\}.*?:::+', '', content, flags=re.DOTALL | re.MULTILINE)

        # Process column content BEFORE markdown conversion
        content = self.extract_and_process_columns(content)
        
        # Process newpage markers BEFORE markdown conversion
        content = self.process_newpage_markers(content)
        
        # Apply markdown processing
        html_content = self.md.convert(content)
        
        # Resolve attachment paths
        html_content = self.resolve_attachment_paths(html_content)
        
        # Clean up column markup
        html_content = self.clean_column_markup(html_content)
        
        return html_content
    
    def resolve_attachment_paths(self, content: str) -> str:
        """Resolve image paths for PDF output - images are now integrated in export tree."""
        # Pattern for images - handle different markdown image formats
        pattern1 = r'src="([^/"\\]+\.(png|jpg|jpeg|gif|svg|webp|bmp|tiff))"'
        pattern2 = r'src="([A-Za-z][^/"\\]*)/([^/"\\]+\.(png|jpg|jpeg|gif|svg|webp|bmp|tiff))"'
        # Also handle markdown image syntax that might be in the HTML
        pattern3 = r'!\[([^\]]*)\]\(([^)]+\.(png|jpg|jpeg|gif|svg|webp|bmp|tiff))\)'
        
        def replace_bare_filename(match):
            filename = match.group(1)
            if filename in self.attachment_registry:
                resolved_path = self.attachment_registry[filename]
                return f'src="{resolved_path}"'
            else:
                # Images are in the export tree, use relative path as-is
                return match.group(0)
        
        def replace_folder_path(match):
            folder = match.group(1)
            filename = match.group(2)
            # Build absolute path to verify file exists
            attachment_path = self.md_dir / folder / filename
            if attachment_path.exists():
                return f'src="{attachment_path}"'
            else:
                # Image not found - log clear error with available files for debugging
                folder_path = self.md_dir / folder
                if folder_path.exists():
                    available_files = [f.name for f in folder_path.iterdir() if f.is_file()]
                    self.logger.error(
                        f"Image not found: {folder}/{filename}\n"
                        f"  Available files in {folder}/: {', '.join(available_files) if available_files else 'none'}",
                        "pdf"
                    )
                else:
                    self.logger.error(f"Image not found: {folder}/{filename} (folder does not exist)", "pdf")
                return match.group(0)  # Return unchanged
        
        def replace_markdown_image(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            # Images are already in the export tree with correct relative paths
            attachment_path = self.md_dir / image_path
            if attachment_path.exists():
                return f'<img src="{attachment_path}" alt="{alt_text}">'
            else:
                self.logger.warning(f"Image not found: {image_path}", "pdf")
                return f'<img src="{image_path}" alt="{alt_text}">'
        
        # Apply patterns
        content = re.sub(pattern1, replace_bare_filename, content, flags=re.IGNORECASE)
        content = re.sub(pattern2, replace_folder_path, content, flags=re.IGNORECASE)
        content = re.sub(pattern3, replace_markdown_image, content, flags=re.IGNORECASE)
        
        return content
    
    def extract_and_process_columns(self, content: str) -> str:
        """Process column layouts before markdown conversion.

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
                        temp_md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc', 'tables'])
                        processed_part = temp_md.convert(col_content.strip())
                        processed_parts.append(f'<div class="column column-{i}">{processed_part}</div>')

            # Count columns automatically
            column_count = len(processed_parts)
            processed_content = ''.join(processed_parts)
            return f'<div class="columns columns-{column_count}">{processed_content}</div>'

        # Process Pandoc syntax
        content = re.sub(pandoc_column_pattern, process_pandoc_column_section, content, flags=re.DOTALL)
        return content
    
    def process_newpage_markers(self, content: str) -> str:
        """Process page break markers for PDF.

        Pandoc div syntax: ::: {.page-break} or ::: {.pagebreak}
        """
        # Pandoc div syntax - matches both {.page-break} and {.pagebreak}
        content = re.sub(r':::+\s*\{\.page-?break\}\s*:::+', '<div class="page-break"></div>', content, flags=re.MULTILINE)

        return content
    
    def clean_column_markup(self, content: str) -> str:
        """Clean up markdown-generated markup for PDF."""
        content = re.sub(r'<p><div class="columns', '<div class="columns', content)
        content = re.sub(r'<p><div class="column', '<div class="column', content)
        content = re.sub(r'</div></div></p>', '</div></div>', content)
        content = re.sub(r'</div></p>', '</div>', content)
        return content
    
    def generate_html_document(self, content: str, title: str = "Arbeitspapier") -> str:
        """Generate complete HTML document for A4 output."""
        template_content = self.load_template('pdf_template.html')
        
        # Template variables
        template_vars = {
            'TITLE': title,
            'AUTHOR': 'Trilium Presenter',
            'SLIDES_CONTENT': content,
            'FOOTER_CONTENT': ''
        }
        
        html_content = self.render_template(template_content, **template_vars)
        return html_content
    
    def generate_pdf_with_weasyprint(self, html_file: Path, pdf_file: Path):
        """Generate PDF using WeasyPrint with full color support."""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint is not available. Install with: pip install weasyprint")
        
        self.logger.step("Generating A4 PDF with WeasyPrint...", "pdf")
        
        try:
            # Read HTML content
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create WeasyPrint HTML document
            html_doc = weasyprint.HTML(string=html_content, base_url=str(self.temp_dir))
            
            # Generate PDF with color support
            html_doc.write_pdf(str(pdf_file))
            
            if pdf_file.exists():
                file_size = pdf_file.stat().st_size / 1024  # KB
                self.logger.success(f"A4 PDF generated successfully with WeasyPrint: {pdf_file} ({file_size:.1f} KB)", "pdf")
            else:
                raise FileNotFoundError(f"PDF was not created: {pdf_file}")
                
        except Exception as e:
            self.logger.error(f"Error running WeasyPrint: {e}", "pdf")
            raise

    def generate_pdf_with_wkhtmltopdf(self, html_file: Path, pdf_file: Path):
        """Generate PDF using wkhtmltopdf with A4 settings."""
        self.logger.step("Generating A4 PDF with wkhtmltopdf...", "pdf")
        
        # Build wkhtmltopdf command with fixed A4 settings
        cmd = ['wkhtmltopdf']
        
        # Page format and orientation
        cmd.extend(['--page-size', 'A4'])
        cmd.extend(['--orientation', 'Portrait'])
        
        # Fixed margins for A4
        cmd.extend(['--margin-top', '2.5cm'])
        cmd.extend(['--margin-bottom', '3cm'])
        cmd.extend(['--margin-left', '2.5cm'])
        cmd.extend(['--margin-right', '2.5cm'])
        
        # Basic settings
        cmd.append('--enable-local-file-access')
        cmd.append('--disable-javascript')
        cmd.append('--background')
        
        # Input and output files
        cmd.extend([str(html_file), str(pdf_file)])
        
        
        try:
            # Run wkhtmltopdf
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.temp_dir)
            
            if result.returncode == 0:
                self.logger.success(f"A4 PDF generated successfully: {pdf_file}", "pdf")
            else:
                self.logger.error(f"wkhtmltopdf failed with return code {result.returncode}", "pdf")
                if result.stderr:
                    self.logger.error(f"wkhtmltopdf error: {result.stderr}", "pdf")
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
                
        except FileNotFoundError:
            self.logger.error("wkhtmltopdf not found. Please install wkhtmltopdf.", "pdf")
            raise
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running wkhtmltopdf: {e}", "pdf")
            raise
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def sanitize_filename(self, filename: str) -> str:
        """Convert filename to safe PDF filename."""
        # Remove .md extension
        name = filename.replace('.md', '')
        # Replace problematic characters
        safe_chars = []
        for char in name:
            if char.isalnum() or char in '-_ ':
                if char == ' ':
                    safe_chars.append('-')
                elif char == '_':
                    safe_chars.append('-')
                else:
                    safe_chars.append(char)
            elif char in 'äöüÄÖÜß':
                # German umlauts
                replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss'}
                safe_chars.append(replacements.get(char, char))
        return ''.join(safe_chars)

    def generate_individual_pdf(self, md_file: Path) -> Path:
        """Generate individual A4 PDF from single markdown file."""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process content
        html_content = self.process_markdown_content(content)
        
        # Add title from filename if content doesn't start with a heading
        if not html_content.strip().startswith('<h'):
            title = md_file.stem.replace('-', ' ').replace('_', ' ')
            html_content = f"<h2>{title}</h2>\n{html_content}"
        
        # Generate complete HTML document
        title = md_file.stem.replace('-', ' ').replace('_', ' ')
        html_document = self.generate_html_document(html_content, title)
        
        # Write HTML to temporary file
        html_filename = self.sanitize_filename(md_file.name) + '.html'
        html_file = self.temp_dir / html_filename
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_document)
        
        # Generate PDF with same name as markdown file
        pdf_filename = self.sanitize_filename(md_file.name) + '.pdf'
        pdf_file = self.output_dir / pdf_filename
        
        # Generate PDF using absolute paths - prefer WeasyPrint for color support
        if WEASYPRINT_AVAILABLE:
            self.generate_pdf_with_weasyprint(html_file, pdf_file.absolute())
        else:
            self.logger.warning("WeasyPrint not available, falling back to wkhtmltopdf", "pdf")
            self.generate_pdf_with_wkhtmltopdf(html_file, pdf_file.absolute())
        
        return pdf_file

    def generate_document_pdf(self) -> List[Path]:
        """Generate separate A4 PDF documents for each markdown file."""
        self.logger.section("Starting individual A4 PDF generation", "pdf")
        
        try:
            # Setup temporary structure
            self.setup_temp_structure()
            
            # Check for markdown files
            md_files = self.get_markdown_files()
            if not md_files:
                self.logger.error("No markdown files found!", "pdf")
                return []
            
            self.logger.info(f"Processing {len(md_files)} markdown files individually...", "pdf")

            # Remove existing output directory to ensure clean rebuild
            if self.output_dir.exists():
                self.logger.info(f"Clearing existing output directory: {self.output_dir}", "pdf")
                shutil.rmtree(self.output_dir)

            # Create fresh output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate individual PDFs
            generated_pdfs = []
            total_files = len(md_files)
            for i, md_file in enumerate(md_files, 1):
                # Only log every 10th file or first/last to reduce log spam
                if i == 1 or i == total_files or i % 10 == 0:
                    self.logger.info(f"Processing {md_file.name} ({i}/{total_files})...", "pdf")
                try:
                    pdf_file = self.generate_individual_pdf(md_file)
                    if pdf_file.exists():
                        file_size = pdf_file.stat().st_size / 1024  # KB
                        # Only log success for every 10th file or first/last to reduce spam
                        if i == 1 or i == total_files or i % 10 == 0:
                            self.logger.success(f"Created {pdf_file.name} ({file_size:.1f} KB)", "pdf")
                        generated_pdfs.append(pdf_file)
                    else:
                        self.logger.error(f"PDF was not created for {md_file.name}", "pdf")
                except Exception as e:
                    self.logger.error(f"Error processing {md_file.name}: {e}", "pdf")
            
            self.logger.success(f"Generated {len(generated_pdfs)} PDF files", "pdf")
            return generated_pdfs
            
        except Exception as e:
            self.logger.error(f"Error generating individual PDFs: {e}", "pdf")
            raise
        finally:
            # Cleanup temporary files
            self.cleanup_temp_files()


def main():
    """Main function to generate A4 document PDF."""
    parser = argparse.ArgumentParser(description='Generate A4 PDF document from markdown files')
    parser.add_argument('--input-dir', '-i', help='Input directory containing markdown files', 
                       default=None)
    parser.add_argument('--output-dir', '-o', help='Output directory for generated PDFs (default: created/)', 
                       default=None)
    parser.add_argument('--config', '-c', help='Configuration YAML file (default: config/presentation.yaml)',
                       default=None)
    parser.add_argument('--no-background', action='store_true', help='Generate PDFs without background images')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Setup logging
        logging_config = {}
        if Path("config/logging.yaml").exists():
            import yaml
            with open("config/logging.yaml", 'r', encoding='utf-8') as f:
                logging_config = yaml.safe_load(f) or {}
        
        logger = logging_manager.setup_logging(logging_config)
        
        # Create generator and run
        generator = DocumentPDFGenerator(
            config_file=args.config,
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        pdf_files = generator.generate_document_pdf()
        
        if pdf_files:
            logger.success(f"A4 PDF generation completed successfully!", "pdf")
            logger.success(f"Generated {len(pdf_files)} PDF files in {generator.output_dir}/", "pdf")
        else:
            logger.error("No PDF files were generated!", "pdf")
            return 1
            
    except Exception as e:
        logger = logging_manager.get_logger()
        logger.error(f"Error generating A4 document PDF: {e}", "pdf")
        if args.verbose:
            import traceback
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())