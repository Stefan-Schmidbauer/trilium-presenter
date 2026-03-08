# Trilium Organization Guide

How to structure your presentations in Trilium Notes for easy content management and reuse.

## Overview

Instead of creating presentations from scratch each time, build a **library of reusable slides** that can be assembled into different presentations. This guide explains a professional workflow using Trilium's cloning feature.

**Key Concept**: Separate your content library (Master) from your finished presentations (Sets). Use Trilium's **clone feature** (🔗) to reuse slides across multiple presentations while maintaining a single source of truth.

## The Main Areas

Your Trilium structure needs two essential areas, plus optional helpers:

```
📁 Presentations
├── 📁 Master        (Your content library - essential)
├── 📁 Sets          (Finished presentations - essential)
├── 📁 Templates     (Reusable layouts - optional)
└── 📁 Themes        (Visual organization - optional, Trilium-specific)
```

### 1. Master - Your Slide Library

The **Master** area is your central repository where all original slides live, organized by topics.

```
📁 Master
├── 📁 Topic A
│   ├── 📄 Slide - A1 🔗
│   ├── 📄 Slide - A2 🔗
│   └── 📄 Handout - HA1 🔗
├── 📁 Topic B
│   ├── 📄 Slide - B1 🔗
│   └── 📄 Slide - B2 🔗
├── 📁 Topic C
│   ├── 📄 Slide - C1 🔗
│   ├── 📄 Slide - C2 🔗
│   └── 📄 Slide - C3 🔗
└── 📄 Images 🔗
```

**Purpose**:

- Single source of truth - edit once, update everywhere
- Organized by themes or topics
- Contains both slides and handouts
- The 🔗 symbol indicates a cloned note — both the original and the clone show this symbol. Clones are not copies but references to the same note, so editing one updates all instances.

**Images Folder**: Contains all images used across slides. Clone this folder into each presentation set so all slides can access the images.

### 2. Templates - Reusable Layouts (Optional)

The **Templates** area contains special slides used in most presentations that need customization for each one. This is a Trilium organizational convenience, not required by the export tool.

```
📁 Templates
├── 📄 Title
├── 📄 Agenda
└── 📄 Contact
```

**Common Templates**:

- **Title**: Title slide with presentation name, date, author
- **Agenda**: Overview of topics covered
- **Contact**: Contact information, links, resources

**Important**: The templates are used to create new notes in the sets folder because each presentation needs its own unique version with specific content.

### 3. Themes - Visual Organization (Optional)

The **Themes** area contains Trilium-specific theme configurations for visual organization in the tree view.

```
📁 Themes
└── 📄 TreeLine
```

**Purpose**: Controls colored vertical lines in Trilium's tree view to help visually identify which slides belong to which topic. This is Trilium-specific and not part of exported presentations.

### 4. Sets - Finished Presentations

The **Sets** area contains your actual presentations, assembled from Master slides using clones.

```
📁 Sets
├── 📁 Presentation - Beginner
│   ├── 📁 Slides - Presentation Beginner
│   │   ├── 📄 Title (unique - no 🔗)
│   │   ├── 📄 Agenda (unique - no 🔗)
│   │   ├── 📄 A1 🔗 (cloned from Master)
│   │   ├── 📄 A2 🔗 (cloned from Master)
│   │   ├── 📄 B1 🔗 (cloned from Master)
│   │   ├── 📄 C1 🔗 (cloned from Master)
│   │   ├── 📄 C2 🔗 (cloned from Master)
│   │   ├── 📄 Contact 🔗 (cloned - same contact everywhere)
│   │   └── 📄 Images 🔗 (cloned from Master)
│   └── 📁 Handouts - Presentation Beginner
│       ├── 📄 HA1 🔗 (cloned from Master)
│       └── 📄 Images 🔗 (cloned from Master)
│
└── 📁 Presentation - Advanced
    └── 📁 Slides - Presentation Advanced
        ├── 📄 Title (unique - no 🔗)
        ├── 📄 Agenda (unique - no 🔗)
        ├── 📄 A2 🔗 (cloned from Master)
        ├── 📄 B2 🔗 (cloned from Master)
        ├── 📄 C2 🔗 (cloned from Master)
        ├── 📄 C3 🔗 (cloned from Master)
        ├── 📄 Contact 🔗 (cloned - same contact everywhere)
        └── 📄 Images 🔗 (cloned from Master)
```

**Structure of Each Set**:

- **Slides folder**: Contains cloned slides for HTML presentation export
- **Handouts folder** (optional): Contains cloned handouts for PDF document export
- **Images**: Cloned from Master, provides access to all images

**Why Separate Slides and Handouts?**

- Different export targets: Slides → HTML presentation, Handouts → PDF document
- Handouts can have more detailed content than slides
- Allows selective export

## Understanding the Clone Symbol 🔗

The **🔗 (link) symbol** in Trilium indicates a **cloned note**:

- **With 🔗**: The note is a clone - it shares content with the original in Master
- **Without 🔗**: The note is unique to this presentation (like Title, Agenda)

**When you edit a cloned note**: The change appears in ALL clones and in the Master. This is the power of the system - fix a typo once, it updates everywhere.

