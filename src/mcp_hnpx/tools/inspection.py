"""
Node inspection tools for HNPX MCP server.
"""

from lxml import etree
from ..hnpx_utils import (
    parse_xml_file,
    is_valid_hnpx_document,
    find_node_by_id,
    format_xml_for_output,
)
from ..errors import NotHNPXError, NodeNotFoundError


def get_subtree(file_path: str, node_id: str) -> str:
    """
    Retrieves XML representation of a node including all its descendants.

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the root node

    Returns:
        Complete XML subtree as string
    """
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        raise NodeNotFoundError(node_id)

    return format_xml_for_output(node)


def get_direct_children(file_path: str, node_id: str) -> str:
    """
    Retrieves immediate child nodes of a specified parent.

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the parent node

    Returns:
        XML containing all direct child elements
    """
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    parent = find_node_by_id(root, node_id)
    if parent is None:
        raise NodeNotFoundError(node_id)

    # Create container element
    container = etree.Element("children")

    # Add each direct child (excluding summary)
    for child in parent:
        if child.tag != "summary":
            container.append(child)

    return format_xml_for_output(container)


def get_node_path(file_path: str, node_id: str) -> str:
    """
    Returns the complete hierarchical path from document root to specified node.

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the target node

    Returns:
        XML containing each ancestor in order
    """
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        raise NodeNotFoundError(node_id)

    # Build path from node to root
    path = []
    current = node

    while current is not None and current != root:
        if current.tag != "summary":  # Skip summary elements
            # Create a copy with only attributes and summary
            element_copy = etree.Element(current.tag)
            for attr_name, attr_value in current.attrib.items():
                element_copy.set(attr_name, attr_value)

            summary = current.find("summary")
            if summary is not None:
                summary_copy = etree.SubElement(element_copy, "summary")
                summary_copy.text = summary.text

            path.insert(0, element_copy)

        current = current.getparent()

    # Add root element
    root_copy = etree.Element(root.tag)
    for attr_name, attr_value in root.attrib.items():
        root_copy.set(attr_name, attr_value)

    root_summary = root.find("summary")
    if root_summary is not None:
        summary_copy = etree.SubElement(root_copy, "summary")
        summary_copy.text = root_summary.text

    path.insert(0, root_copy)

    # Create container
    container = etree.Element("path")
    for element in path:
        container.append(element)

    return format_xml_for_output(container)


def get_node_context(file_path: str, node_id: str) -> dict:
    """
    Gets comprehensive context about a node including parent, children, and siblings.

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the target node

    Returns:
        Dictionary with node information and context
    """
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        raise NodeNotFoundError(node_id)

    parent = node.getparent()
    siblings = []

    if parent is not None:
        for child in parent:
            if child != node and child.tag != "summary":
                siblings.append(
                    {
                        "id": child.get("id"),
                        "type": child.tag,
                        "summary": child.findtext("summary", "").strip(),
                    }
                )

    children = []
    for child in node:
        if child.tag != "summary":
            children.append(
                {
                    "id": child.get("id"),
                    "type": child.tag,
                    "summary": child.findtext("summary", "").strip(),
                }
            )

    return {
        "node": {
            "id": node_id,
            "type": node.tag,
            "summary": node.findtext("summary", "").strip(),
            "attributes": dict(node.attrib),
        },
        "parent": {
            "id": parent.get("id") if parent is not None else None,
            "type": parent.tag if parent is not None else None,
        }
        if parent is not None
        else None,
        "children": children,
        "siblings": siblings,
    }
