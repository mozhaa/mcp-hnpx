"""
XML schema validation for HNPX documents.
"""

import os

from lxml import etree

from .errors import HNPXError
from .hnpx_utils import parse_xml_file


def validate_hnpx(file_path: str, schema_file: str = None) -> None:
    """
    Validate HNPX document against XML schema.

    Args:
        file_path: Path to HNPX XML file
        schema_file: Path to XSD schema file (default: use bundled schema)

    Raises:
        HNPXError: If validation fails
    """
    try:
        xml_doc = parse_xml_file(file_path)

        if schema_file is None:
            schema_file = os.path.join(
                os.path.dirname(__file__), "..", "..", "docs", "HNPX.xml"
            )

        if not os.path.exists(schema_file):
            raise HNPXError(f"Schema file not found: {schema_file}")

        schema_doc = etree.parse(schema_file)
        schema = etree.XMLSchema(schema_doc)

        if not schema.validate(xml_doc):
            errors = [
                f"Line {error.line}: {error.message}" for error in schema.error_log
            ]
            raise HNPXError("\n".join(errors))

    except etree.XMLSchemaError as e:
        raise HNPXError(f"Schema validation error: {str(e)}")
    except Exception as e:
        if isinstance(e, HNPXError):
            raise
        raise HNPXError(f"Validation error: {str(e)}")
