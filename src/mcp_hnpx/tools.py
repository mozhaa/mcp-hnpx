import random
import string
from typing import Optional
from lxml import etree

from . import hnpx
from .exceptions import (
    NodeNotFoundError,
    InvalidAttributeError,
    InvalidHierarchyError,
    MissingAttributeError,
    InvalidParentError,
    InvalidOperationError,
)


def create_document(file_path: str) -> str:
    """Create a new empty HNPX document
    
    Args:
        file_path (str): Path where the new HNPX document will be created
    """
    # Generate initial book ID
    book_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Create minimal document
    book = etree.Element("book", id=book_id)
    summary = etree.SubElement(book, "summary")
    summary.text = "New book"

    # Create tree and save
    tree = etree.ElementTree(book)
    hnpx.save_document(tree, file_path)

    return f"Created book with id {book_id} at {file_path}"


def get_next_empty_container(file_path: str) -> str:
    """Find next container node that needs children (BFS order)
    
    Args:
        file_path (str): Path to the HNPX document
        
    Returns:
        str: XML representation of the next empty container node or a message if none found
    """
    tree = hnpx.parse_document(file_path)
    empty_node = hnpx.find_first_empty_container(tree)

    if empty_node is None:
        return "No empty containers found - document is fully expanded"

    # Return node XML (like get_node)
    return etree.tostring(empty_node, encoding="unicode", method="html")


def get_next_empty_container_in_node(file_path: str, node_id: str) -> str:
    """Find next container node that needs children within a specific node's subtree (BFS order)
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to search within
        
    Returns:
        str: XML representation of the next empty container node or a message if none found
    """
    tree = hnpx.parse_document(file_path)
    start_node = hnpx.find_node(tree, node_id)

    if start_node is None:
        raise NodeNotFoundError(node_id)

    empty_node = hnpx.find_first_empty_container(tree, start_node)

    if empty_node is None:
        return f"No empty containers found within node {node_id}"

    # Return node XML (like get_node)
    return etree.tostring(empty_node, encoding="unicode", method="html")

def _remove_children(node: Any) -> None:
    for child in node:
        if child.tag != "summary":
            node.remove(child)

def get_node(file_path: str, node_id: str) -> str:
    """Retrieve XML representation of a specific node (without descendants)
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to retrieve
        
    Returns:
        str: XML representation of the node with its attributes and summary child only
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    _remove_children(node)

    # Return node with all attributes and summary child
    return etree.tostring(node, encoding="unicode", method="html")


def get_subtree(file_path: str, node_id: str) -> str:
    """Retrieve XML representation of node including all descendants
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to retrieve
        
    Returns:
        str: XML representation of the node and all its descendants
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    return etree.tostring(node, encoding="unicode", method="html")


def get_direct_children(file_path: str, node_id: str) -> str:
    """Retrieve immediate child nodes of a specified parent
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the parent node
        
    Returns:
        str: Concatenated XML representation of all direct child nodes
    """
    tree = hnpx.parse_document(file_path)
    parent = hnpx.find_node(tree, node_id)

    if parent is None:
        raise NodeNotFoundError(node_id)

    # Return concatenated XML of all direct children
    children_xml = []
    for child in parent:
        if child.tag == "summary":
            continue
        _remove_children(child)
        children_xml.append(etree.tostring(child, encoding="unicode", method="html"))

    return "\n".join(children_xml)


