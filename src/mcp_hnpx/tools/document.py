"""
Document management tools for HNPX MCP server.
"""

import os
from ..hnpx_utils import create_minimal_hnpx_document, format_xml_for_output
from ..errors import FileExistsError


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
    if os.path.exists(file_path):
        raise FileExistsError(file_path)

    try:
        root = create_minimal_hnpx_document()

        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += format_xml_for_output(root)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        return {
            "success": True,
            "file_path": file_path,
            "book_id": root.get("id"),
            "message": f"Created new HNPX document at {file_path}",
        }
    except Exception as e:
        raise OSError(f"Cannot create file at {file_path}: {str(e)}")
