# Customization Guide

How to customize backgrounds, styles, and templates in Trilium Presenter.

**⚠️ Warning**: This guide is for **advanced users** who are comfortable with HTML, CSS, and SVG. If you're not familiar with these technologies, it's best to use the default settings.

## Overview

Trilium Presenter uses **standardized formats** for optimal display quality:
- **HTML Presentations**: 16:9 aspect ratio, Full HD (1920x1080px) - optimized for modern projectors and displays
- **PDF Documents**: A4 format (210x297mm) - standard paper size for printing and digital distribution

You can customize:

1. **Background images** - Replace SVG backgrounds for presentations and PDFs
2. **CSS styles** - Customize colors, fonts, and layout
3. **HTML templates** - Modify presentation structure (very advanced)

## Background Images

### HTML Presentations (16:9 Full HD)

Background images for HTML presentations are in:

```
config/html_templates/assets/
├── title-background.svg       (Title slide)
└── content-background.svg     (Content slides)
```

**Format Requirements**:
- **Resolution**: 1920x1080 pixels (Full HD)
- **Aspect Ratio**: 16:9
- **Format**: SVG (vector graphics) recommended for crisp display at any scale

**To customize**:

1. Create your own SVG files matching the 1920x1080 resolution
2. Replace the existing files:
   ```bash
   cp your-title.svg config/html_templates/assets/title-background.svg
   cp your-content.svg config/html_templates/assets/content-background.svg
   ```
3. Regenerate your presentation

**Design Tips**:

- Keep text areas clear of complex graphics
- Use consistent branding across both backgrounds
- Test on an actual projector if possible - colors may appear differently
- Consider contrast: dark text on light backgrounds or vice versa
- Leave margins around edges (safe area: ~100px from borders)

### PDF Documents (A4 Format)

Background image for PDF documents is in:

```
config/pdf_templates/assets/background.svg
```

**Format Requirements**:
- **Size**: A4 (210x297mm)
- **Orientation**: Portrait
- **Format**: SVG (vector graphics) recommended

**To customize**:

1. Create your own SVG file matching A4 dimensions (210x297mm)
2. Replace the existing file:
   ```bash
   cp your-background.svg config/pdf_templates/assets/background.svg
   ```
3. Regenerate your PDF

**Design Tips**:

- Design for A4 size (210x297mm or 8.27x11.69 inches)
- Leave 15-20mm margins for printing (bleed area)
- Consider grayscale printing if distributing printed copies
- Test print before finalizing - screen colors differ from print
- Keep important elements away from page edges

### Automatic Setup

The installer (`./install.py`) automatically copies example backgrounds if the files don't exist. You can customize them afterwards.

## CSS Customization

**⚠️ Note**: Only customize CSS if you understand how CSS works. Incorrect changes can break the presentation layout.

### CSS File Locations

CSS files for HTML presentations are in:

```
config/html_templates/css/
├── base.css              (Layout, fonts, general styles)
├── title-slide.css       (Title slide styling)
├── content-slides.css    (Content slide styling)
└── navigation.css        (Navigation controls)
```

All files are automatically loaded when you generate a presentation.

### Simple Customizations

**Change colors** - Edit `base.css` or `title-slide.css`:

```css
h1 {
  color: #1e3a8a; /* Change heading color */
}
```

**Change fonts** - Edit `base.css`:

```css
html,
body {
  font-family: "Arial", sans-serif; /* Change font */
}
```

**Change heading sizes** - Edit `title-slide.css` or `content-slides.css`:

```css
h1 {
  font-size: 3rem; /* Make headings larger or smaller */
}
```

### After Making Changes

1. Save your CSS files
2. Regenerate your presentation (Tab 2 in GUI)
3. Refresh your browser to see changes

## HTML Templates

**⚠️ Very Advanced**: Only modify HTML templates if you are experienced with HTML and web development.

There are two HTML templates:

| File | Purpose |
| ---- | ------- |
| `config/html_templates/html/slide_template.html` | **Main slide template** — controls slide structure and layout |
| `config/html_templates/html/simple_presenter.html` | Presenter view — shows notes, slide list, current/next slide |

The slide template contains placeholders like `{{TITLE}}`, `{{CONTENT}}`, `{{NAVIGATION}}`, `{{COUNTER}}`, etc. that are filled in during generation.

**If you must modify**:

- Make a backup first: `cp slide_template.html slide_template.html.backup`
- Don't remove placeholder variables like `{{TITLE}}`, `{{CONTENT}}`, `{{NAVIGATION}}`, `{{COUNTER}}`, `{{SLIDE_CLASS}}`, etc.
- Test thoroughly after changes

## PDF Styling

PDF document styling is controlled by:

```
config/pdf_templates/css/pdf_document.css
```

**Simple changes** you can make:

- Font size: Change `font-size: 11pt;` to another value
- Margins: Change `margin: 2cm;` in the `@page` section
- Font family: Change `font-family: 'Inter', sans-serif;`

**After making changes**: Regenerate your PDF document.

## Quick Reference

### File Locations

| What             | Where                                              |
| ---------------- | -------------------------------------------------- |
| HTML backgrounds | `config/html_templates/assets/*.svg`               |
| CSS styles       | `config/html_templates/css/*.css`                  |
| JavaScript       | `config/html_templates/js/*.js`                    |
| Slide template   | `config/html_templates/html/slide_template.html`   |
| Presenter view   | `config/html_templates/html/simple_presenter.html` |
| PDF background   | `config/pdf_templates/assets/background.svg`       |
| PDF styles       | `config/pdf_templates/css/pdf_document.css`        |
| PDF template     | `config/pdf_templates/html/pdf_template.html`      |

### Workflow After Changes

1. **Changed backgrounds** → Regenerate presentation (Tab 2)
2. **Changed CSS** → Regenerate presentation, then refresh browser
3. **Changed HTML template** → Regenerate presentation
4. **Changed PDF styles** → Regenerate PDF document

## Troubleshooting

### Backgrounds not appearing

**Check**:

- Files exist in `config/html_templates/assets/` or `config/pdf_templates/assets/`
- Files are valid SVG format
- Files have correct names

**Solution**: Run `./install.py` to copy example backgrounds if missing

### CSS changes not visible

**Check**:

- Did you save the CSS file?
- Did you regenerate the presentation?
- Did you refresh your browser (Ctrl+Shift+R)?

**Solution**: Regenerate presentation and hard-refresh browser

### Presentation layout broken

**Cause**: Invalid CSS or HTML changes

**Solution**:

- Restore from backup if you made one
- Or reinstall: Delete modified files and run `./install.py` to get defaults

## Next Steps

- **[Getting Started Guide](GETTING_STARTED.md)** - Learn how to generate presentations
- **[Markdown Syntax](MARKDOWN_SYNTAX.md)** - Learn how to format content
- **[Trilium Organization](TRILIUM_ORGANIZATION.md)** - Learn how to structure content
