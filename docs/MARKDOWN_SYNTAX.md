# Markdown Syntax for Presentations

Guide to the special Markdown syntax supported by Trilium Presenter for creating presentations.

## Overview

Trilium Presenter uses **Pandoc-compatible syntax** for all presentation elements. This modern, widely-supported syntax ensures compatibility with other markdown tools and follows industry standards.

## Pandoc Syntax

Pandoc's fenced divs with CSS classes provide a clean, standardized way to structure presentations.

### Column Layouts

Create multi-column layouts for side-by-side content:

```markdown
::: {.columns}
::: {.column}
Left column content

- Item 1
- Item 2
- Item 3
:::
::: {.column}
Right column content

- Item A
- Item B
- Item C
:::
:::
```

**Features:**
- Automatic column counting (no need to specify number)
- Responsive design adapts to screen size
- Nested content fully supported

**Example - Two Column Layout:**

```markdown
::: {.columns}
::: {.column}
## Problem

- High complexity
- Low performance
- Difficult maintenance
:::
::: {.column}
## Solution

- Modular architecture
- Optimized algorithms
- Clean code structure
:::
:::
```

**Example - Three Column Layout:**

```markdown
::: {.columns}
::: {.column}
### Phase 1
Planning and design
:::
::: {.column}
### Phase 2
Implementation
:::
::: {.column}
### Phase 3
Testing and deployment
:::
:::
```

### Presenter Notes

Add notes that are only visible in presenter mode (not in exported PDFs):

```markdown
::: {.notes}
These are presenter notes

- Remind audience about previous topic
- Emphasize key points
- Mention upcoming demo
:::
```

**Features:**
- Only visible in HTML presenter mode
- Not included in PDF exports
- Support for markdown formatting
- Can include lists, bold text, etc.

**Example:**

```markdown
## Main Content

This is what the audience sees.

::: {.notes}
**Remember to:**
- Speak slowly
- Show the demo
- Ask for questions

Time: 5 minutes
:::
```

### Page Breaks (PDF Only)

Force a page break in PDF documents:

```markdown
::: {.page-break}
:::
```

**Alternative syntax (without hyphen):**

```markdown
::: {.pagebreak}
:::
```

**Example:**

```markdown
## Section 1

Content for first page.

::: {.page-break}
:::

## Section 2

Content for second page.
```

## Standard Markdown Features

All standard Markdown syntax is supported:

### Headings

```markdown
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
```

### Lists

**Unordered:**
```markdown
- Item 1
- Item 2
  - Nested item
  - Another nested item
- Item 3
```

**Ordered:**
```markdown
1. First item
2. Second item
3. Third item
```

### Text Formatting

```markdown
**Bold text**
*Italic text*
***Bold and italic***
`Code inline`
~~Strikethrough~~
```

### Links and Images

```markdown
[Link text](https://example.com)
![Alt text](image.png)
![Tiny image: alt text](small-image.png)
```

### Code Blocks

````markdown
```python
def hello():
    print("Hello, World!")
```
````

### Blockquotes

```markdown
> This is a quote
> It can span multiple lines
```

### Tables

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

### Horizontal Rules

```markdown
---
```

## Image Handling

### CSS Class-Based Sizing (Recommended)

Use Pandoc attribute syntax `{.class}` for precise image sizing:

```markdown
![Description](Bilder/image.svg){.img-tiny}
![Description](Bilder/image.svg){.img-small}
![Description](Bilder/image.svg){.img-medium}
![Description](Bilder/image.svg){.img-large}
![Description](Bilder/image.svg){.img-xlarge}
![Description](Bilder/image.svg){.img-imgonly}
![Description](Bilder/image.svg){.img-fill}
![Description](Bilder/image.svg){.img-fit}
```

**Image Size Reference (Full HD 1920x1080):**
- `.img-tiny`: 4rem = 64px (~15% slide height) - Icons, small graphics
- `.img-small`: 8rem = 128px (~30% slide height) - Small images
- `.img-medium`: 12rem = 192px (~45% slide height) - Medium diagrams
- `.img-large`: 24rem = 384px (~90% slide height) - Large diagrams
- `.img-xlarge`: 30rem = 480px - Maximum predefined height
- `.img-imgonly`: 500px (fixed) - Image-only slides
- `.img-fill`: 100% width and height - Fills entire area
- `.img-fit`: Responsive fit - Optimally fits available space

### Centering Images

Combine size classes with `.center`:

```markdown
![Description](Bilder/logo.svg){.img-medium .center}
![Self Attention](Bilder/diagram.svg){.img-imgonly .center}
```

### Size-Based Auto-Sizing (Alternative)

Images are automatically sized based on their filename:

```markdown
![Description](attachment_small.png)    # Automatically sized as small
![Description](attachment_medium.png)   # Automatically sized as medium
![Description](attachment_large.png)    # Automatically sized as large
```

### Alt-Text Based Sizing (Alternative)

Override automatic sizing using alt text:

```markdown
![tiny: This is a tiny image](image.png)
![small: This is a small image](image.png)
![medium: This is a medium image](image.png)
![large: This is a large image](image.png)
![full: This is a full-width image](image.png)
```

## Text Centering

### Center Text

Use Pandoc attributes to center text blocks:

```markdown
This is centered text.
{.center}

Alternative centering.
{.text-center}
```

### Center Headings

