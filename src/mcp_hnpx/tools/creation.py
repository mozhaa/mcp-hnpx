"""
Node creation tools for HNPX MCP server.
"""

import logging
from lxml import etree
from ..hnpx_utils import (
    parse_xml_file,
    is_valid_hnpx_document,
    find_node_by_id,
    generate_random_id,
    get_all_ids,
    validate_narrative_mode,
)
from ..errors import (
    NotHNPXError,
    NodeNotFoundError,
    InvalidParentError,
    MissingAttributeError,
    ValidationFailedError,
)

logger = logging.getLogger(__name__)


def _validate_parent_child(parent: etree.Element, child_type: str) -> None:
    """Validate that parent can accept the specified child type."""
    logger.debug(
        "Validating parent-child relationship: %s -> %s", parent.tag, child_type
    )

    valid_children = {
        "book": ["chapter"],
        "chapter": ["sequence"],
        "sequence": ["beat"],
        "beat": ["paragraph"],
    }

    parent_type = parent.tag
    if parent_type not in valid_children:
        logger.error("Invalid parent type: %s", parent_type)
        raise InvalidParentError(parent_type, child_type)

    if child_type not in valid_children[parent_type]:
        logger.error("Invalid child type %s for parent %s", child_type, parent_type)
        raise InvalidParentError(parent_type, child_type)

    logger.debug("Parent-child validation passed: %s -> %s", parent_type, child_type)


