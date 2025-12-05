# MCP Tools for HNPX Document Processing

## Available Tools

### Document Creation
- `create_document(file_path, title="Untitled Book")` - Create a new empty HNPX document

### Core Node Operations
- `get_node(file_path, node_id)` - Get node details by ID
- `get_node_context(file_path, node_id, include_text=false)` - Get node context (parent, siblings)
- `edit_node_attributes(file_path, node_id, attributes)` - Edit node attributes

### Content Editing
- `set_node_children(file_path, node_id, children_xml)` - Replace all children
- `append_node_children(file_path, node_id, children_xml)` - Append children
- `remove_node(file_path, node_id)` - Remove node

### Document Analysis
- `get_empty_containers(file_path, limit=10)` - Find containers needing children
- `search_nodes(file_path, tag, attributes, text_contains, summary_contains)` - Search nodes
- `validate_document(file_path)` - Validate against schema
- `get_document_stats(file_path)` - Get document statistics

### Export Operations
- `export_document(file_path, format, include_summaries=true)` - Export to plain/markdown
- `save_document(file_path, output_path)` - Save changes

## Quick Examples

```
// Create new document
create_document({"file_path": "new_story.xml", "title": "My Novel"})

// Get node
get_node({"file_path": "example.xml", "node_id": "b3k9m7"})

// Get context
get_node_context({"file_path": "example.xml", "node_id": "p9m5k2", "include_text": true})

// Add paragraph
append_node_children({
  "file_path": "example.xml", 
  "node_id": "b1v6x3",
  "children_xml": "<paragraph id='x1y2z3' mode='narration'><summary>New paragraph</summary>Content</paragraph>"
})

// Find empty containers
get_empty_containers({"file_path": "example.xml", "limit": 5})

// Search
search_nodes({
  "file_path": "example.xml",
  "text_contains": "Boogiepop",
  "tag": "paragraph"
})

// Export
export_document({
  "file_path": "example.xml",
  "format": "markdown",
  "include_summaries": true
})
```

## Key Parameters
- `file_path` (required): Path to HNPX XML file
- `title` (optional for create_document): Document title (default: "Untitled Book")
- `node_id` (required for node ops): Unique node identifier
- `children_xml`: XML string for child elements
- `format`: "plain" or "markdown"
- `include_text/include_summaries`: Boolean flags for content inclusion

---
**Note**: All tools require `file_path`. Use `save_document` after edits to persist changes.