```markdown
# Centered Main Heading
{.center}

## Centered Subheading
{.center}
```

### Center Block Elements

```markdown
- List Point 1
- List Point 2
{.center}
```

## Advanced Formatting

### Combined Styles

Combine multiple CSS classes for complex layouts:

```markdown
# Large, centered image with text

![Main Graphic](Bilder/overview.svg){.img-large .center}

This is centered text below the image.
{.center}
```

### Multi-Column with Centered Images

```markdown
::: {.columns}
::: {.column}

![Logo](Bilder/logo1.svg){.img-medium .center}

**Product A**

:::

::: {.column}

![Logo](Bilder/logo2.svg){.img-medium .center}

**Product B**

:::
:::
```

### Multiple CSS Classes

You can apply multiple classes to any element:

```markdown
![Image](Bilder/test.svg){.img-large .center .special-class}

Text with multiple classes.
{.center .highlight .important}
```

## Best Practices

### Keep Presenter Notes Concise

```markdown
::: {.notes}
- Brief bullet points
- Key reminders only
- Time estimates
:::
```

### Use Semantic Headings

```markdown
# Presentation Title (h1)
## Section Title (h2)
### Subsection (h3)
```

### Optimize Images

- **Prefer SVG**: For diagrams and logos - scales perfectly at Full HD
- **Use Appropriate Size Classes**:
  - Diagrams/Charts: `.img-medium` or `.img-large`
  - Full-slide graphics: `.img-imgonly` or `.img-xlarge`
  - Icons/Logos: `.img-tiny` or `.img-small`
- **Consistent Formats**: SVG for graphics, PNG for screenshots
- **Descriptive Alt Texts**: For accessibility
- **Full HD Optimization**: Test on 1920x1080 display for best results

## Examples

### Complete Slide Example

```markdown
# Introduction to Python

::: {.columns}
::: {.column}
## What is Python?

- High-level language
- Easy to learn
- Versatile
:::
::: {.column}
## Why Python?

- Readable syntax
- Large ecosystem
- Great community
:::
:::

::: {.notes}
**Talking points:**
- Emphasize ease of learning
- Mention popular frameworks
- Show code example next

Duration: 3 minutes
:::

::: {.page-break}
:::

## Code Example

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
```
```

### Complex Multi-Column Example

```markdown
# Project Architecture

::: {.columns}
::: {.column}
### Frontend
- React
- TypeScript
- Tailwind CSS
:::
::: {.column}
### Backend
- Python
- FastAPI
- PostgreSQL
:::
::: {.column}
### DevOps
- Docker
- GitHub Actions
- AWS
:::
:::

::: {.notes}
Explain how each component interacts. Show deployment diagram on next slide.
:::
```

## Technical Details

### File Paths

- **Images from Export**: `Bilder/filename.svg` (relative to export directory)
- **Assets**: `assets/filename.png` or `/assets/filename.svg`
- **Automatic Path Correction**: The system automatically corrects paths for HTML structure

### Supported Image Formats

- **SVG**: Recommended for scalable graphics
- **PNG**: For photos with transparency
- **JPG**: For photos without transparency
- **WebP, GIF, BMP, TIFF**: Also supported

### CSS Classes Overview

**Display Resolution:** Optimized for Full HD (1920x1080)

```css
/* Image Sizes (Full HD optimized) */
.img-tiny        /* 64px - ~15% slide height */
.img-small       /* 128px - ~30% slide height */
.img-medium      /* 192px - ~45% slide height */
.img-large       /* 384px - ~90% slide height */
.img-xlarge      /* 480px - maximum predefined height */
.img-imgonly     /* 500px - for image-only slides */
.img-fill        /* 100% width and height */
.img-fit         /* Responsive fit */

/* Centering */
.center
.text-center
.block-center

/* Column Layouts (automatically generated) */
.columns
.columns-2, .columns-3, .columns-4
.column
.column-1, .column-2, .column-3, .column-4

/* PDF-specific */
.page-break
.pagebreak
```

### Responsive Design

The system is automatically responsive:

- **Desktop (Full HD 1920x1080)**: Optimal display - all columns side by side, images at defined sizes
- **Tablet/Mobile (< 768px)**: Columns automatically stack vertically
- **Images**: Scale automatically using rem units and remain readable
- **Breakpoint**: 768px width triggers mobile layout

**Note:** Image sizes use `rem` units (except `.img-imgonly`) for responsive scaling:
- 1rem = 16px (default browser font size)
- Scales proportionally if user changes browser font size
- `.img-imgonly` uses fixed 500px for consistent presentation display

## Syntax Reference

| Element | Syntax | Description |
|---------|--------|-------------|
| Columns | `::: {.columns}` ... `:::` | Multi-column layout container |
| Column | `::: {.column}` ... `:::` | Individual column within layout |
| Notes | `::: {.notes}` ... `:::` | Presenter notes (not in PDF) |
| Page Break | `::: {.page-break}` ... `:::` | Force page break in PDF |
| Page Break (alt) | `::: {.pagebreak}` ... `:::` | Alternative spelling |
| Image Classes | `{.img-size .center}` | Size and position images |
| Text Centering | `{.center}` | Center text or block elements |

## Support

For issues or questions about Markdown syntax:

- Check [examples](../export/) directory for working examples
- Open an issue on [GitHub](https://github.com/Stefan-Schmidbauer/trilium-presenter/issues)
