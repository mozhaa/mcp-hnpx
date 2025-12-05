"""
Navigation and discovery tools for HNPX MCP server.
"""

import os
from typing import Optional
from lxml import etree
from ..hnpx_utils import parse_xml_file, is_valid_hnpx_document, get_required_children
from ..errors import NotHNPXError, NodeNotFoundError


def get_next_empty_container(file_path: str) -> Optional[dict]:
    """
    Finds the next container node in BFS order that needs children.

    Args:
        file_path: Path to existing HNPX XML file

    Returns:
        Dictionary with id, type, and message of the empty container,
        or None if no empty containers exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    # BFS queue: (element, level)
    queue = [(root, 0)]

    while queue:
        element, level = queue.pop(0)

        # Check if this element needs children
        required_children = get_required_children(element.tag)
        if required_children:
            child_type = required_children[0]  # First required child type
            has_children = bool(element.find(child_type))

            if not has_children:
                return {
                    "id": element.get("id"),
                    "type": element.tag,
                    "message": f"{element.tag.capitalize()} has no {child_type}s",
                    "level": level,
                }

        # Add children to queue for BFS traversal
        for child in element:
            if child.tag != "summary":  # Skip summary elements
                queue.append((child, level + 1))

    return None


def get_node(file_path: str, node_id: str) -> str:
    """
    Retrieves XML representation of a specific node (without descendants).

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the node

    Returns:
        XML string of the node with attributes and summary only

    Raises:
        NodeNotFoundError: If node with given ID doesn't exist
    """
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    # Find the node
    target_element = None
    for element in root.xpath(f"//*[@id='{node_id}']"):
        target_element = element
        break

    if target_element is None:
        raise NodeNotFoundError(node_id)

    # Create a copy with only attributes and summary
    result = etree.Element(target_element.tag)

    # Copy attributes
    for attr_name, attr_value in target_element.attrib.items():
        result.set(attr_name, attr_value)

    # Find and copy summary element
    summary = target_element.find("summary")
    if summary is not None:
        summary_copy = etree.SubElement(result, "summary")
        summary_copy.text = summary.text

    # Format as XML string
    from ..hnpx_utils import format_xml_for_output

    return format_xml_for_output(result)
