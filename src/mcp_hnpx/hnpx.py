import random
import string
from functools import cache
from pathlib import Path
from typing import Optional

from lxml import etree

from .exceptions import (
    ValidationError,
)


def load_schema() -> etree.XMLSchema:
    """Load HNPX schema from docs directory"""

    @cache
    def load_schema_doc() -> str:
        schema_path = Path(__file__).parent.parent.parent / "docs" / "HNPX.xml"
        return etree.parse(str(schema_path))

    return etree.XMLSchema(load_schema_doc())


def parse_document(file_path: str) -> etree.ElementTree:
    """Parse XML file and return ElementTree"""
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(file_path, parser)

    # Valudate document right after read
    validate_document(tree)

    return tree


def validate_document(tree: etree.ElementTree) -> None:
    """Validate document against schema, raise ValidationError if invalid"""
    schema = load_schema()
    if not schema.validate(tree):
        raise ValidationError(schema.error_log)

    error_log = []
    # Check dialogue paragraphs have char attribute
    for para in tree.xpath('//paragraph[@mode="dialogue"]'):
        if not para.get("char"):
            error_log.append(
                f"Dialogue paragraph {para.get('id')} missing char attribute"
            )

    # Check non-dialogue shouldn't have char
    for para in tree.xpath('//paragraph[@char][not(@mode="dialogue")]'):
        error_log.append(
            f"Paragraph {para.get('id')} has char but mode is {para.get('mode')}"
        )

    if len(error_log) > 0:
        raise ValidationError(error_log)


def save_document(tree: etree.ElementTree, file_path: str) -> None:
    """Save document to file with pretty printing"""

    # Validate document before saving
    validate_document(tree)

    tree.write(file_path, pretty_print=True, encoding="UTF-8", xml_declaration=True)


def get_all_ids(tree: etree.ElementTree) -> set:
    """Get all ID attributes in document"""
    return set(tree.xpath("//@id"))


def generate_unique_id(existing_ids: set) -> str:
    """Generate unique 6-character ID"""
    chars = string.ascii_lowercase + string.digits
    while True:
        new_id = "".join(random.choice(chars) for _ in range(6))
        if new_id not in existing_ids:
            return new_id


def find_node(tree: etree.ElementTree, node_id: str) -> Optional[etree.Element]:
    """Find node by ID, return None if not found"""
    nodes = tree.xpath(f"//*[@id='{node_id}']")
    return nodes[0] if nodes else None


def get_child_count(node: etree.Element) -> int:
    """Get count of children excluding summary"""
    return len([child for child in node if child.tag != "summary"])


def find_first_empty_container(
    tree: etree.ElementTree, start_node: Optional[etree.Element] = None
) -> Optional[etree.Element]:
    """
    Find first container node with no children (BFS order).
    Container nodes: book, chapter, sequence, beat

    Args:
        tree: The XML document tree
        start_node: If provided, search only within this node's subtree. If None, search from root.
    """
    if start_node is None:
        start_node = tree.getroot()

    queue = [start_node]

    while queue:
        node = queue.pop(0)

        # Check if this is a container node
        if node.tag in ["book", "chapter", "sequence", "beat"]:
            # Check if it has required children (excluding summary)
            if get_child_count(node) == 0:
                return node
        elif node.tag == "paragraph":
            # Check if paragraph has no text content
            if not (node.text or "").strip():
                return node

        # Add children to queue (BFS)
        queue.extend([child for child in node if child.tag != "summary"])

    return None


def render_paragraph(paragraph: etree.Element) -> str:
    """Render a single paragraph based on its mode"""
    text = (paragraph.text or "").strip()
    mode = paragraph.get("mode", "narration")
    char = paragraph.get("char", "")

    # Only render if there's actual text content
    if not text:
        return ""

    if mode == "dialogue" and char:
        return f'{char}: "{text}"'
    elif mode == "internal":
        return f"*{text}*"
    else:
        return text
