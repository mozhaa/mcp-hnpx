"""
Node creation tools for HNPX MCP server.
"""

from lxml import etree
from ..hnpx_utils import (
    parse_xml_file,
    is_valid_hnpx_document,
    find_node_by_id,
    generate_random_id,
    get_all_ids,
    validate_narrative_mode,
    create_backup_file,
    cleanup_backup_file,
)
from ..errors import (
    NotHNPXError,
    NodeNotFoundError,
    InvalidParentError,
    MissingAttributeError,
    ValidationFailedError,
)


def _validate_parent_child(parent: etree.Element, child_type: str) -> None:
    """Validate that parent can accept the specified child type."""
    valid_children = {
        "book": ["chapter"],
        "chapter": ["sequence"],
        "sequence": ["beat"],
        "beat": ["paragraph"],
    }

    parent_type = parent.tag
    if parent_type not in valid_children:
        raise InvalidParentError(parent_type, child_type)

    if child_type not in valid_children[parent_type]:
        raise InvalidParentError(parent_type, child_type)


def _check_duplicate_title(parent: etree.Element, title: str, child_type: str) -> None:
    """Check for duplicate titles among siblings."""
    if child_type != "chapter":
        return

    for chapter in parent.findall("chapter"):
        if chapter.get("title") == title:
            raise ValidationFailedError(
                f"Chapter title must be unique within book: '{title}'"
            )


def create_chapter(
    file_path: str, parent_id: str, title: str, summary: str, pov: str = None
) -> dict:
    """
    Creates a new chapter element.

    Args:
        file_path: Path to HNPX XML file
        parent_id: ID of parent book element
        title: Chapter title
        summary: Chapter summary
        pov: Point-of-view character identifier

    Returns:
        Dictionary with created chapter information
    """
    if not title or not summary:
        raise MissingAttributeError(
            "title and summary"
            if not title and not summary
            else "title"
            if not title
            else "summary"
        )

    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    parent = find_node_by_id(root, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    _validate_parent_child(parent, "chapter")
    _check_duplicate_title(parent, title, "chapter")

    # Get all existing IDs
    existing_ids = get_all_ids(root)

    # Generate unique ID
    chapter_id = generate_random_id(existing_ids)

    # Create backup
    backup_path = create_backup_file(file_path)

    try:
        # Create chapter element
        chapter_attrib = {"id": chapter_id, "title": title}
        if pov:
            chapter_attrib["pov"] = pov

        chapter = etree.SubElement(parent, "chapter", chapter_attrib)

        # Add summary
        summary_elem = etree.SubElement(chapter, "summary")
        summary_elem.text = summary

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
            "chapter_id": chapter_id,
            "title": title,
            "summary": summary,
            "pov": pov,
            "message": f"Created chapter '{title}' with ID {chapter_id}",
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


def create_sequence(
    file_path: str,
    parent_id: str,
    location: str,
    summary: str,
    time: str = None,
    pov: str = None,
) -> dict:
    """
    Creates a new sequence element.

    Args:
        file_path: Path to HNPX XML file
        parent_id: ID of parent chapter element
        location: Where the sequence takes place
        summary: Sequence summary
        time: Time indicator
        pov: Overrides chapter POV if present

    Returns:
        Dictionary with created sequence information
    """
    if not location or not summary:
        raise MissingAttributeError(
            "location and summary"
            if not location and not summary
            else "location"
            if not location
            else "summary"
        )

    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    parent = find_node_by_id(root, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    _validate_parent_child(parent, "sequence")

    # Get all existing IDs
    existing_ids = get_all_ids(root)

    # Generate unique ID
    sequence_id = generate_random_id(existing_ids)

    # Create backup
    backup_path = create_backup_file(file_path)

    try:
        # Create sequence element
        sequence_attrib = {"id": sequence_id, "loc": location}
        if time:
            sequence_attrib["time"] = time
        if pov:
            sequence_attrib["pov"] = pov

        sequence = etree.SubElement(parent, "sequence", sequence_attrib)

        # Add summary
        summary_elem = etree.SubElement(sequence, "summary")
        summary_elem.text = summary

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
            "sequence_id": sequence_id,
            "location": location,
            "summary": summary,
            "time": time,
            "pov": pov,
            "message": f"Created sequence at '{location}' with ID {sequence_id}",
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


def create_beat(file_path: str, parent_id: str, summary: str) -> dict:
    """
    Creates a new beat element.

    Args:
        file_path: Path to HNPX XML file
        parent_id: ID of parent sequence element
        summary: Beat summary

    Returns:
        Dictionary with created beat information
    """
    if not summary:
        raise MissingAttributeError("summary")

    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    parent = find_node_by_id(root, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    _validate_parent_child(parent, "beat")

    # Get all existing IDs
    existing_ids = get_all_ids(root)

    # Generate unique ID
    beat_id = generate_random_id(existing_ids)

    # Create backup
    backup_path = create_backup_file(file_path)

    try:
        # Create beat element
        beat = etree.SubElement(parent, "beat", id=beat_id)

        # Add summary
        summary_elem = etree.SubElement(beat, "summary")
        summary_elem.text = summary

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
            "beat_id": beat_id,
            "summary": summary,
            "message": f"Created beat with ID {beat_id}",
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


def create_paragraph(
    file_path: str,
    parent_id: str,
    summary: str,
    text: str,
    mode: str = "narration",
    char: str = None,
) -> dict:
    """
    Creates a new paragraph element.

    Args:
        file_path: Path to HNPX XML file
        parent_id: ID of parent beat element
        summary: Paragraph summary
        text: Paragraph text content
        mode: "narration", "dialogue", or "internal"
        char: Character identifier

    Returns:
        Dictionary with created paragraph information
    """
    if not summary or not text:
        raise MissingAttributeError(
            "summary and text"
            if not summary and not text
            else "summary"
            if not summary
            else "text"
        )

    # Validate mode and char combination
    validate_narrative_mode(mode, char)

    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    parent = find_node_by_id(root, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    _validate_parent_child(parent, "paragraph")

    # Get all existing IDs
    existing_ids = get_all_ids(root)

    # Generate unique ID
    paragraph_id = generate_random_id(existing_ids)

    # Create backup
    backup_path = create_backup_file(file_path)

    try:
        # Create paragraph element
        paragraph_attrib = {"id": paragraph_id}
        if mode != "narration":
            paragraph_attrib["mode"] = mode
        if char:
            paragraph_attrib["char"] = char

        paragraph = etree.SubElement(parent, "paragraph", paragraph_attrib)

        # Add summary
        summary_elem = etree.SubElement(paragraph, "summary")
        summary_elem.text = summary

        # Add text content
        paragraph.text = text

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
            "paragraph_id": paragraph_id,
            "summary": summary,
            "text": text,
            "mode": mode,
            "char": char,
            "message": f"Created paragraph with ID {paragraph_id}",
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
