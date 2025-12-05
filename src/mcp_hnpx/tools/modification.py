"""
Node modification tools for HNPX MCP server.
"""

import logging
from typing import Any
from lxml import etree
from ..hnpx_utils import (
    parse_xml_file,
    is_valid_hnpx_document,
    find_node_by_id,
    validate_narrative_mode,
)
from ..errors import (
    NotHNPXError,
    NodeNotFoundError,
    ReadOnlyError,
    ValidationFailedError,
    ImmutableRootError,
)

logger = logging.getLogger(__name__)


def edit_node_attributes(
    file_path: str, node_id: str, attributes: dict[str, Any]
) -> dict:
    """
    Modifies attributes of an existing node.

    Args:
        file_path: Path to HNPX XML file
        node_id: ID of node to modify
        attributes: Key-value pairs of attributes to update

    Returns:
        Dictionary with modification result
    """
    logger.info("Editing attributes for node %s in file: %s", node_id, file_path)
    logger.debug("Attributes to update: %s", attributes)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for attribute editing: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        logger.error("Node with ID %s not found in file: %s", node_id, file_path)
        raise NodeNotFoundError(node_id)

    logger.debug("Found node: %s with ID: %s", node.tag, node_id)

    # Check if trying to modify ID
    if "id" in attributes:
        logger.error("Attempt to modify read-only attribute 'id' for node %s", node_id)
        raise ReadOnlyError("id")

    # Validate attributes based on node type
    if node.tag == "chapter" and "title" in attributes and not attributes["title"]:
        logger.error("Chapter title cannot be empty for node %s", node_id)
        raise ValidationFailedError("Chapter title cannot be empty")

    if node.tag == "sequence" and "loc" in attributes and not attributes["loc"]:
        logger.error("Sequence location cannot be empty for node %s", node_id)
        raise ValidationFailedError("Sequence location cannot be empty")

    if node.tag == "paragraph":
        mode = attributes.get("mode", node.get("mode", "narration"))
        char = attributes.get("char", node.get("char"))
        validate_narrative_mode(mode, char)
        logger.debug("Validated narrative mode for paragraph: %s, char: %s", mode, char)

        if mode == "dialogue" and not char:
            logger.error(
                "Dialogue paragraph missing character attribute for node %s", node_id
            )
            raise ValidationFailedError("Dialogue paragraphs must have char attribute")

    try:
        # Update attributes
        updated_attrs = {}
        for attr_name, attr_value in attributes.items():
            if attr_value is None or attr_value == "":
                # Remove attribute if value is None or empty string
                if attr_name in node.attrib:
                    del node.attrib[attr_name]
                    updated_attrs[attr_name] = None
                    logger.debug("Removed attribute: %s", attr_name)
            else:
                node.set(attr_name, str(attr_value))
                updated_attrs[attr_name] = str(attr_value)
                logger.debug("Set attribute: %s = %s", attr_name, str(attr_value))

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        logger.info(
            "Successfully saved document with updated attributes: %s", file_path
        )

        result = {
            "success": True,
            "node_id": node_id,
            "node_type": node.tag,
            "updated_attributes": updated_attrs,
            "message": f"Updated attributes for {node.tag} {node_id}",
        }
        logger.info("Attribute editing completed: %s", result["message"])
        return result
    except Exception as e:
        logger.error("Failed to edit attributes: %s", str(e))
        raise e


