"""
Error definitions following mcp-tools.md specification.
All exceptions inherit from fastmcp.ToolError for proper MCP integration.
"""

from fastmcp import ToolError


class HNPXError(ToolError):
    """Base exception for all HNPX-related errors."""

    def __init__(self, message: str):
        super().__init__(message)


class FileNotFoundError(HNPXError):
    def __init__(self, file_path: str):
        super().__init__(f"File not found at '{file_path}'")


class InvalidXMLError(HNPXError):
    def __init__(self, reason: str):
        super().__init__(f"The file contains malformed XML\nReason: {reason}")


class NotHNPXError(HNPXError):
    def __init__(self):
        super().__init__(
            "The file is not a valid HNPX document\n"
            "Reason: HNPX documents must have a root <book> element with proper structure"
        )


class FileExistsError(HNPXError):
    def __init__(self, file_path: str):
        super().__init__(f"File already exists at '{file_path}'")


class NodeNotFoundError(HNPXError):
    def __init__(self, node_id: str):
        super().__init__(f"Node with ID '{node_id}' was not found")


class InvalidParentError(HNPXError):
    def __init__(self, parent_type: str, child_type: str):
        valid_hierarchy = "book→chapter→sequence→beat→paragraph"
        valid_children = {
            "book": "chapters",
            "chapter": "sequences",
            "sequence": "beats",
            "beat": "paragraphs",
            "paragraph": "no children",
        }
        children_info = valid_children.get(parent_type, "unknown element type")
        super().__init__(
            f"Cannot add {child_type} element to {parent_type} element\n"
            f"Reason: This violates the HNPX hierarchy: {valid_hierarchy}. "
            f"{parent_type} can only contain: {children_info}"
        )


class DuplicateIDError(HNPXError):
    def __init__(self, node_id: str):
        super().__init__(f"Node ID '{node_id}' already exists in the document")


class MissingAttributeError(HNPXError):
    def __init__(self, attribute: str):
        super().__init__(f"Required attribute '{attribute}' is missing")


class InvalidAttributeError(HNPXError):
    def __init__(self, attribute: str, value: str):
        super().__init__(f"Invalid value '{value}' for attribute '{attribute}'")


class InvalidHierarchyError(HNPXError):
    def __init__(self):
        super().__init__(
            "Operation would break the HNPX hierarchy\n"
            "Reason: HNPX requires strict book→chapter→sequence→beat→paragraph nesting"
        )


class EmptySummaryError(HNPXError):
    def __init__(self):
        super().__init__(
            "Summary element is missing or empty\n"
            "Reason: All HNPX container elements must have a non-empty <summary> child"
        )


class MissingCharError(HNPXError):
    def __init__(self):
        super().__init__(
            "Dialogue paragraph is missing the 'char' attribute\n"
            "Reason: Dialogue paragraphs must specify which character is speaking"
        )


class ValidationFailedError(HNPXError):
    def __init__(self, reason: str):
        super().__init__(f"Operation would create invalid HNPX\nReason: {reason}")


class ReadOnlyError(HNPXError):
    def __init__(self, attribute: str):
        super().__init__(f"Cannot modify read-only attribute '{attribute}'")


class ImmutableRootError(HNPXError):
    def __init__(self):
        super().__init__(
            "Cannot remove the root book element\n"
            "Reason: The book element is the document root and cannot be deleted"
        )
