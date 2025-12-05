"""
Utility functions for HNPX document processing.
"""

import logging
import os
import random
import string
import time
from typing import Optional

from lxml import etree

from .errors import InvalidAttributeError, InvalidXMLError, MissingCharError

logger = logging.getLogger(__name__)

ID_CHARACTERS = string.ascii_lowercase + string.digits
ID_LENGTH = 6
NARRATIVE_MODES = {"narration", "dialogue", "internal"}
ALL_ELEMENTS = {"book", "chapter", "sequence", "beat", "paragraph", "summary"}
ELEMENT_HIERARCHY = {
    "book": ["chapter"],
    "chapter": ["sequence"],
    "sequence": ["beat"],
    "beat": ["paragraph"],
    "paragraph": [],
}


def generate_random_id(existing_ids: set[str] = None) -> str:
    """
    Generate a random 6-character ID using lowercase letters and digits.
    Keeps generating until a unique ID is found.
    """
    logger.debug(
        "Generating random ID with existing_ids count: %d",
        len(existing_ids) if existing_ids else 0,
    )

    if existing_ids is None:
        existing_ids = set()

    attempts = 0
    while True:
        attempts += 1
        new_id = "".join(random.choice(ID_CHARACTERS) for _ in range(ID_LENGTH))
        if new_id not in existing_ids:
            logger.debug("Generated unique ID '%s' after %d attempts", new_id, attempts)
            return new_id
        if attempts > 1000:  # Safety check
            logger.warning("Excessive attempts (%d) to generate unique ID", attempts)


def validate_id_format(node_id: str) -> bool:
    """Validate that ID follows HNPX specification."""
    logger.debug("Validating ID format for '%s'", node_id)

    if len(node_id) != ID_LENGTH:
        logger.debug(
            "ID '%s' invalid: length %d != %d", node_id, len(node_id), ID_LENGTH
        )
        return False

    is_valid = all(c in ID_CHARACTERS for c in node_id)
    logger.debug("ID '%s' format validation: %s", node_id, is_valid)
    return is_valid


def parse_xml_file(file_path: str) -> etree.Element:
    """Parse XML file with proper error handling."""
    logger.debug("Parsing XML file: %s", file_path)

    if not os.path.exists(file_path):
        logger.error("File not found: %s", file_path)
        raise FileNotFoundError(file_path)

    try:
        parser = etree.XMLParser(remove_blank_text=False, encoding="utf-8")
        root = etree.parse(file_path, parser).getroot()
        logger.debug(
            "Successfully parsed XML file: %s, root element: %s", file_path, root.tag
        )
        return root
    except etree.XMLSyntaxError as e:
        logger.error("XML syntax error in file %s: %s", file_path, str(e))
        raise InvalidXMLError(str(e))


def create_minimal_hnpx_document() -> etree.Element:
    """Create minimal valid HNPX document structure."""
    logger.debug("Creating minimal HNPX document")

    book_id = generate_random_id()
    logger.debug("Generated book ID: %s", book_id)

    root = etree.Element("book", id=book_id)
    summary = etree.SubElement(root, "summary")
    summary.text = "New book"

    logger.debug("Created minimal HNPX document with book ID: %s", book_id)
    return root


def format_xml_for_output(element: etree.Element) -> str:
    """Format XML element as pretty-printed string."""
    logger.debug("Formatting XML element for output: %s", element.tag)

    xml_str = etree.tostring(
        element, encoding="utf-8", pretty_print=True, xml_declaration=False
    ).decode("utf-8")

    logger.debug("Formatted XML string length: %d characters", len(xml_str))
    return xml_str


def get_all_ids(root: etree.Element) -> set[str]:
    """Extract all IDs from an XML document."""
    logger.debug("Extracting all IDs from document")

    ids = set()
    for element in root.xpath("//*[@id]"):
        node_id = element.get("id")
        if node_id:
            ids.add(node_id)

    logger.debug("Found %d unique IDs in document", len(ids))
    return ids


