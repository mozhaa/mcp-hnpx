# HNPX MCP Tools Documentation

This document describes all available MCP (Model Context Protocol) tools provided by the HNPX server for managing hierarchical narrative documents.

## Overview

The HNPX MCP server provides tools for creating, navigating, inspecting, modifying, and rendering hierarchical narrative documents. The document structure follows the HNPX XML schema with the following hierarchy:

```
book
├── chapter
│   └── sequence
│       └── beat
│           └── paragraph
```

## Document Management Tools

### create_document

**Description:** Create a new empty HNPX document with a minimal book structure.

**Parameters:**
- `file_path` (string, required): Path where the new document should be created

**Returns:** String confirmation with the generated book ID and file path

**Example:**
```python
create_document("my_story.xml")
# Returns: "Created book with id abc123 at my_story.xml"
```

---

## Navigation & Discovery Tools

### get_next_empty_container

**Description:** Find the next container node that needs children, searched in breadth-first order. Container nodes include book, chapter, sequence, beat, and empty paragraphs.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document

**Returns:** XML representation of the empty container node, or a message if no empty containers exist

**Example:**
```python
get_next_empty_container("my_story.xml")
# Returns: <beat id="xyz789"><summary>Empty beat</summary></beat>
```

### get_node

**Description:** Retrieve XML representation of a specific node without its descendants.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the node to retrieve

**Returns:** XML representation of the specified node

**Errors:**
- `NodeNotFoundError`: Raised if the node with the specified ID is not found

**Example:**
```python
get_node("my_story.xml", "abc123")
# Returns: <chapter id="abc123" title="Chapter 1"><summary>Chapter summary</summary></chapter>
```

---

## Node Inspection Tools

### get_subtree

**Description:** Retrieve XML representation of a node including all its descendants.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the node to retrieve

**Returns:** XML representation of the node and all its descendants

**Errors:**
- `NodeNotFoundError`: Raised if the node with the specified ID is not found

**Example:**
```python
get_subtree("my_story.xml", "abc123")
# Returns complete XML tree starting from the specified node
```

### get_direct_children

**Description:** Retrieve immediate child nodes of a specified parent.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the parent node

**Returns:** Concatenated XML of all direct children (excluding summary elements)

**Errors:**
- `NodeNotFoundError`: Raised if the parent node with the specified ID is not found

**Example:**
```python
get_direct_children("my_story.xml", "abc123")
# Returns XML of all immediate children of the specified node
```

### get_node_path

**Description:** Return hierarchical path from document root to the specified node.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the target node

**Returns:** Concatenated XML of all ancestors from root to the specified node

**Errors:**
- `NodeNotFoundError`: Raised if the node with the specified ID is not found

**Example:**
```python
get_node_path("my_story.xml", "xyz789")
# Returns XML path from book root through all ancestors to the target node
```

---

## Node Creation Tools

### create_chapter

**Description:** Create a new chapter element within a book.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `parent_id` (string, required): ID of the parent book node
- `title` (string, required): Title of the chapter
- `summary` (string, required): Summary text for the chapter
- `pov` (string, optional): Point of view character for the chapter

**Returns:** String confirmation with the generated chapter ID

**Errors:**
- `NodeNotFoundError`: Raised if the parent node is not found
- `InvalidHierarchyError`: Raised if parent is not a book
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
create_chapter("my_story.xml", "book123", "Chapter 1", "The beginning of the story", "John")
# Returns: "Created chapter with id def456"
```

### create_sequence

**Description:** Create a new sequence element within a chapter.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `parent_id` (string, required): ID of the parent chapter node
- `location` (string, required): Location where the sequence takes place
- `summary` (string, required): Summary text for the sequence
- `time` (string, optional): Time setting for the sequence
- `pov` (string, optional): Point of view character for the sequence

**Returns:** String confirmation with the generated sequence ID

**Errors:**
- `NodeNotFoundError`: Raised if the parent node is not found
- `InvalidHierarchyError`: Raised if parent is not a chapter
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
create_sequence("my_story.xml", "def456", "Forest", "Journey through the woods", "Morning", "John")
# Returns: "Created sequence with id ghi789"
```

### create_beat

**Description:** Create a new beat element within a sequence.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `parent_id` (string, required): ID of the parent sequence node
- `summary` (string, required): Summary text for the beat

**Returns:** String confirmation with the generated beat ID

**Errors:**
- `NodeNotFoundError`: Raised if the parent node is not found
- `InvalidHierarchyError`: Raised if parent is not a sequence
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
create_beat("my_story.xml", "ghi789", "Character discovers something important")
# Returns: "Created beat with id jkl012"
```

### create_paragraph

**Description:** Create a new paragraph element within a beat.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `parent_id` (string, required): ID of the parent beat node
- `summary` (string, required): Summary text for the paragraph
- `text` (string, required): The actual text content of the paragraph
- `mode` (string, optional): Paragraph mode - "narration" (default), "dialogue", or "internal"
- `char` (string, optional): Character name (required for dialogue mode)

**Returns:** String confirmation with the generated paragraph ID

**Errors:**
- `NodeNotFoundError`: Raised if the parent node is not found
- `InvalidParentError`: Raised if parent is not a beat
- `MissingAttributeError`: Raised if char is missing for dialogue mode
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
create_paragraph("my_story.xml", "jkl012", "Opening line", "It was a dark and stormy night.", "narration")
# Returns: "Created paragraph with id mno345"

create_paragraph("my_story.xml", "jkl012", "Character speaks", "Hello there!", "dialogue", "John")
# Returns: "Created paragraph with id pqr678"
```

---

## Node Modification Tools

### edit_node_attributes