def _check_duplicate_title(parent: etree.Element, title: str, child_type: str) -> None:
    """Check for duplicate titles among siblings."""
    logger.debug("Checking for duplicate title: '%s' in %s elements", title, child_type)

    if child_type != "chapter":
        logger.debug(
            "Skipping duplicate title check for non-chapter element: %s", child_type
        )
        return

    for chapter in parent.findall("chapter"):
        if chapter.get("title") == title:
            logger.error("Duplicate chapter title found: '%s'", title)
            raise ValidationFailedError(
                f"Chapter title must be unique within book: '{title}'"
            )

    logger.debug("No duplicate titles found for: '%s'", title)


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
    logger.info(
        "Creating chapter with title '%s' in parent %s, file: %s",
        title,
        parent_id,
        file_path,
    )

    if not title or not summary:
        missing_attr = (
            "title and summary"
            if not title and not summary
            else "title"
            if not title
            else "summary"
        )
        logger.error("Missing required attribute: %s", missing_attr)
        raise MissingAttributeError(missing_attr)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for chapter creation: %s", file_path)

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

    _validate_parent_child(parent, "chapter")
    _check_duplicate_title(parent, title, "chapter")

    # Get all existing IDs
    existing_ids = get_all_ids(root)
    logger.debug("Found %d existing IDs in document", len(existing_ids))

    # Generate unique ID
    chapter_id = generate_random_id(existing_ids)
    logger.debug("Generated chapter ID: %s", chapter_id)

    try:
        # Create chapter element
        chapter_attrib = {"id": chapter_id, "title": title}
        if pov:
            chapter_attrib["pov"] = pov
            logger.debug("Chapter POV: %s", pov)

        chapter = etree.SubElement(parent, "chapter", chapter_attrib)
        logger.debug("Created chapter element with ID: %s", chapter_id)

        # Add summary
        summary_elem = etree.SubElement(chapter, "summary")
        summary_elem.text = summary
        logger.debug("Added chapter summary")

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        logger.info("Successfully saved document with new chapter: %s", file_path)

        result = {
            "success": True,
            "chapter_id": chapter_id,
            "title": title,
            "summary": summary,
            "pov": pov,
            "message": f"Created chapter '{title}' with ID {chapter_id}",
        }
        logger.info("Chapter creation completed: %s", result["message"])
        return result
    except Exception as e:
        logger.error("Failed to create chapter: %s", str(e))
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
    logger.info(
        "Creating sequence at location '%s' in parent %s, file: %s",
        location,
        parent_id,
        file_path,
    )

    if not location or not summary:
        missing_attr = (
            "location and summary"
            if not location and not summary
            else "location"
            if not location
            else "summary"
        )
        logger.error("Missing required attribute: %s", missing_attr)
        raise MissingAttributeError(missing_attr)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for sequence creation: %s", file_path)

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

    _validate_parent_child(parent, "sequence")

    # Get all existing IDs
    existing_ids = get_all_ids(root)
    logger.debug("Found %d existing IDs in document", len(existing_ids))

    # Generate unique ID
    sequence_id = generate_random_id(existing_ids)
    logger.debug("Generated sequence ID: %s", sequence_id)

    try:
        # Create sequence element
        sequence_attrib = {"id": sequence_id, "loc": location}
        if time:
            sequence_attrib["time"] = time
            logger.debug("Sequence time: %s", time)
        if pov:
            sequence_attrib["pov"] = pov
            logger.debug("Sequence POV: %s", pov)

        sequence = etree.SubElement(parent, "sequence", sequence_attrib)
        logger.debug("Created sequence element with ID: %s", sequence_id)

        # Add summary
        summary_elem = etree.SubElement(sequence, "summary")
        summary_elem.text = summary
        logger.debug("Added sequence summary")

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        logger.info("Successfully saved document with new sequence: %s", file_path)

        result = {
            "success": True,
            "sequence_id": sequence_id,
            "location": location,
            "summary": summary,
            "time": time,
            "pov": pov,
            "message": f"Created sequence at '{location}' with ID {sequence_id}",
        }
        logger.info("Sequence creation completed: %s", result["message"])
        return result
    except Exception as e:
        logger.error("Failed to create sequence: %s", str(e))
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
    logger.info("Creating beat in parent %s, file: %s", parent_id, file_path)

    if not summary:
        logger.error("Missing required attribute: summary")
        raise MissingAttributeError("summary")

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for beat creation: %s", file_path)

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

    _validate_parent_child(parent, "beat")

    # Get all existing IDs
    existing_ids = get_all_ids(root)
    logger.debug("Found %d existing IDs in document", len(existing_ids))

    # Generate unique ID
    beat_id = generate_random_id(existing_ids)
    logger.debug("Generated beat ID: %s", beat_id)

    try:
        # Create beat element
        beat = etree.SubElement(parent, "beat", id=beat_id)
        logger.debug("Created beat element with ID: %s", beat_id)

        # Add summary
        summary_elem = etree.SubElement(beat, "summary")
        summary_elem.text = summary
        logger.debug("Added beat summary")

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        logger.info("Successfully saved document with new beat: %s", file_path)

        result = {
            "success": True,
            "beat_id": beat_id,
            "summary": summary,
            "message": f"Created beat with ID {beat_id}",
        }
        logger.info("Beat creation completed: %s", result["message"])
        return result
    except Exception as e:
        logger.error("Failed to create beat: %s", str(e))
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
    logger.info(
        "Creating paragraph with mode '%s' in parent %s, file: %s",
        mode,
        parent_id,
        file_path,
    )

    if not summary or not text:
        missing_attr = (
            "summary and text"
            if not summary and not text
            else "summary"
            if not summary
            else "text"
        )
        logger.error("Missing required attribute: %s", missing_attr)
        raise MissingAttributeError(missing_attr)

    # Validate mode and char combination
    validate_narrative_mode(mode, char)
    logger.debug("Validated narrative mode: %s, char: %s", mode, char)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for paragraph creation: %s", file_path)

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

    _validate_parent_child(parent, "paragraph")

    # Get all existing IDs
    existing_ids = get_all_ids(root)
    logger.debug("Found %d existing IDs in document", len(existing_ids))

    # Generate unique ID
    paragraph_id = generate_random_id(existing_ids)
    logger.debug("Generated paragraph ID: %s", paragraph_id)

    try:
        # Create paragraph element
        paragraph_attrib = {"id": paragraph_id}
        if mode != "narration":
            paragraph_attrib["mode"] = mode
            logger.debug("Paragraph mode: %s", mode)
        if char:
            paragraph_attrib["char"] = char
            logger.debug("Paragraph character: %s", char)

        paragraph = etree.SubElement(parent, "paragraph", paragraph_attrib)
        logger.debug("Created paragraph element with ID: %s", paragraph_id)

        # Add summary
        summary_elem = etree.SubElement(paragraph, "summary")
        summary_elem.text = summary
        logger.debug("Added paragraph summary")

        # Add text content
        paragraph.text = text
        logger.debug("Added paragraph text content (length: %d)", len(text))

        # Save document
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        logger.info("Successfully saved document with new paragraph: %s", file_path)

        result = {
            "success": True,
            "paragraph_id": paragraph_id,
            "summary": summary,
            "text": text,
            "mode": mode,
            "char": char,
            "message": f"Created paragraph with ID {paragraph_id}",
        }
        logger.info("Paragraph creation completed: %s", result["message"])
        return result
    except Exception as e:
        logger.error("Failed to create paragraph: %s", str(e))
        raise e
