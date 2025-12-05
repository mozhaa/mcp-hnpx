# MCP Server Specification for HNPX Document Processing

## 1. Introduction

This document specifies a Model Context Protocol (MCP) server designed for AI agents to create and manipulate HNPX (Hierarchical Narrative Planning XML) documents. HNPX is a structured XML format for planning and writing fiction with a strict hierarchy from book-level overview to atomic paragraph units.

### 1.1 Purpose
The server enables AI agents to write books step-by-step using a Breadth-First Search (BFS) expansion approach. Agents start with high-level planning and progressively add detail, moving through the narrative hierarchy in a systematic manner.

### 1.2 Design Philosophy
- **AI-First**: Tools are designed specifically for AI agent workflows
- **BFS Guidance**: Built-in navigation tools guide agents through the expansion process
- **Native XML**: Agents work directly with HNPX format
- **Validation**: All operations enforce HNPX specification compliance
- **Atomic Operations**: Each tool performs a single, well-defined operation

## 2. HNPX Format Overview

### 2.1 Hierarchy
```
book → chapter → sequence → beat → paragraph
```
Each element must contain exactly one `<summary>` child element.

### 2.2 Element Requirements
- **Unique IDs**: All elements must have a unique 6-character `id` attribute (lowercase letters + digits)
- **Summary Required**: Every container element must contain exactly one `<summary>` child
- **Strict Nesting**: Elements can only contain children of specific types as defined by the hierarchy

### 2.3 Key Attributes
- **Book**: `id` (required)
- **Chapter**: `id` (required), `title` (required), `pov` (optional)
- **Sequence**: `id` (required), `loc` (required), `time` (optional), `pov` (optional)
- **Beat**: `id` (required)
- **Paragraph**: `id` (required), `mode` (optional: "narration", "dialogue", "internal"), `char` (optional)

## 3. Tool Categories

The MCP server provides 15 tools organized into 5 categories:

1. **Document Management** (1 tool)
2. **Navigation & Discovery** (2 tools)
3. **Node Inspection** (4 tools)
4. **Node Creation** (4 tools)
5. **Node Modification** (3 tools)
6. **Rendering & Export** (2 tools)

## 4. Tool Specifications

### 4.1 Document Management

#### `create_document(file_path)`
Creates a new empty HNPX document with a root `<book>` element.

**Parameters:**
- `file_path` (string, required): Absolute or relative path where the document will be created

**Behavior:**
1. Creates an XML file at `file_path`
2. Initializes with a minimal valid HNPX structure:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <book id="[random_6_char_id]">
     <summary>New book</summary>
   </book>
   ```
3. Generates a random 6-character ID for the book (lowercase letters + digits)

**Error Conditions:**
- File already exists → Returns error "File already exists at [file_path]"
- Invalid file path → Returns error "Cannot create file at [file_path]"

**Example:**
```json
{
  "file_path": "/projects/my_novel.hnpx"
}
```

### 4.2 Navigation & Discovery

#### `get_next_empty_container(file_path)`
Finds the next container node in BFS order that needs children.

**Parameters:**
- `file_path` (string, required): Path to existing HNPX file

**Algorithm:**
1. Parse the document
2. Traverse in BFS order: book → chapter → sequence → beat
3. For each container node, check if it has child elements of the required type:
   - Book: needs at least one `<chapter>`
   - Chapter: needs at least one `<sequence>`
   - Sequence: needs at least one `<beat>`
   - Beat: needs at least one `<paragraph>`
4. Return the first container that fails this check

**Returns:**
- Object with `id` and `type` of the empty container
- `null` if no empty containers exist (document is fully expanded)

**Example Response:**
```json
{
  "id": "k9p3q1",
  "type": "chapter",
  "message": "Chapter has no sequences"
}
```

#### `get_node(file_path, node_id)`
Retrieves XML representation of a specific node (without descendants).

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `node_id` (string, required): Unique identifier of the node

**Behavior:**
1. Locates the node with matching `id` attribute
2. Returns the node's XML including all attributes but excluding child elements
3. For container nodes, includes the `<summary>` child

**Error Conditions:**
- Node not found → Returns error "Node with id [node_id] not found"
- Invalid XML → Returns error "Document is not valid XML"

**Example Response:**
```xml
<chapter id="k9p3q1" title="The Awakening" pov="mira">
  <summary>A young mage discovers her powers in the forbidden woods.</summary>
