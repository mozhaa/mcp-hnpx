"""
XML schema validation for HNPX documents.
"""

import os
from lxml import etree
from .hnpx_utils import parse_xml_file


def validate_hnpx_with_schema(file_path: str, schema_file: str = None) -> list[str]:
    """
    Validate HNPX document against XML schema.

    Args:
        file_path: Path to HNPX XML file
        schema_file: Path to XSD schema file (default: use bundled schema)

    Returns:
        List of validation errors, empty if valid
    """
    try:
        # Parse the document
        xml_doc = parse_xml_file(file_path)

        # Load schema
        if schema_file is None:
            # Use default schema path (assuming it's in the same directory)
            schema_file = os.path.join(
                os.path.dirname(__file__), "..", "..", "docs", "HNPX.xml"
            )

        if not os.path.exists(schema_file):
            return [f"Schema file not found: {schema_file}"]

        schema_doc = etree.parse(schema_file)
        schema = etree.XMLSchema(schema_doc)

        # Validate
        if not schema.validate(xml_doc):
            errors = []
            for error in schema.error_log:
                errors.append(f"Line {error.line}: {error.message}")
            return errors

        return []
    except Exception as e:
        return [f"Validation error: {str(e)}"]


def validate_hnpx_basic(file_path: str) -> list[str]:
    """
    Perform basic HNPX validation without schema.

    Args:
        file_path: Path to HNPX XML file

    Returns:
        List of validation errors, empty if valid
    """
    errors = []

    try:
        root = parse_xml_file(file_path)

        # Check root element
        if root.tag != "book":
            errors.append("Root element must be 'book'")

        # Check book ID
        book_id = root.get("id")
        if not book_id:
            errors.append("Book element must have 'id' attribute")
        elif len(book_id) != 6 or not all(c.islower() or c.isdigit() for c in book_id):
            errors.append("Book ID must be exactly 6 lowercase letters/digits")

        # Check book summary
        book_summary = root.find("summary")
        if (
            book_summary is None
            or book_summary.text is None
            or book_summary.text.strip() == ""
        ):
            errors.append("Book must have a non-empty summary")

        # Collect all IDs for uniqueness check
        all_ids = set()

        # Validate hierarchy recursively
        def validate_element(element, parent_type: str = None) -> list[str]:
            elem_errors = []
            elem_id = element.get("id")

            # Check ID
            if elem_id:
                if elem_id in all_ids:
                    elem_errors.append(f"Duplicate ID: {elem_id}")
                else:
                    all_ids.add(elem_id)

                # Validate ID format for all elements with ID
                if len(elem_id) != 6 or not all(
                    c.islower() or c.isdigit() for c in elem_id
                ):
                    elem_errors.append(f"Invalid ID format: {elem_id}")

            # Check summary for container elements
            if element.tag in ["book", "chapter", "sequence", "beat", "paragraph"]:
                summary = element.find("summary")
                if summary is None:
                    elem_errors.append(f"{element.tag} missing summary")
                elif summary.text is None or summary.text.strip() == "":
                    elem_errors.append(f"{element.tag} has empty summary")

            # Element-specific validation
            if element.tag == "chapter":
                if not element.get("title"):
                    elem_errors.append("Chapter missing title attribute")

            elif element.tag == "sequence":
                if not element.get("loc"):
                    elem_errors.append("Sequence missing loc attribute")

            elif element.tag == "paragraph":
                mode = element.get("mode", "narration")
                if mode == "dialogue" and not element.get("char"):
                    elem_errors.append("Dialogue paragraph missing char attribute")

                if not element.text or element.text.strip() == "":
                    elem_errors.append("Paragraph has empty text content")

            # Validate children
            for child in element:
                if child.tag == "summary":
                    continue

                # Check hierarchy
                valid_children = {
                    "book": ["chapter"],
                    "chapter": ["sequence"],
                    "sequence": ["beat"],
                    "beat": ["paragraph"],
                    "paragraph": [],
                }

                if element.tag in valid_children:
                    if child.tag not in valid_children[element.tag]:
                        elem_errors.append(f"{element.tag} cannot contain {child.tag}")

                # Recursively validate child
                elem_errors.extend(validate_element(child, element.tag))

            return elem_errors

        errors.extend(validate_element(root))

    except Exception as e:
        errors.append(f"Validation error: {str(e)}")

    return errors