**Clone or unique - your choice**: Some slides like Contact can be cloned (same everywhere) or unique (different per presentation). The export works the same either way - it simply reads the content from Trilium regardless of whether it's a clone or not.

## Step-by-Step: Creating a Presentation

### Step 1: Build Your Master Library

Organize your content in Master by topics:

1. Create topic folders (e.g., "Topic A", "Topic B")
2. Create slides within each topic
3. Add images to the Images folder
4. Create handouts for detailed documentation (optional)

**Naming tip**: Use consistent prefixes like "Slide -" and "Handout -" for easy identification.

**Automation tip**: If you use Claude Code, the trilium-content-generator agent can automatically create structured content in your Master library. See [Claude Code Integration](CLAUDE_INTEGRATION.md) for details.

### Step 2: Create a New Presentation Set

When you need a new presentation:

1. Create a new folder under Sets (e.g., "Presentation - Workshop")
2. Create a subfolder: "Slides - Presentation Workshop"
3. (Optional) Create another subfolder: "Handouts - Presentation Workshop"

### Step 3: Clone Slides from Master

Use Trilium's clone feature to add slides:

1. Navigate to a slide in Master (e.g., Master/Topic A/Slide - A1)
2. **Right-click** → **Clone note** or **drag and drop it** with the mouse
3. Place the clone in your Set's Slides folder
4. Repeat for all slides you need

**Result**: The slide appears in both locations with a 🔗 icon. Editing in either place updates both.

### Step 4: Clone the Images Folder

Clone the entire Images folder from Master into your Slides Folder:

1. Right-click on Master/Images
2. Clone note
3. Place in your Slides folder)

**Result**: Your presentation has access to all images.

### Step 5: Add Unique Slides

Create presentation-specific content:

**Title Slide**:

1. Right click on your Slides folder, click **Insert child note** and chosse the Title Template.
2. Move the note within the Sets folder to the top
3. Fill the slide

This note is unique (no 🔗) - each presentation has its own

**Agenda, Contact Slide**, see Title Slide

### Step 6: Clone Handouts (Optional)

If you need handouts:

1. Clone handout notes from Master topics
2. Place in Set's Handouts folder
3. You might have 100 handouts in Master but only need 10 for a specific presentation
4. Clone the images folder in the handouts folder.

## Exporting Your Presentation

### Export HTML Presentation

1. Launch Trilium Presenter: `./start.sh`
2. Go to **Export** tab
3. Select your Set's **Slides folder** (e.g., "Slides - Presentation Beginner")
4. Click "Export Selected Subtree"
5. Go to **Create** tab, select the exported folder, generate HTML

### Export PDF Handouts

1. In the **Export** tab
2. Select your Set's **Handouts folder** (e.g., "Handouts - Presentation Beginner")
3. Click "Export Selected Subtree"
4. Go to **Create** tab, select the exported folder, generate PDF

## Clone vs. Unique: When to Use Each

### Use Clone (🔗) When:

- **Content is shared** across multiple presentations
- You want **automatic updates** when editing the original
- Examples: Standard slides from Master, images, common handouts

**How**: Right-click → Clone note

### Use Unique (no 🔗) When:

- **Content is unique** to one presentation
- Each presentation needs **different content**
- Examples: Title slides, agenda slides, presentation-specific notes

**How**: Create new note (no cloning)

## Best Practices

### 1. Keep Master Organized

- Group related slides in topic folders
- Use clear, descriptive names: "Slide - Python Variables" not just "Variables". The name does not appear on the slide.
- Maintain consistent formatting across all slides

### 2. Make Sets Self-Contained

Each Set should include:

- All needed slides (copied/cloned from Master)
- Images folder (copied/cloned from Master)
- Set-specific slides (Title, Agenda)
- Only relevant handouts (not all)

### 3. Edit in Master, Not in Sets

**Rule**: Always edit content in the Master area.

**Why**: Clones update automatically. Editing in Master updates all presentations that use that slide.

**Exception**: Set-specific content (Title, Agenda) only exists in that Set, so edit it there.

### 4. Organize Master by Topic, Not by Presentation

Organize by reusable topics, not by specific presentations. This allows mixing and matching slides for different audiences.

**Example**: Use topic folders like "Basics", "Intermediate", "Advanced" rather than "Beginner Workshop Slides", "Advanced Workshop Slides".

## Summary

The Master/Templates/Sets approach provides:

- **Reusable content** - Write once, use in multiple presentations
- **Easy updates** - Fix once in Master, updates everywhere
- **Flexible assembly** - Mix and match slides for different audiences
- **Clean organization** - Clear separation between library and presentations
- **Efficient workflow** - No duplicate content maintenance

**Remember**: Master is your library, Sets are your presentations. Clone from Master to Sets, edit in Master, export from Sets.

## Next Steps

- **[Getting Started Guide](GETTING_STARTED.md)** - Learn how to export and generate presentations
- **[Markdown Syntax](MARKDOWN_SYNTAX.md)** - Learn how to format slide content
- **[Customization Guide](CUSTOMIZATION.md)** - Customize backgrounds and styles (advanced)
- **[Claude Code Integration](CLAUDE_INTEGRATION.md)** - Automate content creation with Claude Code (optional)
