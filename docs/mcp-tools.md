# Available MCP Tools

### Navigation:
- [create_document](#create_document)
- [get_root_id](#get_root_id)
- [get_node](#get_node)
- [get_subtree](#get_subtree)
- [get_children](#get_children)
- [get_empty](#get_empty)
- [get_path](#get_path)
- [create_chapter](#create_chapter)
- [create_sequence](#create_sequence)
- [create_beat](#create_beat)
- [create_paragraph](#create_paragraph)
- [edit_summary](#edit_summary)
- [edit_paragraph_text](#edit_paragraph_text)
- [edit_node_attributes](#edit_node_attributes)
- [move_nodes](#move_nodes)
- [reorder_children](#reorder_children)
- [remove_nodes](#remove_nodes)
- [remove_node_children](#remove_node_children)
- [render_node](#render_node)

## `create_document`
Create a new empty HNPX document

Args:
    file_path (str): Path where the new HNPX document will be created

## `get_root_id`
Get ID of the book node (document root)

Args:
    file_path (str): Path to the HNPX document

Returns:
    str: ID of the book node

## `get_node`
Retrieve XML representation of a specific node (without descendants)

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the node to retrieve

Returns:
    str: XML representation of the node with its attributes and summary child only

## `get_subtree`
Retrieve XML representation of node including all descendants, optionally pruned

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the node to retrieve
    pruning_level (str): Depth level - one of: "book", "chapter", "sequence", "beat", "full"

Returns:
    str: XML representation of the node and its descendants, pruned to specified depth

## `get_children`
Retrieve immediate child nodes of a specified parent

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the parent node

Returns:
    str: Concatenated XML representation of all direct child nodes

## `get_empty`
Find next container node without children within a specific node's subtree (BFS order)

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the node to search within

Returns:
    str: XML representation of the next empty container node or a message if none found

## `get_path`
Return hierarchical path from document root to specified node

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the target node

Returns:
    str: Concatenated XML representation of all nodes in the path from root to target

## `create_chapter`
Create a new chapter element

Args:
    file_path (str): Path to the HNPX document
    parent_id (str): ID of the parent book element
    title (str): Chapter title
    summary (str): Chapter summary text
    pov (Optional[str]): Point-of-view character identifier

## `create_sequence`
Create a new sequence element

Args:
    file_path (str): Path to the HNPX document
    parent_id (str): ID of the parent chapter element
    location (str): Location description
    summary (str): Sequence summary text
    time (Optional[str]): Time indicator (e.g., "night", "next day", "flashback")
    pov (Optional[str]): Point-of-view character identifier

## `create_beat`
Create a new beat element

Args:
    file_path (str): Path to the HNPX document
    parent_id (str): ID of the parent sequence element
    summary (str): Beat summary text

## `create_paragraph`
Create a new paragraph element

Args:
    file_path (str): Path to the HNPX document
    parent_id (str): ID of the parent beat element
    text (str): Paragraph text content
    mode (str): Narrative mode - one of: "narration" (default), "dialogue", "internal"
    char (Optional[str]): Character identifier (required when mode="dialogue")

## `edit_summary`
Edit summary text of a node

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the node containing the summary
    new_summary (str): New summary text content

## `edit_paragraph_text`
Edit paragraph text content

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the paragraph node to modify
    new_text (str): New paragraph text content

## `edit_node_attributes`
Modify attributes of an existing node

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the node to modify
    attributes (dict): Dictionary of attribute names and values to update

## `move_nodes`
Move multiple nodes between parents

Args:
    file_path (str): Path to the HNPX document
    node_ids (list): List of node IDs to move
    new_parent_id (str): ID of the new parent node

## `reorder_children`
Reorganize the order of child elements

Args:
    file_path (str): Path to the HNPX document
    parent_id (str): ID of the parent node
    child_ids (list): List of child IDs in the desired order

## `remove_nodes`
Permanently remove multiple nodes and all their descendants

Args:
    file_path (str): Path to the HNPX document
    node_ids (list): List of node IDs to remove

## `remove_node_children`
Remove all children of a node

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the parent node

## `render_node`
Render text representation of the node (only descendent paragraphs)

Args:
    file_path (str): Path to the HNPX document
    node_id (str): ID of the node to render
    show_ids (bool): Whether to show paragraph IDs in square brackets

Returns:
    str: Formatted text representation the node

