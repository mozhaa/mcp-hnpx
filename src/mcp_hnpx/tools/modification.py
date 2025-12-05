"""
Node modification tools for HNPX MCP server.
"""

from typing import Any
from lxml import etree
from ..hnpx_utils import (
    parse_xml_file,
    is_valid_hnpx_document,
    find_node_by_id,
    create_backup_file,
    cleanup_backup_file,
    validate_narrative_mode,
)
from ..errors import (
    NotHNPXError,
    NodeNotFoundError,
    ReadOnlyError,
    ValidationFailedError,
    ImmutableRootError,
)


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
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        raise NodeNotFoundError(node_id)

    # Check if trying to modify ID
    if "id" in attributes:
        raise ReadOnlyError("id")

    # Validate attributes based on node type
    if node.tag == "chapter" and "title" in attributes and not attributes["title"]:
        raise ValidationFailedError("Chapter title cannot be empty")

    if node.tag == "sequence" and "loc" in attributes and not attributes["loc"]:
        raise ValidationFailedError("Sequence location cannot be empty")

    if node.tag == "paragraph":
        mode = attributes.get("mode", node.get("mode", "narration"))
        char = attributes.get("char", node.get("char"))
        validate_narrative_mode(mode, char)

        if mode == "dialogue" and not char:
            raise ValidationFailedError("Dialogue paragraphs must have char attribute")

    # Create backup
    backup_path = create_backup_file(file_path)

    try:
        # Update attributes
        for attr_name, attr_value in attributes.items():
            if attr_value is None or attr_value == "":
                # Remove attribute if value is None or empty string
                if attr_name in node.attrib:
                    del node.attrib[attr_name]
            else:
                node.set(attr_name, str(attr_value))

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Clean up backup
        cleanup_backup_file(backup_path)

        return {
            "success": True,
            "node_id": node_id,
            "node_type": node.tag,
            "updated_attributes": attributes,
            "message": f"Updated attributes for {node.tag} {node_id}",
        }
    except Exception as e:
        # Restore from backup if available
        if backup_path:
            import os

            if os.path.exists(backup_path):
                with open(backup_path, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                os.remove(backup_path)
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
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        raise NodeNotFoundError(node_id)

    # Cannot remove root book element
    if node.tag == "book":
        raise ImmutableRootError()

    # Create backup
    backup_path = create_backup_file(file_path)

    try:
        parent = node.getparent()

        # Store information about what's being removed
        removed_info = {
            "node_id": node_id,
            "node_type": node.tag,
            "summary": node.findtext("summary", "").strip(),
        }

        # Remove the node
        parent.remove(node)

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Clean up backup
        cleanup_backup_file(backup_path)

        removed_info["success"] = True
        removed_info["message"] = (
            f"Removed {node.tag} {node_id} and all its descendants"
        )
        return removed_info
    except Exception as e:
        # Restore from backup if available
        if backup_path:
            import os

            if os.path.exists(backup_path):
                with open(backup_path, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                os.remove(backup_path)
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
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    parent = find_node_by_id(root, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    # Get all current children (excluding summary)
    current_children = []
    child_map = {}

    for child in parent:
        if child.tag != "summary":
            child_id = child.get("id")
            if child_id:
                current_children.append(child)
                child_map[child_id] = child

    # Validate that all specified IDs exist
    for child_id in child_ids:
        if child_id not in child_map:
            raise NodeNotFoundError(
                f"Child with id {child_id} not found under parent {parent_id}"
            )

    # Validate that all children are included
    if len(child_ids) != len(current_children):
        raise ValidationFailedError("Must include all children in reorder list")

    # Create backup
    backup_path = create_backup_file(file_path)

    try:
        # Remove all children (except summary)
        for child in list(parent):
            if child.tag != "summary":
                parent.remove(child)

        # Re-add children in new order
        summary_elem = parent.find("summary")
        if summary_elem is not None:
            # Remove and re-add summary to ensure it's first
            summary_text = summary_elem.text
            parent.remove(summary_elem)
            new_summary = etree.SubElement(parent, "summary")
            new_summary.text = summary_text

        # Add children in specified order
        for child_id in child_ids:
            parent.append(child_map[child_id])

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Clean up backup
        cleanup_backup_file(backup_path)

        return {
            "success": True,
            "parent_id": parent_id,
            "parent_type": parent.tag,
            "new_order": child_ids,
            "message": f"Reordered children of {parent.tag} {parent_id}",
        }
    except Exception as e:
        # Restore from backup if available
        if backup_path:
            import os

            if os.path.exists(backup_path):
                with open(backup_path, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                os.remove(backup_path)
        raise e