**Description:** Modify attributes of an existing node.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the node to modify
- `attributes` (object, required): Dictionary of attributes to modify. Set value to null or empty string to remove an attribute.

**Returns:** String confirmation of the update

**Errors:**
- `NodeNotFoundError`: Raised if the node is not found
- `InvalidOperationError`: Raised if trying to modify the id attribute
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
edit_node_attributes("my_story.xml", "def456", {"title": "New Chapter Title", "pov": "Jane"})
# Returns: "Updated attributes for node def456"

edit_node_attributes("my_story.xml", "ghi789", {"time": ""})  # Removes time attribute
# Returns: "Updated attributes for node ghi789"
```

### remove_node

**Description:** Permanently remove a node and all its descendants.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the node to remove

**Returns:** String confirmation of the removal

**Errors:**
- `NodeNotFoundError`: Raised if the node is not found
- `InvalidOperationError`: Raised if trying to remove the book element
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
remove_node("my_story.xml", "jkl012")
# Returns: "Removed node jkl012 and its descendants"
```

### reorder_children

**Description:** Reorganize the order of child elements within a parent node.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `parent_id` (string, required): ID of the parent node
- `child_ids` (array, required): Array of child IDs in the desired new order

**Returns:** String confirmation of the reordering

**Errors:**
- `NodeNotFoundError`: Raised if the parent node is not found
- `InvalidOperationError`: Raised if child_ids doesn't match existing children
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
reorder_children("my_story.xml", "ghi789", ["mno345", "pqr678", "stu901"])
# Returns: "Reordered children of node ghi789"
```

### edit_summary

**Description:** Edit the summary text of any HNPX element.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the node whose summary should be edited
- `new_summary` (string, required): New summary text content

**Returns:** String confirmation of the update

**Errors:**
- `NodeNotFoundError`: Raised if the node is not found
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
edit_summary("my_story.xml", "def456", "Updated chapter summary")
# Returns: "Updated summary for node def456"
```

### edit_paragraph_text

**Description:** Edit the actual text content of a paragraph element.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `paragraph_id` (string, required): ID of the paragraph to modify
- `new_text` (string, required): New text content for the paragraph

**Returns:** String confirmation of the update

**Errors:**
- `NodeNotFoundError`: Raised if the paragraph is not found
- `InvalidOperationError`: Raised if the specified node is not a paragraph
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
edit_paragraph_text("my_story.xml", "mno345", "It was a bright and sunny morning.")
# Returns: "Updated text content for paragraph mno345"
```

### move_node

**Description:** Move a node to a new parent with optional positioning.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the node to move
- `new_parent_id` (string, required): ID of the new parent node
- `position` (integer, optional): Position index where the node should be placed (0-based). If not specified, node is appended to the end.

**Returns:** String confirmation of the move operation

**Errors:**
- `NodeNotFoundError`: Raised if either the node or new parent is not found
- `InvalidOperationError`: Raised if trying to move the book element or move a node to its own descendant
- `InvalidHierarchyError`: Raised if the parent-child relationship is invalid
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
move_node("my_story.xml", "jkl012", "ghi789", 0)
# Returns: "Moved node jkl012 to parent ghi789"

move_node("my_story.xml", "pqr678", "stu901")
# Returns: "Moved node pqr678 to parent stu901"
```

### remove_node_children

**Description:** Remove all children of a node.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the node to clear

**Returns:** String confirmation with count of removed children

**Errors:**
- `NodeNotFoundError`: Raised if the node is not found
- `ValidationError`: Raised if the document fails schema validation

**Example:**
```python
remove_node_children("my_story.xml", "ghi789")
# Returns: "Cleared all 3 descendants from node ghi789"
```

---

## Rendering & Export Tools

### render_node

**Description:** Render a node and its descendants as formatted text with hierarchical structure.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document
- `node_id` (string, required): ID of the node to render

**Returns:** Formatted text representation of the node and its descendants

**Errors:**
- `NodeNotFoundError`: Raised if the node is not found

**Example:**
```python
render_node("my_story.xml", "def456")
# Returns formatted text like:
# [def456] Chapter: Chapter 1 (POV: John)
#   Summary: The beginning of the story
#   [ghi789] Sequence: Forest at Morning (POV: John)
#     Summary: Journey through the woods
#     [jkl012] Beat: Character discovers something important
#       [mno345] Opening line
#         It was a dark and stormy night.
```

### render_document

**Description:** Export the entire document to plain text, rendering only paragraph content.

**Parameters:**
- `file_path` (string, required): Path to the HNPX document

**Returns:** Plain text representation of all paragraphs in the document

**Example:**
```python
render_document("my_story.xml")
# Returns plain text like:
# It was a dark and stormy night.
# 
# John: "Hello there!"
# 
# *This is an internal thought.*
```

---

## Error Handling

The HNPX MCP server uses specific exception types for different error conditions:

- `HNPXError`: Base exception for all HNPX errors
- `DuplicateIDError`: When trying to create a node with an existing ID
- `InvalidParentError`: When the parent node type is invalid for the operation
- `NodeNotFoundError`: When a specified node ID is not found
- `InvalidAttributeError`: When an attribute value is invalid
- `MissingAttributeError`: When a required attribute is missing
- `InvalidHierarchyError`: When trying to create an invalid parent-child relationship
- `ValidationError`: When document validation fails
- `InvalidOperationError`: When the operation is not allowed

---

## Schema Validation

All modification operations (create, edit, remove, reorder) automatically validate the document against the HNPX XML schema before saving. If validation fails, a `ValidationError` is raised and the document is not modified.

The schema is loaded from `docs/HNPX.xml` relative to the server file location.
