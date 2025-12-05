"""
XML schema validation for HNPX documents.
"""

import logging
import os
from lxml import etree
from .hnpx_utils import parse_xml_file

logger = logging.getLogger(__name__)


def validate_hnpx_with_schema(file_path: str, schema_file: str = None) -> list[str]:
    """
    Validate HNPX document against XML schema.

    Args:
        file_path: Path to HNPX XML file
        schema_file: Path to XSD schema file (default: use bundled schema)

    Returns:
        List of validation errors, empty if valid
    """
    logger.info("Starting schema validation for file: %s", file_path)

    try:
        # Parse the document
        xml_doc = parse_xml_file(file_path)
        logger.debug("Successfully parsed XML document for schema validation")

        # Load schema
        if schema_file is None:
            # Use default schema path (assuming it's in the same directory)
            schema_file = os.path.join(
                os.path.dirname(__file__), "..", "..", "docs", "HNPX.xml"
            )

        logger.debug("Using schema file: %s", schema_file)

        if not os.path.exists(schema_file):
            logger.error("Schema file not found: %s", schema_file)
            return [f"Schema file not found: {schema_file}"]

        schema_doc = etree.parse(schema_file)
        schema = etree.XMLSchema(schema_doc)
        logger.debug("Successfully loaded XML schema")

        # Validate
        if not schema.validate(xml_doc):
            errors = []
            for error in schema.error_log:
                error_msg = f"Line {error.line}: {error.message}"
                errors.append(error_msg)
                logger.warning("Schema validation error: %s", error_msg)
            logger.error("Schema validation failed with %d errors", len(errors))
            return errors

        logger.info("Schema validation passed successfully")
        return []
    except Exception as e:
        logger.error("Exception during schema validation: %s", str(e))
        return [f"Validation error: {str(e)}"]


def validate_hnpx_basic(file_path: str) -> list[str]:
    """
    Perform basic HNPX validation without schema.

    Args:
        file_path: Path to HNPX XML file

    Returns:
        List of validation errors, empty if valid
    """
    logger.info("Starting basic validation for file: %s", file_path)
    errors = []

    try:
        root = parse_xml_file(file_path)
        logger.debug("Successfully parsed XML document for basic validation")

        # Check root element
        if root.tag != "book":
            error_msg = "Root element must be 'book'"
            errors.append(error_msg)
            logger.error("Root element validation failed: %s", error_msg)

        # Check book ID
        book_id = root.get("id")
        if not book_id:
            error_msg = "Book element must have 'id' attribute"
            errors.append(error_msg)
            logger.error("Book ID validation failed: %s", error_msg)
        elif len(book_id) != 6 or not all(c.islower() or c.isdigit() for c in book_id):
            error_msg = "Book ID must be exactly 6 lowercase letters/digits"
            errors.append(error_msg)
            logger.error("Book ID format validation failed: %s", error_msg)
        else:
            logger.debug("Book ID validation passed: %s", book_id)

        # Check book summary
        book_summary = root.find("summary")
        if (
            book_summary is None
            or book_summary.text is None
            or book_summary.text.strip() == ""
        ):
            error_msg = "Book must have a non-empty summary"
            errors.append(error_msg)
            logger.error("Book summary validation failed: %s", error_msg)
        else:
            logger.debug("Book summary validation passed")

        # Collect all IDs for uniqueness check
        all_ids = set()
        element_count = 0

        # Validate hierarchy recursively
        def validate_element(element, parent_type: str = None) -> list[str]:
            nonlocal element_count
            element_count += 1
            elem_errors = []
            elem_id = element.get("id")

            # Check ID
            if elem_id:
                if elem_id in all_ids:
                    error_msg = f"Duplicate ID: {elem_id}"
                    elem_errors.append(error_msg)
                    logger.error("ID validation failed: %s", error_msg)
                else:
                    all_ids.add(elem_id)
                    logger.debug("Added unique ID: %s", elem_id)

                # Validate ID format for all elements with ID
                if len(elem_id) != 6 or not all(
                    c.islower() or c.isdigit() for c in elem_id
                ):
                    error_msg = f"Invalid ID format: {elem_id}"
                    elem_errors.append(error_msg)
                    logger.error("ID format validation failed: %s", error_msg)

            # Check summary for container elements
            if element.tag in ["book", "chapter", "sequence", "beat", "paragraph"]:
                summary = element.find("summary")
                if summary is None:
                    error_msg = f"{element.tag} missing summary"
                    elem_errors.append(error_msg)
                    logger.error("Summary validation failed: %s", error_msg)
                elif summary.text is None or summary.text.strip() == "":
                    error_msg = f"{element.tag} has empty summary"
                    elem_errors.append(error_msg)
                    logger.error("Summary content validation failed: %s", error_msg)
                else:
                    logger.debug("Summary validation passed for %s", element.tag)

            # Element-specific validation
            if element.tag == "chapter":
                if not element.get("title"):
                    error_msg = "Chapter missing title attribute"
                    elem_errors.append(error_msg)
                    logger.error("Chapter title validation failed: %s", error_msg)
                else:
                    logger.debug("Chapter title validation passed")

            elif element.tag == "sequence":
                if not element.get("loc"):
                    error_msg = "Sequence missing loc attribute"
                    elem_errors.append(error_msg)
                    logger.error("Sequence location validation failed: %s", error_msg)
                else:
                    logger.debug("Sequence location validation passed")

            elif element.tag == "paragraph":
                mode = element.get("mode", "narration")
                if mode == "dialogue" and not element.get("char"):
                    error_msg = "Dialogue paragraph missing char attribute"
                    elem_errors.append(error_msg)
                    logger.error("Paragraph dialogue validation failed: %s", error_msg)

                if not element.text or element.text.strip() == "":
                    error_msg = "Paragraph has empty text content"
                    elem_errors.append(error_msg)
                    logger.error("Paragraph text validation failed: %s", error_msg)
                else:
                    logger.debug("Paragraph validation passed")

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
                        error_msg = f"{element.tag} cannot contain {child.tag}"
                        elem_errors.append(error_msg)
                        logger.error("Hierarchy validation failed: %s", error_msg)

                # Recursively validate child
                elem_errors.extend(validate_element(child, element.tag))

            return elem_errors

        errors.extend(validate_element(root))
        logger.info(
            "Basic validation completed: %d elements checked, %d errors found",
            element_count,
            len(errors),
        )

    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        errors.append(error_msg)
        logger.error("Exception during basic validation: %s", str(e))

    return errors