</chapter>
```

### 4.3 Node Inspection

#### `get_subtree(file_path, node_id)`
Retrieves XML representation of a node including all its descendants.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `node_id` (string, required): Unique identifier of the root node

**Behavior:**
1. Locates the node with matching `id` attribute
2. Returns the node's complete XML subtree
3. Includes all child elements recursively

**Example Response:**
```xml
<sequence id="r4s8t6" loc="Forest" time="night">
  <summary>Mira discovers an ancient shrine.</summary>
  <beat id="u1v7w3">
    <summary>Entering the forbidden woods.</summary>
    <paragraph id="z5y2x4" mode="narration">
      <summary>Mira pushes through the undergrowth.</summary>
      Mira pushed through the thick undergrowth, her breath fogging in the cold air.
    </paragraph>
  </beat>
</sequence>
```

#### `get_direct_children(file_path, node_id)`
Retrieves immediate child nodes of a specified parent.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `node_id` (string, required): Unique identifier of the parent node

**Behavior:**
1. Locates the parent node
2. Returns XML of all direct child elements
3. Does not include grandchildren or deeper descendants

**Example Response:**
```xml
<children>
  <beat id="u1v7w3">
    <summary>Entering the forbidden woods.</summary>
  </beat>
  <beat id="p9o3i7">
    <summary>Finding the shrine.</summary>
  </beat>
</children>
```

#### `get_node_path(file_path, node_id)`
Returns the complete hierarchical path from document root to specified node.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `node_id` (string, required): Unique identifier of the target node

**Behavior:**
1. Locates the target node
2. Traces parent chain up to root
3. Returns XML containing each ancestor in order

**Example Response:**
```xml
<path>
  <book id="a3f9b2">
    <summary>A young mage's journey to uncover her forgotten past.</summary>
  </book>
  <chapter id="k9p3q1" title="The Awakening" pov="mira">
    <summary>A young mage discovers her powers in the forbidden woods.</summary>
  </chapter>
  <sequence id="r4s8t6" loc="Forest" time="night">
    <summary>Mira discovers an ancient shrine.</summary>
  </sequence>
</path>
```

#### `create_chapter(file_path, parent_id, title, summary, pov=null)`
Creates a new chapter element.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `parent_id` (string, required): ID of parent book element
- `title` (string, required): Chapter title
- `summary` (string, required): Chapter summary
- `pov` (string, optional): Point-of-view character identifier

**Validation:**
1. Parent must be a `<book>` element
2. `parent_id` must exist
3. `title` must be non-empty
4. `summary` must be non-empty
5. Generated ID must be unique 6-character string

**Generated XML:**
```xml
<chapter id="[generated_id]" title="[title]" pov="[pov if provided]">
  <summary>[summary]</summary>
