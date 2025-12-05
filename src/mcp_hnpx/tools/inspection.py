"""
Node inspection tools for HNPX MCP server.
"""

import logging
from lxml import etree
from ..hnpx_utils import (
    parse_xml_file,
    is_valid_hnpx_document,
    find_node_by_id,
    format_xml_for_output,
)
from ..errors import NotHNPXError, NodeNotFoundError

logger = logging.getLogger(__name__)


def get_subtree(file_path: str, node_id: str) -> str:
    """
    Retrieves XML representation of a node including all its descendants.

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the root node

    Returns:
        Complete XML subtree as string
    """
    logger.info("Retrieving subtree for node ID: %s from file: %s", node_id, file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for subtree retrieval: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        logger.error("Node with ID %s not found in file: %s", node_id, file_path)
        raise NodeNotFoundError(node_id)

    logger.debug("Found node for subtree: %s with ID: %s", node.tag, node_id)

    subtree_xml = format_xml_for_output(node)
    logger.debug("Formatted subtree XML, length: %d characters", len(subtree_xml))
    return subtree_xml


def get_direct_children(file_path: str, node_id: str) -> str:
    """
    Retrieves immediate child nodes of a specified parent.

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the parent node

    Returns:
        XML containing all direct child elements
    """
    logger.info(
        "Retrieving direct children for node ID: %s from file: %s", node_id, file_path
    )

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for children retrieval: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    parent = find_node_by_id(root, node_id)
    if parent is None:
        logger.error("Parent node with ID %s not found in file: %s", node_id, file_path)
        raise NodeNotFoundError(node_id)

    logger.debug("Found parent node: %s with ID: %s", parent.tag, node_id)

    # Create container element
    container = etree.Element("children")
    child_count = 0

    # Add each direct child (excluding summary)
    for child in parent:
        if child.tag != "summary":
            container.append(child)
            child_count += 1
            logger.debug("Added child: %s with ID: %s", child.tag, child.get("id"))

    logger.debug("Found %d direct children for node %s", child_count, node_id)

    children_xml = format_xml_for_output(container)
    logger.debug("Formatted children XML, length: %d characters", len(children_xml))
    return children_xml


def get_node_path(file_path: str, node_id: str) -> str:
    """
    Returns the complete hierarchical path from document root to specified node.

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the target node

    Returns:
        XML containing each ancestor in order
    """
    logger.info("Retrieving path for node ID: %s from file: %s", node_id, file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for path retrieval: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        logger.error("Node with ID %s not found in file: %s", node_id, file_path)
        raise NodeNotFoundError(node_id)

    logger.debug("Found target node: %s with ID: %s", node.tag, node_id)

    # Build path from node to root
    path = []
    current = node
    path_length = 0

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
            path_length += 1
            logger.debug(
                "Added path element: %s with ID: %s", current.tag, current.get("id")
            )

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
    path_length += 1

    logger.debug("Built path with %d elements for node %s", path_length, node_id)

    # Create container
    container = etree.Element("path")
    for element in path:
        container.append(element)

    path_xml = format_xml_for_output(container)
    logger.debug("Formatted path XML, length: %d characters", len(path_xml))
    return path_xml


def get_node_context(file_path: str, node_id: str) -> dict:
    """
    Gets comprehensive context about a node including parent, children, and siblings.

    Args:
        file_path: Path to HNPX XML file
        node_id: Unique identifier of the target node

    Returns:
        Dictionary with node information and context
    """
    logger.info("Retrieving context for node ID: %s from file: %s", node_id, file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for context retrieval: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        logger.error("Node with ID %s not found in file: %s", node_id, file_path)
        raise NodeNotFoundError(node_id)

    logger.debug("Found target node: %s with ID: %s", node.tag, node_id)

    parent = node.getparent()
    siblings = []

    if parent is not None:
        logger.debug("Found parent node: %s with ID: %s", parent.tag, parent.get("id"))
        for child in parent:
            if child != node and child.tag != "summary":
                sibling_info = {
                    "id": child.get("id"),
                    "type": child.tag,
                    "summary": child.findtext("summary", "").strip(),
                }
                siblings.append(sibling_info)
                logger.debug(
                    "Found sibling: %s with ID: %s", child.tag, sibling_info["id"]
                )
        logger.debug("Found %d siblings for node %s", len(siblings), node_id)
    else:
        logger.debug("Node %s has no parent (is root)", node_id)

    children = []
    for child in node:
        if child.tag != "summary":
            child_info = {
                "id": child.get("id"),
                "type": child.tag,
                "summary": child.findtext("summary", "").strip(),
            }
            children.append(child_info)
            logger.debug("Found child: %s with ID: %s", child.tag, child_info["id"])
    logger.debug("Found %d children for node %s", len(children), node_id)

    context = {
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

    logger.debug(
        "Built context for node %s: %d children, %d siblings",
        node_id,
        len(children),
        len(siblings),
    )
    return context
