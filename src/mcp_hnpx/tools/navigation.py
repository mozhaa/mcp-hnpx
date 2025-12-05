"""
Navigation and discovery tools for HNPX MCP server.
"""

import logging
import os
from typing import Optional
from lxml import etree
from ..hnpx_utils import parse_xml_file, is_valid_hnpx_document, get_required_children
from ..errors import NotHNPXError, NodeNotFoundError

logger = logging.getLogger(__name__)


def get_next_empty_container(file_path: str) -> Optional[dict]:
    """
    Finds the next container node in BFS order that needs children.

    Args:
        file_path: Path to existing HNPX XML file

    Returns:
        Dictionary with id, type, and message of the empty container,
        or None if no empty containers exist
    """
    logger.info("Finding next empty container in file: %s", file_path)

    if not os.path.exists(file_path):
        logger.error("File not found: %s", file_path)
        raise FileNotFoundError(file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for navigation: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    # BFS queue: (element, level)
    queue = [(root, 0)]
    elements_checked = 0

    while queue:
        element, level = queue.pop(0)
        elements_checked += 1
        logger.debug("Checking element: %s at level %d", element.tag, level)

        # Check if this element needs children
        required_children = get_required_children(element.tag)
        if required_children:
            child_type = required_children[0]  # First required child type
            has_children = bool(element.find(child_type))

            if not has_children:
                result = {
                    "id": element.get("id"),
                    "type": element.tag,
                    "message": f"{element.tag.capitalize()} has no {child_type}s",
                    "level": level,
                }
                logger.info(
                    "Found empty container: %s (ID: %s) after checking %d elements",
                    element.tag,
                    result["id"],
                    elements_checked,
                )
                return result

        # Add children to queue for BFS traversal
        for child in element:
            if child.tag != "summary":  # Skip summary elements
                queue.append((child, level + 1))

    logger.info(
        "No empty containers found after checking %d elements", elements_checked
    )
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
    logger.info("Retrieving node with ID: %s from file: %s", node_id, file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for node retrieval: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    # Find the node
    target_element = None
    elements = root.xpath(f"//*[@id='{node_id}']")
    for element in elements:
        target_element = element
        break

    if target_element is None:
        logger.error("Node with ID %s not found in file: %s", node_id, file_path)
        raise NodeNotFoundError(node_id)

    logger.debug("Found node: %s with ID: %s", target_element.tag, node_id)

    # Create a copy with only attributes and summary
    result = etree.Element(target_element.tag)

    # Copy attributes
    for attr_name, attr_value in target_element.attrib.items():
        result.set(attr_name, attr_value)
    logger.debug("Copied %d attributes from node", len(target_element.attrib))

    # Find and copy summary element
    summary = target_element.find("summary")
    if summary is not None:
        summary_copy = etree.SubElement(result, "summary")
        summary_copy.text = summary.text
        logger.debug("Copied summary element for node")

    # Format as XML string
    from ..hnpx_utils import format_xml_for_output

    xml_result = format_xml_for_output(result)
    logger.debug("Formatted node XML, length: %d characters", len(xml_result))
    return xml_result