def is_valid_hnpx_document(root: etree.Element) -> bool:
    """Check if document follows HNPX basic structure."""
    logger.debug("Validating HNPX document structure")

    if root.tag != "book":
        logger.debug(
            "Document invalid: root element is '%s', expected 'book'", root.tag
        )
        return False

    book_id = root.get("id")
    if not book_id:
        logger.debug("Document invalid: book element missing 'id' attribute")
        return False

    summary = root.find("summary")
    if summary is None or summary.text is None or summary.text.strip() == "":
        logger.debug("Document invalid: book missing or empty summary")
        return False

    logger.debug("Document validation passed for book ID: %s", book_id)
    return True


def get_element_type(element: etree.Element) -> str:
    """Get the type of an element for error messages."""
    element_type = element.tag
    logger.debug("Element type: %s", element_type)
    return element_type


def create_backup_file(file_path: str) -> str:
    """Create a backup of the file before destructive operations."""
    backup_path = f"{file_path}.backup.{int(time.time())}"
    logger.debug("Creating backup file: %s", backup_path)

    try:
        with open(file_path, "r", encoding="utf-8") as src:
            content = src.read()
        with open(backup_path, "w", encoding="utf-8") as dst:
            dst.write(content)
        logger.debug("Successfully created backup file: %s", backup_path)
        return backup_path
    except Exception as e:
        logger.error("Failed to create backup file %s: %s", backup_path, str(e))
        return None


def cleanup_backup_file(backup_path: str):
    """Remove backup file after successful operation."""
    if backup_path and os.path.exists(backup_path):
        try:
            os.remove(backup_path)
            logger.debug("Successfully removed backup file: %s", backup_path)
        except Exception as e:
            logger.warning("Failed to remove backup file %s: %s", backup_path, str(e))


def validate_narrative_mode(mode: str, char: Optional[str]) -> None:
    """Validate narrative mode and character combination."""
    logger.debug("Validating narrative mode: %s, char: %s", mode, char)

    if mode not in NARRATIVE_MODES:
        logger.error(
            "Invalid narrative mode: %s, valid modes: %s", mode, NARRATIVE_MODES
        )
        raise InvalidAttributeError("mode", mode)

    if mode == "dialogue" and not char:
        logger.error("Dialogue mode requires character attribute")
        raise MissingCharError()

    logger.debug("Narrative mode validation passed")


def get_pov_for_paragraph(
    paragraph: etree.Element, root: etree.Element
) -> Optional[str]:
    """Get POV for a paragraph based on inheritance rules."""
    logger.debug("Getting POV for paragraph")

    char = paragraph.get("char")
    if char:
        logger.debug("Found direct character POV: %s", char)
        return char

    if paragraph.get("mode") == "internal":
        logger.debug("Searching for inherited POV for internal monologue")
        current = paragraph.getparent()
        level = 0
        while current is not None and current.tag != "book":
            pov = current.get("pov")
            if pov:
                logger.debug("Found inherited POV at level %d: %s", level, pov)
                return pov
            current = current.getparent()
            level += 1

    logger.debug("No POV found for paragraph")
    return None


def find_node_by_id(root: etree.Element, node_id: str) -> Optional[etree.Element]:
    """Find a node by its ID attribute."""
    logger.debug("Searching for node with ID: %s", node_id)

    nodes = root.xpath(f"//*[@id='{node_id}']")
    if nodes:
        logger.debug("Found node with ID %s: %s", node_id, nodes[0].tag)
        return nodes[0]
    else:
        logger.debug("Node with ID %s not found", node_id)
        return None


def get_parent_node(
    root: etree.Element, node: etree.Element
) -> Optional[etree.Element]:
    """Get the parent node of an element."""
    logger.debug("Getting parent node for element: %s", node.tag)

    parent = node.getparent()
    if parent is root or parent is None:
        logger.debug("No parent node found (element is root or has no parent)")
        return None

    logger.debug("Found parent node: %s", parent.tag)
    return parent


def get_required_children(element_type: str) -> list[str]:
    """Get the required child element types for a given element type."""
    logger.debug("Getting required children for element type: %s", element_type)

    required_children = ELEMENT_HIERARCHY.get(element_type, [])
    logger.debug("Required children for %s: %s", element_type, required_children)
    return required_children