</chapter>
```

**Error Conditions:**
- Invalid parent type → "Parent must be a book element"
- Duplicate title in sibling chapters → "Chapter title must be unique within book"

#### `create_sequence(file_path, parent_id, location, summary, time=null, pov=null)`
Creates a new sequence element.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `parent_id` (string, required): ID of parent chapter element
- `location` (string, required): Where the sequence takes place
- `summary` (string, required): Sequence summary
- `time` (string, optional): Time indicator
- `pov` (string, optional): Overrides chapter POV if present

**Validation:**
1. Parent must be a `<chapter>` element
2. `location` must be non-empty

#### `create_beat(file_path, parent_id, summary)`
Creates a new beat element.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `parent_id` (string, required): ID of parent sequence element
- `summary` (string, required): Beat summary

**Validation:**
1. Parent must be a `<sequence>` element

#### `create_paragraph(file_path, parent_id, summary, text, mode="narration", char=null)`
Creates a new paragraph element.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `parent_id` (string, required): ID of parent beat element
- `summary` (string, required): Paragraph summary
- `text` (string, required): Paragraph text content
- `mode` (string, optional): "narration", "dialogue", or "internal"
- `char` (string, optional): Character identifier

**Validation:**
1. Parent must be a `<beat>` element
2. `text` must be non-empty
3. If `mode="dialogue"`, `char` must be provided
4. If `mode="internal"` and no `char` provided, inherits from sequence/chapter POV

### 4.5 Node Modification

#### `edit_node_attributes(file_path, node_id, attributes)`
Modifies attributes of an existing node.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `node_id` (string, required): ID of node to modify
- `attributes` (object, required): Key-value pairs of attributes to update

**Behavior:**
1. Updates specified attributes
2. Preserves existing attributes not in `attributes` object
3. Removes attributes set to `null` or empty string

**Validation:**
- Cannot modify `id` attribute
- Chapter: `title` cannot be empty
- Sequence: `loc` cannot be empty
- Paragraph: `mode` must be valid value

#### `remove_node(file_path, node_id)`
Permanently removes a node and all its descendants.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `node_id` (string, required): ID of node to remove

**Validation:**
- Cannot remove root `<book>` element
- Removing a node with children removes entire subtree

#### `reorder_children(file_path, parent_id, child_ids)`
Reorganizes the order of child elements.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `parent_id` (string, required): ID of parent container
- `child_ids` (array, required): List of child IDs in desired order

**Validation:**
- All IDs in `child_ids` must exist as children of parent
- Must include all children (cannot omit any)

### 4.6 Rendering & Export

#### `render_node(file_path, node_id)`
Renders a node and descendants as formatted markdown.

**Parameters:**
- `file_path` (string, required): Path to HNPX file
- `node_id` (string, required): ID of node to render

**Format:**
- IDs shown in brackets before each element
- Hierarchy indicated by indentation
- Paragraph text rendered plainly
- Dialogue wrapped in quotes
- Internal thoughts in italics

**Example Output:**
```
[a3f9b2] Book: A young mage's journey
  [k9p3q1] Chapter 1: The Awakening (POV: mira)
    [r4s8t6] Sequence: Forest at night
      [u1v7w3] Beat: Entering the forbidden woods
        [z5y2x4] Mira pushes through the undergrowth.
        Mira pushed through the thick undergrowth...
        
        [m6n8b4] Description of the ancient trees.
        The ancient trees loomed overhead...
```

#### `render_document(file_path)`
Exports entire document to plain text.

**Parameters:**
- `file_path` (string, required): Path to HNPX file

**Behavior:**
- Renders all paragraphs as continuous text
- Omits IDs, summaries, and metadata
- Formats dialogue with quotes and speaker indicators
- Formats internal thoughts appropriately

## 5. AI Agent Workflow

### 5.1 Initialization Phase
1. Agent calls `create_document()` to start new book
2. Agent sets book summary using `edit_node_attributes()`

### 5.2 Planning Phase (BFS Expansion)
```
LOOP UNTIL get_next_empty_container() returns null:
  1. Call get_next_empty_container() → returns next empty node
  2. Based on node type:
     - BOOK: Plan chapters → create_chapter() for each planned chapter
     - CHAPTER: Plan sequences → create_sequence() for each sequence
     - SEQUENCE: Plan beats → create_beat() for each beat
     - BEAT: Write paragraphs → create_paragraph() for each paragraph
  
  3. After creating children for current node:
     - Optionally call get_subtree(parent_id) to review context
     - Optionally call render_node(parent_id) to see formatted output