def get_node_path(file_path: str, node_id: str) -> str:
    """Return hierarchical path from document root to specified node
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the target node
        
    Returns:
        str: Concatenated XML representation of all nodes in the path from root to target
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Collect ancestors
    ancestors = []
    current = node
    while current is not None:
        ancestors.insert(0, current)
        current = current.getparent()

    # Return concatenated XML of all ancestors
    path_xml = []
    for ancestor in ancestors:
        path_xml.append(etree.tostring(ancestor, encoding="unicode", method="html"))

    return "\n".join(path_xml)


def get_document_at_depth(file_path: str, level: str = "chapter") -> str:
    """Retrieve XML representation of document at specified depth level
    
    Args:
        file_path (str): Path to the HNPX document
        level (str): Depth level - one of: "book", "chapter", "sequence", "beat", "full"
        
    Returns:
        str: XML representation of the document pruned to the specified depth
    """
    tree = hnpx.parse_document(file_path)
    root = tree.getroot()

    # Validate level parameter
    valid_levels = ["book", "chapter", "sequence", "beat", "full"]
    if level not in valid_levels:
        raise InvalidAttributeError(
            "level", level, f"Must be one of: {', '.join(valid_levels)}"
        )

    # Define hierarchy levels
    hierarchy = {"book": 0, "chapter": 1, "sequence": 2, "beat": 3, "full": 5}

    max_depth = hierarchy[level]

    def prune_tree(node: etree.Element, current_depth: int) -> None:
        """Recursively remove nodes beyond max_depth"""
        if current_depth >= max_depth:
            # Remove all children except summary
            children_to_remove = []
            for child in node:
                if child.tag != "summary":
                    children_to_remove.append(child)

            for child in children_to_remove:
                node.remove(child)
        else:
            # Recursively process children
            for child in list(node):
                if child.tag in hierarchy:
                    prune_tree(child, current_depth + 1)

    # Start pruning from the root (book is at depth 0)
    prune_tree(root, 0)

    # Return the pruned tree as XML
    return etree.tostring(root, encoding="unicode", pretty_print=True)


def _create_element(
    tree: etree.ElementTree,
    parent_id: str,
    element_tag: str,
    attributes: dict,
    summary_text: str,
) -> str:
    """Generic element creation helper"""
    parent = hnpx.find_node(tree, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    # Check hierarchy
    valid_hierarchy = {
        "book": ["chapter"],
        "chapter": ["sequence"],
        "sequence": ["beat"],
        "beat": ["paragraph"],
    }

    if (
        parent.tag not in valid_hierarchy
        or element_tag not in valid_hierarchy[parent.tag]
    ):
        raise InvalidHierarchyError(parent.tag, element_tag)

    # Generate unique ID
    existing_ids = hnpx.get_all_ids(tree)
    new_id = hnpx.generate_unique_id(existing_ids)
    attributes["id"] = new_id

    # Create element
    element = etree.SubElement(parent, element_tag, **attributes)
    summary = etree.SubElement(element, "summary")
    summary.text = summary_text

    return new_id


def create_chapter(
    file_path: str, parent_id: str, title: str, summary: str, pov: Optional[str] = None
) -> str:
    """Create a new chapter element
    
    Args:
        file_path (str): Path to the HNPX document
        parent_id (str): ID of the parent book element
        title (str): Chapter title
        summary (str): Chapter summary text
        pov (Optional[str]): Point-of-view character identifier
    """
    tree = hnpx.parse_document(file_path)

    attributes = {"title": title}
    if pov:
        attributes["pov"] = pov

    new_id = _create_element(tree, parent_id, "chapter", attributes, summary)

    hnpx.save_document(tree, file_path)

    return f"Created chapter with id {new_id}"


def create_sequence(
    file_path: str,
    parent_id: str,
    location: str,
    summary: str,
    time: Optional[str] = None,
    pov: Optional[str] = None,
) -> str:
    """Create a new sequence element
    
    Args:
        file_path (str): Path to the HNPX document
        parent_id (str): ID of the parent chapter element
        location (str): Location description
        summary (str): Sequence summary text
        time (Optional[str]): Time indicator (e.g., "night", "next day", "flashback")
        pov (Optional[str]): Point-of-view character identifier
    """
    tree = hnpx.parse_document(file_path)

    attributes = {"location": location}
    if time:
        attributes["time"] = time
    if pov:
        attributes["pov"] = pov

    new_id = _create_element(tree, parent_id, "sequence", attributes, summary)

    hnpx.save_document(tree, file_path)

    return f"Created sequence with id {new_id}"


def create_beat(file_path: str, parent_id: str, summary: str) -> str:
    """Create a new beat element
    
    Args:
        file_path (str): Path to the HNPX document
        parent_id (str): ID of the parent sequence element
        summary (str): Beat summary text
    """
    tree = hnpx.parse_document(file_path)

    new_id = _create_element(tree, parent_id, "beat", {}, summary)

    hnpx.save_document(tree, file_path)

    return f"Created beat with id {new_id}"


def create_paragraph(
    file_path: str,
    parent_id: str,
    text: str,
    mode: str = "narration",
    char: Optional[str] = None,
) -> str:
    """Create a new paragraph element
    
    Args:
        file_path (str): Path to the HNPX document
        parent_id (str): ID of the parent beat element
        text (str): Paragraph text content
        mode (str): Narrative mode - one of: "narration" (default), "dialogue", "internal"
        char (Optional[str]): Character identifier (required when mode="dialogue")
    """
    tree = hnpx.parse_document(file_path)

    attributes = {"mode": mode}
    if char:
        attributes["char"] = char
    elif mode == "dialogue":
        raise MissingAttributeError("char")

    # Create the paragraph with text content
    parent = hnpx.find_node(tree, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    if parent.tag != "beat":
        raise InvalidParentError(parent.tag, "beat")

    existing_ids = hnpx.get_all_ids(tree)
    new_id = hnpx.generate_unique_id(existing_ids)
    attributes["id"] = new_id

    paragraph = etree.SubElement(parent, "paragraph", **attributes)
    paragraph.text = text

    hnpx.save_document(tree, file_path)

    return f"Created paragraph with id {new_id}"


def edit_node_attributes(file_path: str, node_id: str, attributes: dict) -> str:
    """Modify attributes of an existing node
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to modify
        attributes (dict): Dictionary of attribute names and values to update
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Update attributes
    for key, value in attributes.items():
        if key == "id":
            raise InvalidOperationError(
                "edit_node_attributes", "Cannot modify id attribute"
            )

        if value is None or value == "":
            if key in node.attrib:
                del node.attrib[key]
        else:
            node.set(key, value)

    hnpx.save_document(tree, file_path)

    return f"Updated attributes for node {node_id}"


