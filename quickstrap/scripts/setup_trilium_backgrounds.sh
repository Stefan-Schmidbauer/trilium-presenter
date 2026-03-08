#!/bin/bash
# Post-Install Script: Setup Trilium-Presenter Background Assets
#
# This script copies example background SVG files to their target locations
# if they don't already exist (first-run setup).

echo "🎨 Setting up background assets..."

# Define background file pairs (target:source)
BACKGROUNDS=(
    "config/html_templates/assets/title-background.svg:config/html_templates/assets/title-background.example.svg"
    "config/html_templates/assets/content-background.svg:config/html_templates/assets/content-background.example.svg"
    "config/pdf_templates/assets/background.svg:config/pdf_templates/assets/background.example.svg"
)

# Copy example backgrounds if target doesn't exist
for bg_pair in "${BACKGROUNDS[@]}"; do
    IFS=':' read -r target source <<< "$bg_pair"

    if [ ! -f "$target" ]; then
        if [ -f "$source" ]; then
            echo "   Copying $(basename "$source") → $(basename "$target")"
            cp "$source" "$target"
        else
            echo "   ⚠️  Warning: $source not found"
        fi
    else
        echo "   ✓ Already exists: $(basename "$target")"
    fi
done

echo "✓ Background assets setup completed!"
exit 0
