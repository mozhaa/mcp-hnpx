"""
Tests for HNPX error handling.
"""

from src.mcp_hnpx.errors import (
    HNPXError,
    FileNotFoundError,
    InvalidXMLError,
    NotHNPXError,
    FileExistsError,
    NodeNotFoundError,
    InvalidParentError,
    DuplicateIDError,
    MissingAttributeError,
    InvalidAttributeError,
    InvalidHierarchyError,
    EmptySummaryError,
    MissingCharError,
    ValidationFailedError,
    ReadOnlyError,
    ImmutableRootError,
)


class TestHNPXError:
    def test_base_error_inheritance(self):
        """Test that HNPXError inherits from fastmcp.ToolError."""
        error = HNPXError("Test message")
        assert str(error) == "Test message"

    def test_base_error_message(self):
        """Test base error message handling."""
        message = "Base HNPX error occurred"
        error = HNPXError(message)
        assert str(error) == message


class TestFileNotFoundError:
    def test_file_not_found_error_message(self):
        """Test FileNotFoundError message format."""
        file_path = "/path/to/nonexistent/file.xml"
        error = FileNotFoundError(file_path)
        expected = f"File not found at '{file_path}'"
        assert str(error) == expected

    def test_file_not_found_with_empty_path(self):
        """Test FileNotFoundError with empty path."""
        error = FileNotFoundError("")
        assert str(error) == "File not found at ''"


class TestInvalidXMLError:
    def test_invalid_xml_error_message(self):
        """Test InvalidXMLError message format."""
        reason = "Mismatched tags at line 10"
        error = InvalidXMLError(reason)
        expected = f"The file contains malformed XML\nReason: {reason}"
        assert str(error) == expected

    def test_invalid_xml_with_empty_reason(self):
        """Test InvalidXMLError with empty reason."""
        error = InvalidXMLError("")
        assert str(error) == "The file contains malformed XML\nReason: "


class TestNotHNPXError:
    def test_not_hnpx_error_message(self):
        """Test NotHNPXError message format."""
        error = NotHNPXError()
        expected = (
            "The file is not a valid HNPX document\n"
            "Reason: HNPX documents must have a root <book> element with proper structure"
        )
        assert str(error) == expected


class TestFileExistsError:
    def test_file_exists_error_message(self):
        """Test FileExistsError message format."""
        file_path = "/path/to/existing/file.xml"
        error = FileExistsError(file_path)
        expected = f"File already exists at '{file_path}'"
        assert str(error) == expected


class TestNodeNotFoundError:
    def test_node_not_found_error_message(self):
        """Test NodeNotFoundError message format."""
        node_id = "nonexistent123"
        error = NodeNotFoundError(node_id)
        expected = f"Node with ID '{node_id}' was not found"
        assert str(error) == expected


class TestInvalidParentError:
    def test_invalid_parent_error_message(self):
        """Test InvalidParentError message format."""
        parent_type = "chapter"
        child_type = "book"
        error = InvalidParentError(parent_type, child_type)

        message = str(error)
        assert f"Cannot add {child_type} element to {parent_type} element" in message
        assert "book→chapter→sequence→beat→paragraph" in message
        assert f"{parent_type} can only contain: chapters" in message

    def test_invalid_parent_for_different_types(self):
        """Test InvalidParentError for different parent-child combinations."""
        test_cases = [
            ("book", "sequence"),
            ("chapter", "beat"),
            ("sequence", "paragraph"),
            ("beat", "chapter"),
        ]

        for parent_type, child_type in test_cases:
            error = InvalidParentError(parent_type, child_type)
            message = str(error)
            assert (
                f"Cannot add {child_type} element to {parent_type} element" in message
            )


class TestDuplicateIDError:
    def test_duplicate_id_error_message(self):
        """Test DuplicateIDError message format."""
        node_id = "duplicate123"
        error = DuplicateIDError(node_id)
        expected = f"Node ID '{node_id}' already exists in the document"
        assert str(error) == expected


class TestMissingAttributeError:
    def test_missing_attribute_error_message(self):
        """Test MissingAttributeError message format."""
        attribute = "title"
        error = MissingAttributeError(attribute)
        expected = f"Required attribute '{attribute}' is missing"
        assert str(error) == expected

    def test_missing_attribute_with_different_attributes(self):
        """Test MissingAttributeError for different attributes."""
        attributes = ["id", "title", "loc", "summary", "text"]

        for attr in attributes:
            error = MissingAttributeError(attr)
            assert str(error) == f"Required attribute '{attr}' is missing"