def remove_node(file_path: str, node_id: str) -> dict:
    """
    Permanently removes a node and all its descendants.

    Args:
        file_path: Path to HNPX XML file
        node_id: ID of node to remove

    Returns:
        Dictionary with removal result
    """
    logger.info("Removing node %s from file: %s", node_id, file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for node removal: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        logger.error("Node with ID %s not found in file: %s", node_id, file_path)
        raise NodeNotFoundError(node_id)

    logger.debug("Found node to remove: %s with ID: %s", node.tag, node_id)

    # Cannot remove root book element
    if node.tag == "book":
        logger.error("Attempt to remove immutable root book element: %s", node_id)
        raise ImmutableRootError()

    try:
        parent = node.getparent()
        logger.debug("Found parent node: %s", parent.tag if parent else "None")

        # Store information about what's being removed
        removed_info = {
            "node_id": node_id,
            "node_type": node.tag,
            "summary": node.findtext("summary", "").strip(),
        }
        logger.debug("Node to remove: %s", removed_info)

        # Remove the node
        parent.remove(node)
        logger.debug("Successfully removed node from parent")

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        logger.info("Successfully saved document after node removal: %s", file_path)

        removed_info["success"] = True
        removed_info["message"] = (
            f"Removed {node.tag} {node_id} and all its descendants"
        )
        logger.info("Node removal completed: %s", removed_info["message"])
        return removed_info
    except Exception as e:
        logger.error("Failed to remove node: %s", str(e))
        raise e


def reorder_children(file_path: str, parent_id: str, child_ids: list[str]) -> dict:
    """
    Reorganizes the order of child elements.

    Args:
        file_path: Path to HNPX XML file
        parent_id: ID of parent container
        child_ids: List of child IDs in desired order

    Returns:
        Dictionary with reorder result
    """
    logger.info("Reordering children for parent %s in file: %s", parent_id, file_path)
    logger.debug("New child order: %s", child_ids)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for child reordering: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    parent = find_node_by_id(root, parent_id)
    if parent is None:
        logger.error(
            "Parent node with ID %s not found in file: %s", parent_id, file_path
        )
        raise NodeNotFoundError(parent_id)

    logger.debug("Found parent node: %s with ID: %s", parent.tag, parent_id)

    # Get all current children (excluding summary)
    current_children = []
    child_map = {}

    for child in parent:
        if child.tag != "summary":
            child_id = child.get("id")
            if child_id:
                current_children.append(child)
                child_map[child_id] = child
                logger.debug("Found child: %s with ID: %s", child.tag, child_id)

    logger.debug("Found %d current children", len(current_children))

    # Validate that all specified IDs exist
    for child_id in child_ids:
        if child_id not in child_map:
            logger.error(
                "Child with ID %s not found under parent %s", child_id, parent_id
            )
            raise NodeNotFoundError(
                f"Child with id {child_id} not found under parent {parent_id}"
            )

    # Validate that all children are included
    if len(child_ids) != len(current_children):
        logger.error(
            "Child count mismatch: expected %d, got %d",
            len(current_children),
            len(child_ids),
        )
        raise ValidationFailedError("Must include all children in reorder list")

    try:
        # Remove all children (except summary)
        for child in list(parent):
            if child.tag != "summary":
                parent.remove(child)
        logger.debug("Removed all children from parent")

        # Re-add children in new order
        summary_elem = parent.find("summary")
        if summary_elem is not None:
            # Remove and re-add summary to ensure it's first
            summary_text = summary_elem.text
            parent.remove(summary_elem)
            new_summary = etree.SubElement(parent, "summary")
            new_summary.text = summary_text
            logger.debug("Re-added summary element first")

        # Add children in specified order
        for i, child_id in enumerate(child_ids):
            parent.append(child_map[child_id])
            logger.debug(
                "Re-added child %d: %s with ID: %s",
                i + 1,
                child_map[child_id].tag,
                child_id,
            )

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        logger.info(
            "Successfully saved document after reordering children: %s", file_path
        )

        result = {
            "success": True,
            "parent_id": parent_id,
            "parent_type": parent.tag,
            "new_order": child_ids,
            "message": f"Reordered children of {parent.tag} {parent_id}",
        }
        logger.info("Child reordering completed: %s", result["message"])
        return result
    except Exception as e:
        logger.error("Failed to reorder children: %s", str(e))
        raise e