def remove_node(file_path: str, node_id: str) -> str:
    """Permanently remove a node and all its descendants
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to remove
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Check if trying to remove root
    if node.tag == "book":
        raise InvalidOperationError("remove_node", "Cannot remove book element")

    # Remove node
    parent = node.getparent()
    parent.remove(node)

    hnpx.save_document(tree, file_path)

    return f"Removed node {node_id} and its descendants"


def reorder_children(file_path: str, parent_id: str, child_ids: list) -> str:
    """Reorganize the order of child elements
    
    Args:
        file_path (str): Path to the HNPX document
        parent_id (str): ID of the parent node
        child_ids (list): List of child IDs in the desired order
    """
    tree = hnpx.parse_document(file_path)
    parent = hnpx.find_node(tree, parent_id)

    if parent is None:
        raise NodeNotFoundError(parent_id)

    # Get current children (excluding summary)
    current_children = [child for child in parent if child.tag != "summary"]
    current_ids = [child.get("id") for child in current_children]

    # Validate input
    if set(child_ids) != set(current_ids):
        raise InvalidOperationError(
            "reorder_children", "child_ids must contain all existing child IDs"
        )

    # Create mapping and reorder
    child_map = {child.get("id"): child for child in current_children}

    # Remove all children (except summary)
    for child in current_children:
        parent.remove(child)

    # Add back in new order
    for child_id in child_ids:
        parent.append(child_map[child_id])

    hnpx.save_document(tree, file_path)

    return f"Reordered children of node {parent_id}"


def edit_summary(file_path: str, node_id: str, new_summary: str) -> str:
    """Edit summary text of any element
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node containing the summary
        new_summary (str): New summary text content
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Find the summary child element
    summary_elem = node.find("summary")
    if summary_elem is None:
        # Create summary if it doesn't exist (shouldn't happen with valid HNPX)
        summary_elem = etree.SubElement(node, "summary")

    # Update the summary text
    summary_elem.text = new_summary

    hnpx.save_document(tree, file_path)

    return f"Updated summary for node {node_id}"


def edit_paragraph_text(file_path: str, paragraph_id: str, new_text: str) -> str:
    """Edit actual paragraph content
    
    Args:
        file_path (str): Path to the HNPX document
        paragraph_id (str): ID of the paragraph element to modify
        new_text (str): New paragraph text content
    """
    tree = hnpx.parse_document(file_path)
    paragraph = hnpx.find_node(tree, paragraph_id)

    if paragraph is None:
        raise NodeNotFoundError(paragraph_id)

    # Verify it's a paragraph element
    if paragraph.tag != "paragraph":
        raise InvalidOperationError(
            "edit_paragraph_text", f"Node {paragraph_id} is not a paragraph"
        )

    # Update the paragraph text content
    paragraph.text = new_text

    hnpx.save_document(tree, file_path)

    return f"Updated text content for paragraph {paragraph_id}"