class TestInvalidAttributeError:
    def test_invalid_attribute_error_message(self):
        """Test InvalidAttributeError message format."""
        attribute = "mode"
        value = "invalid_mode"
        error = InvalidAttributeError(attribute, value)
        expected = f"Invalid value '{value}' for attribute '{attribute}'"
        assert str(error) == expected

    def test_invalid_attribute_with_different_values(self):
        """Test InvalidAttributeError for different attribute values."""
        test_cases = [
            ("mode", "invalid"),
            ("id", "too_long"),
            ("pov", "123invalid"),
        ]

        for attr, value in test_cases:
            error = InvalidAttributeError(attr, value)
            assert str(error) == f"Invalid value '{value}' for attribute '{attr}'"


class TestInvalidHierarchyError:
    def test_invalid_hierarchy_error_message(self):
        """Test InvalidHierarchyError message format."""
        error = InvalidHierarchyError()
        expected = (
            "Operation would break the HNPX hierarchy\n"
            "Reason: HNPX requires strict book→chapter→sequence→beat→paragraph nesting"
        )
        assert str(error) == expected


class TestEmptySummaryError:
    def test_empty_summary_error_message(self):
        """Test EmptySummaryError message format."""
        error = EmptySummaryError()
        expected = (
            "Summary element is missing or empty\n"
            "Reason: All HNPX container elements must have a non-empty <summary> child"
        )
        assert str(error) == expected


class TestMissingCharError:
    def test_missing_char_error_message(self):
        """Test MissingCharError message format."""
        error = MissingCharError()
        expected = (
            "Dialogue paragraph is missing the 'char' attribute\n"
            "Reason: Dialogue paragraphs must specify which character is speaking"
        )
        assert str(error) == expected


class TestValidationFailedError:
    def test_validation_failed_error_message(self):
        """Test ValidationFailedError message format."""
        reason = "Chapter title cannot be empty"
        error = ValidationFailedError(reason)
        expected = f"Operation would create invalid HNPX\nReason: {reason}"
        assert str(error) == expected

    def test_validation_failed_with_empty_reason(self):
        """Test ValidationFailedError with empty reason."""
        error = ValidationFailedError("")
        assert str(error) == "Operation would create invalid HNPX\nReason: "


class TestReadOnlyError:
    def test_read_only_error_message(self):
        """Test ReadOnlyError message format."""
        attribute = "id"
        error = ReadOnlyError(attribute)
        expected = f"Cannot modify read-only attribute '{attribute}'"
        assert str(error) == expected

    def test_read_only_with_different_attributes(self):
        """Test ReadOnlyError for different attributes."""
        attributes = ["id", "created_at", "modified_at"]

        for attr in attributes:
            error = ReadOnlyError(attr)
            assert str(error) == f"Cannot modify read-only attribute '{attr}'"


class TestImmutableRootError:
    def test_immutable_root_error_message(self):
        """Test ImmutableRootError message format."""
        error = ImmutableRootError()
        expected = (
            "Cannot remove the root book element\n"
            "Reason: The book element is the document root and cannot be deleted"
        )
        assert str(error) == expected


class TestErrorInheritance:
    def test_all_errors_inherit_from_base(self):
        """Test that all error classes inherit from HNPXError."""
        error_classes = [
            FileNotFoundError,
            InvalidXMLError,
            NotHNPXError,
            FileExistsError,
            NodeNotFoundError,
            InvalidParentError,
            DuplicateIDError,
            MissingAttributeError,
            InvalidAttributeError,
            InvalidHierarchyError,
            EmptySummaryError,
            MissingCharError,
            ValidationFailedError,
            ReadOnlyError,
            ImmutableRootError,
        ]

        for error_class in error_classes:
            error = error_class("test")
            assert isinstance(error, HNPXError)
            assert isinstance(error, Exception)


class TestErrorWithSpecialCharacters:
    def test_error_with_special_characters(self):
        """Test error handling with special characters in messages."""
        special_chars = "Test with special chars: áéíóú ñ 中文 🚀"

        error_classes = [
            HNPXError,
            FileNotFoundError,
            NodeNotFoundError,
            MissingAttributeError,
            InvalidAttributeError,
            ValidationFailedError,
        ]

        for error_class in error_classes:
            if error_class in [FileNotFoundError, NodeNotFoundError]:
                error = error_class(special_chars)
            elif error_class in [MissingAttributeError]:
                error = error_class(special_chars)
            elif error_class in [InvalidAttributeError]:
                error = error_class("attr", special_chars)
            elif error_class in [ValidationFailedError]:
                error = error_class(special_chars)
            else:
                error = error_class(special_chars)

            assert special_chars in str(error)


class TestErrorWithNoneValues:
    def test_error_with_none_values(self):
        """Test error handling with None values."""
        # These should handle None gracefully
        error = MissingAttributeError(None)
        assert "None" in str(error)

        error = InvalidAttributeError(None, None)
        assert "None" in str(error)

        error = ValidationFailedError(None)
        assert "None" in str(error)
