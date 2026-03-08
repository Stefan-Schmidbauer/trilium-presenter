#!/usr/bin/env python3
"""
PDF Background Processor
Adds background images to existing PDF files using pdftk and ImageMagick.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import yaml

# Import unified logging system
try:
    from . import logging_manager
except ImportError:
    import logging_manager


class PDFBackgroundProcessor:
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the PDF background processor."""
        self.config = config or {}
        self.pdf_input_dir = Path(self.config.get('pdf', {}).get('output_dir', 'created'))
        self.background_svg = Path('config/pdf_templates/assets/background.svg')
        self.temp_dir = None
        self.logger = logging_manager.get_logger()
        
        # Check required tools
        self._check_dependencies()
        
    def _check_dependencies(self):
        """Check if required tools (pdftk, convert) are available."""
        tools = {
            'pdftk': 'PDF manipulation tool',
            'convert': 'ImageMagick for SVG conversion'
        }
        
        missing_tools = []
        for tool, description in tools.items():
            try:
                result = subprocess.run(['which', tool], capture_output=True, text=True)
                if result.returncode != 0:
                    missing_tools.append(f"{tool} ({description})")
            except Exception:
                missing_tools.append(f"{tool} ({description})")
        
        if missing_tools:
            self.logger.error(f"Missing required tools: {', '.join(missing_tools)}", "pdf")
            raise RuntimeError(f"Missing dependencies: {', '.join(missing_tools)}")
        
    
    def setup_temp_structure(self):
        """Create temporary directory for PDF processing."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix='pdf_background_'))
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def convert_svg_to_pdf(self) -> Path:
        """Convert SVG background to PDF format."""
        if not self.background_svg.exists():
            self.logger.error(f"Background SVG not found: {self.background_svg}", "pdf")
            raise FileNotFoundError(f"Background SVG not found: {self.background_svg}")
        
        background_pdf = self.temp_dir / 'background.pdf'
        
        # Use ImageMagick convert to create A4 sized background PDF
        cmd = [
            'convert',
            '-background', 'white',
            '-density', '300',  # High DPI for quality
            '-page', 'A4',     # A4 page size
            str(self.background_svg),
            str(background_pdf)
        ]
        
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.logger.error(f"SVG conversion failed: {result.stderr}", "pdf")
                raise RuntimeError(f"SVG conversion failed: {result.stderr}")
            
            if not background_pdf.exists():
                raise RuntimeError("Background PDF was not created")
            
            self.logger.success(f"Successfully converted SVG to PDF: {background_pdf.name}", "pdf")
            return background_pdf
            
        except subprocess.TimeoutExpired:
            self.logger.error("SVG conversion timed out", "pdf")
            raise RuntimeError("SVG conversion timed out")
    
    def find_pdf_files(self) -> List[Path]:
        """Find all PDF files in the input directory."""
        if not self.pdf_input_dir.exists():
            self.logger.error(f"PDF input directory not found: {self.pdf_input_dir}", "pdf")
            return []
        
        pdf_files = list(self.pdf_input_dir.glob("*.pdf"))
        self.logger.info(f"Found {len(pdf_files)} PDF files to process", "pdf")
        
        # Only log first few files to reduce spam
        if pdf_files:
            shown_count = min(3, len(pdf_files))
            for i, pdf_file in enumerate(pdf_files[:shown_count]):
            if len(pdf_files) > shown_count:
        
        return pdf_files
    
    def add_background_to_pdf(self, pdf_file: Path, background_pdf: Path) -> Path:
        """Add background to a single PDF file using pdftk."""
        output_file = self.temp_dir / f"processed_{pdf_file.name}"
        
        # Use pdftk to combine background with content PDF
        # The background PDF is placed behind (underlay) the content
        cmd = [
            'pdftk',
            str(pdf_file),
            'background',
            str(background_pdf),
            'output',
            str(output_file)
        ]
        
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                self.logger.error(f"pdftk failed for {pdf_file.name}: {result.stderr}", "pdf")
                raise RuntimeError(f"pdftk failed: {result.stderr}")
            
            if not output_file.exists():
                raise RuntimeError(f"Processed PDF was not created: {output_file}")
            
            self.logger.success(f"Successfully added background to {pdf_file.name}", "pdf")
            return output_file
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"pdftk timed out for {pdf_file.name}", "pdf")
            raise RuntimeError(f"pdftk timed out for {pdf_file.name}")
    
    def replace_original_pdfs(self, processed_files: List[tuple], create_backups: bool = False) -> int:
        """Replace original PDFs with processed versions."""
        success_count = 0
        
        for original_file, processed_file in processed_files:
            try:
                # Create backup of original only if requested
                if create_backups:
                    backup_file = original_file.with_suffix('.pdf.backup')
                    if backup_file.exists():
                        backup_file.unlink()  # Remove old backup
                    
                    shutil.copy2(original_file, backup_file)
                
                # Replace original with processed version
                shutil.copy2(processed_file, original_file)
                
                # Verify the replacement was successful
                if original_file.exists() and original_file.stat().st_size > 0:
                    success_count += 1
                    new_size = original_file.stat().st_size / 1024
                    self.logger.success(f"Replaced {original_file.name} ({new_size:.1f} KB)", "pdf")
                else:
                    self.logger.error(f"Failed to replace {original_file.name}", "pdf")
                    
            except Exception as e:
                self.logger.error(f"Error replacing {original_file.name}: {e}", "pdf")
        
        return success_count
    
    def process_all_pdfs(self, skip_backup: bool = False, create_backups: bool = False) -> int:
        """Main processing method: add backgrounds to all PDF files."""
        self.logger.section("Starting PDF background processing", "pdf")
        
        try:
            # Setup
            self.setup_temp_structure()
            
            # Convert background SVG to PDF
            background_pdf = self.convert_svg_to_pdf()
            
            # Find PDF files to process
            pdf_files = self.find_pdf_files()
            if not pdf_files:
                self.logger.warning("No PDF files found to process", "pdf")
                return 0
            
            # Process each PDF
            processed_files = []
            for pdf_file in pdf_files:
                try:
                    processed_file = self.add_background_to_pdf(pdf_file, background_pdf)
                    processed_files.append((pdf_file, processed_file))
                except Exception as e:
                    self.logger.error(f"Failed to process {pdf_file.name}: {e}", "pdf")
            
            if not processed_files:
                self.logger.error("No PDF files were successfully processed", "pdf")
                return 0
            
            # Replace originals with processed versions
            if not skip_backup:
                success_count = self.replace_original_pdfs(processed_files, create_backups)
                
                self.logger.success(f"PDF background processing completed!", "pdf")
                self.logger.success(f"Successfully processed {success_count}/{len(pdf_files)} PDF files", "pdf")
                
                return success_count
            else:
                # Just show what would be done
                self.logger.info(f"Would process {len(processed_files)} PDF files (dry run)", "pdf")
                for original, processed in processed_files:
                    self.logger.info(f"  - {original.name} → background added", "pdf")
                return len(processed_files)
                
        except Exception as e:
            self.logger.error(f"Error in PDF background processing: {e}", "pdf")
            raise
        finally:
            self.cleanup_temp_files()
    
    def restore_backups(self) -> int:
        """Restore PDF files from backups."""
        if not self.pdf_input_dir.exists():
            self.logger.error(f"PDF directory not found: {self.pdf_input_dir}", "pdf")
            return 0
        
        backup_files = list(self.pdf_input_dir.glob("*.pdf.backup"))
        if not backup_files:
            self.logger.warning("No backup files found", "pdf")
            return 0
        
        self.logger.info(f"Found {len(backup_files)} backup files to restore", "pdf")
        
        restored_count = 0
        for backup_file in backup_files:
            original_file = backup_file.with_suffix('')  # Remove .backup extension
            
            try:
                if original_file.exists():
                    # Move current file to temp name
                    temp_name = original_file.with_suffix('.pdf.current')
                    shutil.move(original_file, temp_name)
                
                # Restore backup
                shutil.move(backup_file, original_file)
                
                # Remove temp file if restore was successful
                if temp_name.exists():
                    temp_name.unlink()
                
                self.logger.success(f"Restored {original_file.name} from backup", "pdf")
                restored_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to restore {original_file.name}: {e}", "pdf")
        
        self.logger.success(f"Restored {restored_count}/{len(backup_files)} files from backups", "pdf")
        return restored_count


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='Add background images to PDF files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--restore', action='store_true', help='Restore PDF files from backups')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    try:
        # Setup logging
        logging_config = {}
        if Path("config/logging.yaml").exists():
            with open("config/logging.yaml", 'r', encoding='utf-8') as f:
                logging_config = yaml.safe_load(f) or {}
        
        logger = logging_manager.setup_logging(logging_config)
        
        # Load config if provided
        config = {}
        if args.config and Path(args.config).exists():
            with open(args.config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        
        # Create processor and run
        processor = PDFBackgroundProcessor(config)
        
        if args.restore:
            result = processor.restore_backups()
            if result > 0:
                logger.success(f"Successfully restored {result} PDF files from backups!", "pdf")
            else:
                logger.warning("No files were restored", "pdf")
        else:
            result = processor.process_all_pdfs(skip_backup=args.dry_run)
            if result > 0:
                if args.dry_run:
                    logger.info(f"Dry run complete - would process {result} PDF files", "pdf")
                else:
                    logger.success(f"Successfully processed {result} PDF files with backgrounds!", "pdf")
            else:
                logger.warning("No PDF files were processed", "pdf")
        
        return 0 if result > 0 else 1
        
    except Exception as e:
        logger = logging_manager.get_logger()
        logger.error(f"Error in PDF background processing: {e}", "pdf")
        if args.verbose:
            import traceback
        return 1


if __name__ == "__main__":
    exit(main())