"""
Utility functions for HNPX document processing.
"""

import os
import random
import string
import time
from typing import Optional

from lxml import etree

from .errors import InvalidAttributeError, InvalidXMLError, MissingCharError

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
    if existing_ids is None:
        existing_ids = set()

    while True:
        new_id = "".join(random.choice(ID_CHARACTERS) for _ in range(ID_LENGTH))
        if new_id not in existing_ids:
            return new_id


def validate_id_format(node_id: str) -> bool:
    """Validate that ID follows HNPX specification."""
    if len(node_id) != ID_LENGTH:
        return False
    return all(c in ID_CHARACTERS for c in node_id)


def parse_xml_file(file_path: str) -> etree.Element:
    """Parse XML file with proper error handling."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    try:
        parser = etree.XMLParser(remove_blank_text=False, encoding="utf-8")
        return etree.parse(file_path, parser).getroot()
    except etree.XMLSyntaxError as e:
        raise InvalidXMLError(str(e))


def create_minimal_hnpx_document() -> etree.Element:
    """Create minimal valid HNPX document structure."""
    book_id = generate_random_id()

    root = etree.Element("book", id=book_id)
    summary = etree.SubElement(root, "summary")
    summary.text = "New book"

    return root


def format_xml_for_output(element: etree.Element) -> str:
    """Format XML element as pretty-printed string."""
    return etree.tostring(
        element, encoding="utf-8", pretty_print=True, xml_declaration=False
    ).decode("utf-8")


def get_all_ids(root: etree.Element) -> set[str]:
    """Extract all IDs from an XML document."""
    ids = set()
    for element in root.xpath("//*[@id]"):
        node_id = element.get("id")
        if node_id:
            ids.add(node_id)
    return ids


def is_valid_hnpx_document(root: etree.Element) -> bool:
    """Check if document follows HNPX basic structure."""
    if root.tag != "book":
        return False

    if not root.get("id"):
        return False

    summary = root.find("summary")
    if summary is None or summary.text is None or summary.text.strip() == "":
        return False

    return True


def get_element_type(element: etree.Element) -> str:
    """Get the type of an element for error messages."""
    return element.tag


def create_backup_file(file_path: str) -> str:
    """Create a backup of the file before destructive operations."""
    backup_path = f"{file_path}.backup.{int(time.time())}"

    try:
        with open(file_path, "r", encoding="utf-8") as src:
            content = src.read()
        with open(backup_path, "w", encoding="utf-8") as dst:
            dst.write(content)
        return backup_path
    except Exception:
        return None


def cleanup_backup_file(backup_path: str):
    """Remove backup file after successful operation."""
    if backup_path and os.path.exists(backup_path):
        try:
            os.remove(backup_path)
        except Exception:
            pass


def validate_narrative_mode(mode: str, char: Optional[str]) -> None:
    """Validate narrative mode and character combination."""
    if mode not in NARRATIVE_MODES:
        raise InvalidAttributeError("mode", mode)

    if mode == "dialogue" and not char:
        raise MissingCharError()


def get_pov_for_paragraph(
    paragraph: etree.Element, root: etree.Element
) -> Optional[str]:
    """Get POV for a paragraph based on inheritance rules."""
    char = paragraph.get("char")
    if char:
        return char

    if paragraph.get("mode") == "internal":
        current = paragraph.getparent()
        while current is not None and current.tag != "book":
            pov = current.get("pov")
            if pov:
                return pov
            current = current.getparent()

    return None


def find_node_by_id(root: etree.Element, node_id: str) -> Optional[etree.Element]:
    """Find a node by its ID attribute."""
    return (
        root.xpath(f"//*[@id='{node_id}']")[0]
        if root.xpath(f"//*[@id='{node_id}']")
        else None
    )


def get_parent_node(
    root: etree.Element, node: etree.Element
) -> Optional[etree.Element]:
    """Get the parent node of an element."""
    parent = node.getparent()
    if parent is root or parent is None:
        return None
    return parent


def get_required_children(element_type: str) -> list[str]:
    """Get the required child element types for a given element type."""
    return ELEMENT_HIERARCHY.get(element_type, [])