```

### 5.3 Revision Phase
1. Navigate using `get_node_path()` and `get_direct_children()`
2. Modify content using `edit_node_attributes()` and `reorder_children()`
3. Remove content using `remove_node()`
4. Preview using `render_document()`

## 6. Error Handling Specification

### 6.1 Error Response Format
All errors return JSON with:
```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "details": { /* Additional context */ }
}
```

### 6.2 Error Codes

#### Document-Level Errors
- `FILE_NOT_FOUND`: Specified file doesn't exist
- `INVALID_XML`: File contains malformed XML
- `NOT_HNPX`: File is not valid HNPX format
- `FILE_EXISTS`: File already exists (create_document)

#### Node-Level Errors
- `NODE_NOT_FOUND`: Node ID doesn't exist
- `INVALID_PARENT`: Parent cannot accept this child type
- `DUPLICATE_ID`: Generated ID already exists (retry)
- `MISSING_ATTRIBUTE`: Required attribute not provided
- `INVALID_ATTRIBUTE`: Attribute value violates constraints

#### Hierarchy Errors
- `INVALID_HIERARCHY`: Attempt to break book→chapter→sequence→beat→paragraph chain
- `EMPTY_SUMMARY`: Summary element missing or empty
- `MISSING_CHAR`: Dialogue paragraph missing char attribute

#### Operation Errors
- `VALIDATION_FAILED`: Operation would create invalid HNPX
- `READ_ONLY`: Cannot modify read-only attribute (e.g., id)
- `IMMUTABLE_ROOT`: Cannot remove book element

### 6.3 Validation Rules Enforcement
Each tool must validate:
1. **Pre-operation**: Check if operation would create invalid state
2. **Post-operation**: Verify resulting document is valid HNPX
3. **Rollback**: If validation fails, revert changes

## 7. Implementation Notes

### 7.1 ID Generation
- Use cryptographically secure random generation
- Format: 6 characters from set [a-z0-9] (36^6 ≈ 2.1 billion possibilities)
- Check for uniqueness before assignment
- If collision occurs, regenerate (max 3 attempts before error)

### 7.2 XML Processing
- Use DOM parser that preserves whitespace in paragraph text
- Always include XML declaration: `<?xml version="1.0" encoding="UTF-8"?>`
- Pretty-print with 2-space indentation for readability
- Ensure proper escaping of special characters in text content

### 7.3 File Operations
- All file operations should be atomic
- Use file locking to prevent concurrent modifications
- Validate file permissions before operations

### 7.4 Performance Considerations
- For large documents, use streaming XML processing where possible
- Cache document structure for repeated operations in same session
- Implement pagination for `get_direct_children()` if needed
- Consider memory limits for `get_subtree()` on large branches

## 8. Example Complete Workflow

### 8.1 Step 1: Create Document
```json
Agent calls: create_document("/story.hnpx")
Server creates: /story.hnpx with book element
```

### 8.2 Step 2: Plan Chapters
```json
Agent calls: get_next_empty_container("/story.hnpx")
Returns: { "id": "a3f9b2", "type": "book" }

Agent calls: create_chapter("/story.hnpx", "a3f9b2", "The Awakening", "...", "mira")
Agent calls: create_chapter("/story.hnpx", "a3f9b2", "The Journey", "...", "mira")
```

### 8.3 Step 3: Expand First Chapter
```json
Agent calls: get_next_empty_container("/story.hnpx")
Returns: { "id": "chp001", "type": "chapter" }

Agent calls: get_subtree("/story.hnpx", "chp001")
Agent calls: create_sequence("/story.hnpx", "chp001", "Forest", "...", "night")
```

### 8.4 Step 4: Write Paragraphs
```json
Agent calls: get_next_empty_container("/story.hnpx")
Returns: { "id": "seq001", "type": "sequence" }

Agent creates beats, then paragraphs...
```

### 8.5 Step 5: Review
```json
Agent calls: render_document("/story.hnpx")
Returns: Full text of written content
```

## 9. Testing Requirements

### 9.1 Unit Tests
- Each tool in isolation with valid/invalid inputs
- ID generation uniqueness and format
- XML parsing and serialization

### 9.2 Integration Tests
- Complete BFS workflow simulation
- Error recovery scenarios
- Concurrent access handling

### 9.3 Validation Tests
- All HNPX specification rules enforced
- Edge cases (empty documents, single paragraph books)
- Unicode and special character handling

## 10. Security Considerations

### 10.1 File System Safety
- Validate file paths to prevent directory traversal
- Limit file size to prevent DoS
- Sanitize XML input to prevent injection attacks

### 10.2 Resource Management
- Timeout long-running operations
- Limit memory usage for large documents
- Implement request rate limiting

### 10.3 Data Integrity
- Verify XML well-formedness before processing
- Implement checksum verification

---

This specification provides complete implementation details for an MCP server that enables AI agents to write fiction using the HNPX format. All tools are designed for the BFS expansion workflow, with proper error handling and validation at each step.
