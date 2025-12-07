import random
import string
from typing import Any, Optional

from lxml import etree

from . import hnpx
from .exceptions import (
    InvalidAttributeError,
    InvalidHierarchyError,
    InvalidOperationError,
    InvalidParentError,
    MissingAttributeError,
    NodeNotFoundError,
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


def get_root_id(file_path: str) -> str:
    """Get ID of the book node (document root)

    Args:
        file_path (str): Path to the HNPX document

    Returns:
        str: ID of the book node
    """
    tree = hnpx.parse_document(file_path)
    root = tree.getroot()
    return root.get("id")


def get_empty(file_path: str, node_id: str) -> str:
    """Find next container node without children within a specific node's subtree (BFS order)

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


def get_subtree(file_path: str, node_id: str, pruning_level: str = "full") -> str:
    """Retrieve XML representation of node including all descendants, optionally pruned

    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to retrieve
        pruning_level (str): Depth level - one of: "book", "chapter", "sequence", "beat", "full"

    Returns:
        str: XML representation of the node and its descendants, pruned to specified depth
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # If no pruning needed, return full subtree
    if pruning_level == "full":
        return etree.tostring(node, encoding="unicode", method="html")

    # Validate level parameter
    valid_levels = ["book", "chapter", "sequence", "beat", "full"]
    if pruning_level not in valid_levels:
        raise InvalidAttributeError(
            "pruning_level", pruning_level, f"Must be one of: {', '.join(valid_levels)}"
        )

    # Define hierarchy levels
    hierarchy = {"book": 0, "chapter": 1, "sequence": 2, "beat": 3, "full": 5}

    max_depth = hierarchy[pruning_level]

    # Create a copy of the node to avoid modifying the original
    node_copy = etree.Element(node.tag, node.attrib)
    for child in node:
        node_copy.append(etree.fromstring(etree.tostring(child, encoding="unicode")))

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

    # Start pruning from the node (determine depth based on node type)
    node_depth = hierarchy.get(node.tag, 0)
    prune_tree(node_copy, node_depth)

    # Return the pruned tree as XML
    return etree.tostring(node_copy, encoding="unicode", pretty_print=True)


def get_children(file_path: str, node_id: str) -> str:
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


def get_path(file_path: str, node_id: str) -> str:
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


def remove_nodes(file_path: str, node_ids: list) -> str:
    """Permanently remove multiple nodes and all their descendants

    Args:
        file_path (str): Path to the HNPX document
        node_ids (list): List of node IDs to remove
    """
    tree = hnpx.parse_document(file_path)

    nodes_removed = 0
    for node_id in node_ids:
        node = hnpx.find_node(tree, node_id)

        if node is None:
            raise NodeNotFoundError(node_id)

        # Check if trying to remove root
        if node.tag == "book":
            raise InvalidOperationError("remove_nodes", "Cannot remove book element")

        # Remove node
        parent = node.getparent()
        parent.remove(node)
        nodes_removed += 1

    hnpx.save_document(tree, file_path)

    return f"Removed {nodes_removed} nodes and their descendants"


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
    """Edit summary text of a node

    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node containing the summary
        new_summary (str): New summary text content
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    if node.tag == "paragraph":
        raise InvalidOperationError(
            "edit_summary", "Paragraphs can't contain summaries"
        )

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
    """Edit paragraph text content

    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the paragraph node to modify
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


def move_nodes(file_path: str, node_ids: list, new_parent_id: str) -> str:
    """Move multiple nodes between parents

    Args:
        file_path (str): Path to the HNPX document
        node_ids (list): List of node IDs to move
        new_parent_id (str): ID of the new parent node
    """
    tree = hnpx.parse_document(file_path)
    new_parent = hnpx.find_node(tree, new_parent_id)

    if new_parent is None:
        raise NodeNotFoundError(new_parent_id)

    # Check hierarchy validity for new parent
    valid_hierarchy = {
        "book": ["chapter"],
        "chapter": ["sequence"],
        "sequence": ["beat"],
        "beat": ["paragraph"],
        "paragraph": [],
    }

    nodes_moved = 0
    for node_id in node_ids:
        node = hnpx.find_node(tree, node_id)
        if node is None:
            raise NodeNotFoundError(node_id)

        # Check if trying to move root
        if node.tag == "book":
            raise InvalidOperationError("move_nodes", "Cannot move book element")

        # Check hierarchy validity
        if node.tag not in valid_hierarchy[new_parent.tag]:
            raise InvalidHierarchyError(new_parent.tag, node.tag)

        old_parent = node.getparent()
        old_parent.remove(node)
        new_parent.append(node)
        nodes_moved += 1

    hnpx.save_document(tree, file_path)

    return f"Moved {nodes_moved} nodes to parent {new_parent_id}"


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


def _render_paragraphs_recursive(node: etree.Element, show_ids: bool) -> list:
    """Recursively collect all paragraphs from node and its descendants"""
    paragraphs = []

    # Check if current node is a paragraph
    if node.tag == "paragraph":
        node_id = node.get("id", "")
        rendered_text = hnpx.render_paragraph(node)
        if rendered_text:
            if show_ids:
                paragraphs.append(f"[{node_id}] {rendered_text}")
            else:
                paragraphs.append(rendered_text)

    # Recursively process children (excluding summary)
    for child in node:
        if child.tag != "summary":
            paragraphs.extend(_render_paragraphs_recursive(child, show_ids))

    return paragraphs


def render_node(file_path: str, node_id: str, show_ids: bool = False) -> str:
    """Render text representation of the node (only descendent paragraphs)

    Args:
        file_path (str): Path to the HNPX document
        node_id (str): ID of the node to render
        show_ids (bool): Whether to show paragraph IDs in square brackets

    Returns:
        str: Formatted text representation the node
    """
    tree = hnpx.parse_document(file_path)
    node = hnpx.find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    paragraphs = _render_paragraphs_recursive(node, show_ids)
    return "\n\n".join(paragraphs)
