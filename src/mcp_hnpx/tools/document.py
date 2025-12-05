"""
Document management tools for HNPX MCP server.
"""

import logging
import os
from ..hnpx_utils import create_minimal_hnpx_document, format_xml_for_output
from ..errors import FileExistsError

logger = logging.getLogger(__name__)


def create_document(file_path: str) -> dict:
    """
    Creates a new empty HNPX document with a root <book> element.

    Args:
        file_path: Absolute or relative path where the document will be created

    Returns:
        Dictionary with success message and created file path

    Raises:
        FileExistsError: If file already exists
        OSError: If cannot create file at path
    """
    logger.info("Creating new HNPX document at: %s", file_path)

    if os.path.exists(file_path):
        logger.error("File already exists at: %s", file_path)
        raise FileExistsError(file_path)

    try:
        root = create_minimal_hnpx_document()
        book_id = root.get("id")
        logger.debug("Created minimal HNPX document with book ID: %s", book_id)

        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += format_xml_for_output(root)
        logger.debug("Formatted XML document, length: %d characters", len(xml_str))

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        logger.info("Successfully wrote HNPX document to: %s", file_path)

        return {
            "success": True,
            "file_path": file_path,
            "book_id": book_id,
            "message": f"Created new HNPX document at {file_path}",
        }
    except Exception as e:
        logger.error("Failed to create HNPX document at %s: %s", file_path, str(e))
        raise OSError(f"Cannot create file at {file_path}: {str(e)}")
