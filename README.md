# MCP Server for HNPX Documents

An MCP (Model Context Protocol) server for working with HNPX (Hierarchical Narrative Planning XML) documents. This server provides tools for reading, editing, and analyzing structured fiction documents.

## What is HNPX?

HNPX is a hierarchical XML format for planning and writing fiction. It enables structured decomposition from book-level overview to atomic paragraph units with the following hierarchy:

```
book → chapter → sequence → beat → paragraph
```

Each element must have:
- A unique `id` attribute (6-character random string)
- A `<summary>` child element
- Specific attributes based on the element type

## Installation

1. Install the package dependencies:
```bash
pip install -e .
```

2. The server will be available as `mcp-hnpx` command.

## MCP Server Configuration

Add this server to your MCP configuration file (usually located at `~/.config/roo/mcp_settings.json` or similar):

```json
{
  "mcpServers": {
    "hnpx": {
      "command": "python",
      "args": ["-m", "mcp_hnpx.server"],
      "env": {}
    }
  }
}
```

## Available Tools

### Core Node Operations

#### `get_node`
Get a node by ID and read its attributes and summary.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `node_id` (string): ID of the node to retrieve

**Returns:** Node information including tag, attributes, summary, and text content (for paragraphs)

#### `get_node_context`
Get context for a node including siblings, parent, and parent's siblings.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `node_id` (string): ID of the node to get context for
- `include_text` (boolean, optional): Whether to include full text content (default: false)

**Returns:** Context information including parent, siblings, and parent's siblings

#### `edit_node_attributes`
Edit node attributes.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `node_id` (string): ID of the node to edit
- `attributes` (object): Dictionary of attributes to set

### Content Editing Operations

#### `set_node_children`
Replace a node's entire children list.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `node_id` (string): ID of the node to modify
- `children_xml` (string): XML string representing the new children

#### `append_node_children`
Append children to a node's existing children list.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `node_id` (string): ID of the node to modify
- `children_xml` (string): XML string representing the children to append

#### `remove_node`
Remove a node by ID.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `node_id` (string): ID of the node to remove

### Document Analysis Operations

#### `get_empty_containers`
Get first N container tags that need children populated.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `limit` (integer, optional): Maximum number of containers to return (default: 10)

**Returns:** List of container elements that need children

#### `search_nodes`
Search for nodes matching criteria.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `tag` (string, optional): Element tag to search for
- `attributes` (object, optional): Attributes to match
- `text_contains` (string, optional): Text content to search for
- `summary_contains` (string, optional): Summary content to search for

**Returns:** List of matching nodes

#### `validate_document`
Validate HNPX document against schema.

**Parameters:**
- `file_path` (string): Path to the HNPX file

**Returns:** Validation result with any errors

#### `get_document_stats`
Get statistics about the HNPX document.

**Parameters:**
- `file_path` (string): Path to the HNPX file

**Returns:** Document statistics including element counts, word count, POV analysis, etc.

### Export Operations

#### `export_document`
Export HNPX document to other formats.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `format` (string): Export format ("plain" or "markdown")
- `include_summaries` (boolean, optional): Whether to include summaries (default: true)

**Returns:** Exported document content

#### `save_document`
Save changes to the HNPX document.

**Parameters:**
- `file_path` (string): Path to the HNPX file
- `output_path` (string, optional): Output path (defaults to input path)

## Usage Examples

### Getting Node Information
```
get_node({
  "file_path": "example.xml",
  "node_id": "b3k9m7"
})
```

### Getting Context for a Node
```
get_node_context({
  "file_path": "example.xml",
  "node_id": "p9m5k2",
  "include_text": true
})
```

### Adding a New Paragraph
```
append_node_children({
  "file_path": "example.xml",
  "node_id": "b1v6x3",
  "children_xml": '<paragraph id="x1y2z3" mode="narration"><summary>New paragraph summary</summary>This is the new paragraph content.</paragraph>'
})
```

### Finding Empty Containers
```
get_empty_containers({
  "file_path": "example.xml",
  "limit": 5
})
```

### Searching for Content
```
search_nodes({
  "file_path": "example.xml",
  "text_contains": "Boogiepop",
  "tag": "paragraph"
})
```

### Exporting to Markdown
```
export_document({
  "file_path": "example.xml",
  "format": "markdown",
  "include_summaries": true
})
```

## HNPX Document Structure

### Book Element
```xml
<book id="b3k9m7">
  <summary>Book summary</summary>
  <!-- chapters -->
</book>
```

### Chapter Element
```xml
<chapter id="c8p2q5" title="Chapter Title" pov="character_id">
  <summary>Chapter summary</summary>
  <!-- sequences -->
</chapter>
```

### Sequence Element
```xml
<sequence id="s4r7t9" loc="Location" time="time_indicator" pov="character_id">
  <summary>Sequence summary</summary>
  <!-- beats -->
</sequence>
```

### Beat Element
```xml
<beat id="b1v6x3">
  <summary>Beat summary</summary>
  <!-- paragraphs -->
</beat>
```

### Paragraph Element
```xml
<paragraph id="p9m5k2" mode="narration|dialogue|internal" char="character_id">
  <summary>Paragraph summary</summary>
  Paragraph text content here.
</paragraph>
```

## ID Format

All `id` attributes must be:
- Unique within the document
- Exactly 6 characters
- Lowercase letters (a-z) and digits (0-9) only
- Generated randomly by tools

Examples: `a3f9b2`, `c8e4d1`, `x7j5m2`

## Narrative Modes

- **`narration`** (default): Narrator's voice describing action, setting, or exposition
- **`dialogue`**: Character's spoken words. Must have `char` attribute
- **`internal`**: Character's thoughts. `char` optional (defaults to current POV)

## POV Inheritance

Point-of-view flows down the hierarchy:
1. Chapter `pov` sets default for all sequences
2. Sequence `pov` overrides chapter POV for that sequence
3. Paragraph `char` attribute identifies specific speaker/thinker

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Building for Distribution
```bash
pip install build
python -m build
```

## License

This project is licensed under the MIT License.