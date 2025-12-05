"""
Error definitions following mcp-tools.md specification.
"""

from typing import Any


class HNPXError(Exception):
    """Base exception for all HNPX-related errors."""

    def __init__(self, code: str, message: str, details: dict[str, Any] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code}: {message}")


class FileNotFoundError(HNPXError):
    def __init__(self, file_path: str):
        super().__init__(
            "FILE_NOT_FOUND", f"File not found: {file_path}", {"file_path": file_path}
        )


class InvalidXMLError(HNPXError):
    def __init__(self, reason: str):
        super().__init__("INVALID_XML", f"Invalid XML: {reason}", {"reason": reason})


class NotHNPXError(HNPXError):
    def __init__(self):
        super().__init__("NOT_HNPX", "File is not valid HNPX format")


class FileExistsError(HNPXError):
    def __init__(self, file_path: str):
        super().__init__(
            "FILE_EXISTS",
            f"File already exists at {file_path}",
            {"file_path": file_path},
        )


class NodeNotFoundError(HNPXError):
    def __init__(self, node_id: str):
        super().__init__(
            "NODE_NOT_FOUND", f"Node with id {node_id} not found", {"node_id": node_id}
        )


class InvalidParentError(HNPXError):
    def __init__(self, parent_type: str, child_type: str):
        super().__init__(
            "INVALID_PARENT",
            f"Cannot add {child_type} to {parent_type}",
            {"parent_type": parent_type, "child_type": child_type},
        )


class DuplicateIDError(HNPXError):
    def __init__(self, node_id: str):
        super().__init__(
            "DUPLICATE_ID", f"ID already exists: {node_id}", {"node_id": node_id}
        )


class MissingAttributeError(HNPXError):
    def __init__(self, attribute: str):
        super().__init__(
            "MISSING_ATTRIBUTE",
            f"Required attribute missing: {attribute}",
            {"attribute": attribute},
        )


class InvalidAttributeError(HNPXError):
    def __init__(self, attribute: str, value: str):
        super().__init__(
            "INVALID_ATTRIBUTE",
            f"Invalid value for {attribute}: {value}",
            {"attribute": attribute, "value": value},
        )


class InvalidHierarchyError(HNPXError):
    def __init__(self):
        super().__init__(
            "INVALID_HIERARCHY",
            "Attempt to break book→chapter→sequence→beat→paragraph chain",
        )


class EmptySummaryError(HNPXError):
    def __init__(self):
        super().__init__("EMPTY_SUMMARY", "Summary element missing or empty")


class MissingCharError(HNPXError):
    def __init__(self):
        super().__init__("MISSING_CHAR", "Dialogue paragraph missing char attribute")


class ValidationFailedError(HNPXError):
    def __init__(self, reason: str):
        super().__init__(
            "VALIDATION_FAILED", f"Validation failed: {reason}", {"reason": reason}
        )


class ReadOnlyError(HNPXError):
    def __init__(self, attribute: str):
        super().__init__(
            "READ_ONLY",
            f"Cannot modify read-only attribute: {attribute}",
            {"attribute": attribute},
        )


class ImmutableRootError(HNPXError):
    def __init__(self):
        super().__init__("IMMUTABLE_ROOT", "Cannot remove book element")


def create_error_response(
    code: str, message: str, details: dict[str, Any] = None
) -> dict:
    """Create standardized error response as per mcp-tools.md."""
    return {"error": True, "code": code, "message": message, "details": details or {}}
