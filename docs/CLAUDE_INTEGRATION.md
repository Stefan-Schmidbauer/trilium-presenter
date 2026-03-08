# Claude Code Integration

Automated content creation for Trilium Presenter using the trilium-content-generator agent.

## Overview

Trilium Presenter and Claude Code work together to automate the creation of educational content. While Trilium Presenter provides the GUI workflow for exporting, generating, and presenting content, Claude Code's **trilium-content-generator agent** can automatically create properly formatted German Folien (slides) or English worksheets directly in your Trilium instance.

## Prerequisites

- **Claude Code** installed and running
- **Trilium Notes** with ETAPI enabled
- **`.env` file** configured with your Trilium connection details:
  ```env
  TRILIUM_SERVER_URL=http://localhost:8080
  TRILIUM_ETAPI_TOKEN=your_token_here
  ```

The agent reads these credentials from your `.env` file to connect to Trilium's REST API (ETAPI).

## Setup

The agent definition is at `.claude/agents/trilium-content-generator.md`. It reads credentials from your `.env` file automatically - no additional setup needed.

## The trilium-content-generator Agent

### What It Does

The agent transforms source material (articles, documentation, training content) into structured Trilium notes with:

- Correct Markdown formatting for presentation slides or worksheets
- Proper hierarchy
- German Folien/Themenblätter or English slide/worksheet format
- special formatting

### When to Use It

**Use the agent** when:

- You have source material to transform into slides/worksheets
- You want to quickly populate your Master library
- You're creating new educational content from scratch

**Use the Trilium Notes GUI** when:

- You already have content in Trilium
- You want to export and present existing slides
- You're assembling presentations from your Master library

## How to Use

Simply tell Claude Code what you want to create:

```
"Create German presentation slides (Folien) from this article about Python functions. Parent Note ist 'Python'."
```

```
"Turn this training material into detailed English worksheets"
```

The agent will:

1. Read your `.env` file for Trilium credentials
2. Analyze the source material
3. Create structured notes in your Trilium instance
4. Format content appropriately (Folien vs. worksheet style)

## Integration with Master/Sets Workflow

Content created by the agent appears in your Trilium instance and integrates seamlessly with the Master/Sets organizational structure:

1. **Agent creates content** → New notes appear in Trilium (typically in Master area)
2. **Organize in Trilium** → Clone slides into Sets as needed
3. **Use Trilium Presenter GUI** → Export, create presentations, and present

The agent handles content creation; Trilium Presenter handles export and presentation.

## Technical Details

- **Connection**: Agent uses Trilium's ETAPI (REST API) via credentials in `.env`
- **Format**: Creates notes with Trilium-specific Markdown syntax
- **Hierarchy**: Automatically structures content with parent/child relationships
- **Images**: Handles image references compatible with Trilium's attachment system

## Next Steps

- **[Getting Started Guide](GETTING_STARTED.md)** - Install, configure, and use Trilium Presenter
- **[Trilium Organization](TRILIUM_ORGANIZATION.md)** - Learn the Master/Sets workflow