def move_node(
    file_path: str, node_id: str, new_parent_id: str, position: Optional[int] = None
) -> str:
    """Move nodes between parents
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to move
        new_parent_id (str): ID of the new parent node
        position (Optional[int]): Position index in the new parent's children (0-based)
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)
    new_parent = hnpx.find_node(tree, new_parent_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    if new_parent is None:
        raise NodeNotFoundError(new_parent_id)

    # Check if trying to move root
    if node.tag == "book":
        raise InvalidOperationError("move_node", "Cannot move book element")

    # Check hierarchy validity
    valid_hierarchy = {
        "book": ["chapter"],
        "chapter": ["sequence"],
        "sequence": ["beat"],
        "beat": ["paragraph"],
    }

    if (
        new_parent.tag not in valid_hierarchy
        or node.tag not in valid_hierarchy[new_parent.tag]
    ):
        raise InvalidHierarchyError(new_parent.tag, node.tag)

    # Check if trying to move a node to its own descendant
    current = new_parent
    while current is not None:
        if current == node:
            raise InvalidOperationError(
                "move_node", "Cannot move a node to its own descendant"
            )
        current = current.getparent()

    # Get old parent
    old_parent = node.getparent()

    # Remove from old parent
    old_parent.remove(node)

    # Add to new parent
    if position is None:
        # Append to the end
        new_parent.append(node)
    else:
        # Insert at specific position
        # Get current children (excluding summary)
        children = [child for child in new_parent if child.tag != "summary"]

        if position < 0 or position > len(children):
            raise InvalidOperationError(
                "move_node", f"Position {position} out of range (0-{len(children)})"
            )

        if position == len(children):
            new_parent.append(node)
        else:
            new_parent.insert(
                position + (1 if new_parent[0].tag == "summary" else 0), node
            )

    hnpx.save_document(tree, file_path)

    return f"Moved node {node_id} to parent {new_parent_id}"


def remove_node_children(file_path: str, node_id: str) -> str:
    """Remove all children of a node
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the parent node
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    children_count = 0

    # Remove all children except summary
    for child in list(node):
        if child.tag != "summary":
            node.remove(child)
            children_count += 1

    hnpx.save_document(tree, file_path)

    return f"Removed {children_count} children from node {node_id}"


def _render_node_recursive(node: etree.Element, indent: int = 0) -> str:
    """Recursively render node and children as formatted text"""
    lines = []
    indent_str = "  " * indent

    # Get node info
    node_id = node.get("id", "")
    summary = node.findtext("summary", "").strip()

    # Render based on node type
    if node.tag == "book":
        lines.append(f"{indent_str}[{node_id}] Book: {summary}")
    elif node.tag == "chapter":
        title = node.get("title", "")
        pov = node.get("pov", "")
        pov_str = f" (POV: {pov})" if pov else ""
        lines.append(f"{indent_str}[{node_id}] Chapter: {title}{pov_str}")
        lines.append(f"{indent_str}  Summary: {summary}")
    elif node.tag == "sequence":
        location = node.get("location", "")
        time = node.get("time", "")
        pov = node.get("pov", "")
        time_str = f" at {time}" if time else ""
        pov_str = f" (POV: {pov})" if pov else ""
        lines.append(f"{indent_str}[{node_id}] Sequence: {location}{time_str}{pov_str}")
        lines.append(f"{indent_str}  Summary: {summary}")
    elif node.tag == "beat":
        lines.append(f"{indent_str}[{node_id}] Beat: {summary}")
    elif node.tag == "paragraph":
        lines.append(f"{indent_str}[{node_id}] {summary}")
        rendered_text = hnpx.render_paragraph(node)
        if rendered_text:
            lines.append(f"{indent_str}  {rendered_text}")

    # Recursively render children (excluding summary)
    for child in node:
        if child.tag != "summary":
            lines.append(_render_node_recursive(child, indent + 1))

    return "\n".join(lines)


def render_node(file_path: str, node_id: str) -> str:
    """Render a node and descendants as formatted text
    
    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to render
        
    Returns:
        str: Formatted text representation of the node and its descendants
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    return _render_node_recursive(node)


def render_document(file_path: str) -> str:
    """Export entire document to plain text
    
    Args:
        file_path (str): Path to the HNPX document
        
    Returns:
        str: Complete document rendered as readable plain text
    """
    tree = hnpx.parse_document(file_path)

    paragraphs = []
    for paragraph in tree.xpath("//paragraph"):
        rendered = hnpx.render_paragraph(paragraph)
        if rendered:
            paragraphs.append(rendered)

    return "\n\n".join(paragraphs)
