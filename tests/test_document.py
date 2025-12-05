"""
Tests for document management tools.
"""

import os
from unittest.mock import patch

import pytest
from lxml import etree

from src.mcp_hnpx.tools.document import create_document
from src.mcp_hnpx.errors import FileExistsError


class TestCreateDocument:
    def test_create_new_document(self, temp_file):
        """Test creating a new HNPX document."""
        result = create_document(str(temp_file))

        assert result["success"] is True
        assert result["file_path"] == str(temp_file)
        assert "book_id" in result
        assert len(result["book_id"]) == 6
        assert "Created new HNPX document" in result["message"]

        # Check file was created
        assert temp_file.exists()

        # Check file content
        with open(temp_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert '<?xml version="1.0" encoding="utf-8"?>' in content
            assert "<book" in content
            assert result["book_id"] in content
            assert "<summary>New book</summary>" in content

    def test_create_document_with_custom_path(self, temp_dir):
        """Test creating document with custom path."""
        custom_path = temp_dir / "custom_document.hnpx"
        result = create_document(str(custom_path))

        assert result["success"] is True
        assert result["file_path"] == str(custom_path)
        assert custom_path.exists()

    def test_create_document_unique_ids(self, temp_dir):
        """Test that multiple documents have unique IDs."""
        ids = set()

        for i in range(5):
            file_path = temp_dir / f"document_{i}.hnpx"
            result = create_document(str(file_path))

            book_id = result["book_id"]
            assert book_id not in ids
            ids.add(book_id)
            assert len(book_id) == 6
            assert all(c.islower() or c.isdigit() for c in book_id)

    def test_create_document_file_exists(self, temp_file):
        """Test creating document when file already exists."""
        # Create the file first
        temp_file.write_text("existing content")

        with pytest.raises(FileExistsError) as exc_info:
            create_document(str(temp_file))

        assert str(temp_file) in str(exc_info.value)

    def test_create_document_invalid_path(self):
        """Test creating document with invalid path."""
        invalid_path = "/invalid/path/that/does/not/exist/document.hnpx"

        with pytest.raises(OSError) as exc_info:
            create_document(invalid_path)

        assert "Cannot create file" in str(exc_info.value)

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_create_document_permission_error(self, temp_file):
        """Test creating document with permission error."""
        with pytest.raises(OSError) as exc_info:
            create_document(str(temp_file))

        assert "Cannot create file" in str(exc_info.value)

    @patch("src.mcp_hnpx.tools.document.create_minimal_hnpx_document")
    def test_create_document_with_mock(self, mock_create, temp_file):
        """Test creating document with mocked minimal document."""
        # Mock the minimal document creation
        mock_root = etree.Element("book", id="mock123")
        mock_summary = etree.SubElement(mock_root, "summary")
        mock_summary.text = "Mock book"
        mock_create.return_value = mock_root

        result = create_document(str(temp_file))

        assert result["success"] is True
        assert result["book_id"] == "mock123"
        mock_create.assert_called_once()

    def test_create_document_xml_structure(self, temp_file):
        """Test that created document has correct XML structure."""
        result = create_document(str(temp_file))

        # Parse the created file
        with open(temp_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check XML declaration
        assert content.startswith('<?xml version="1.0" encoding="utf-8"?>')

        # Parse and verify structure
        root = etree.fromstring(content.split("\n", 1)[1])  # Skip XML declaration
        assert root.tag == "book"
        assert root.get("id") == result["book_id"]

        summary = root.find("summary")
        assert summary is not None
        assert summary.text == "New book"

    def test_create_document_file_encoding(self, temp_file):
        """Test that created file uses UTF-8 encoding."""
        create_document(str(temp_file))

        # Read file as bytes to check encoding
        with open(temp_file, "rb") as f:
            content = f.read()

        # Check for UTF-8 BOM or encoding declaration
        assert b'encoding="utf-8"' in content or content.startswith(b"\xef\xbb\xbf")

    def test_create_document_pretty_print(self, temp_file):
        """Test that created document is pretty-printed."""
        create_document(str(temp_file))

        with open(temp_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for indentation (pretty printing)
        lines = content.split("\n")
        assert len(lines) > 3  # Should have multiple lines

        # Check for proper indentation
        summary_line = None
        for line in lines:
            if "<summary>" in line:
                summary_line = line
                break

        assert summary_line is not None
        assert summary_line.startswith("  ")  # Should be indented

    def test_create_document_return_structure(self, temp_file):
        """Test the structure of the return value."""
        result = create_document(str(temp_file))

        required_keys = {"success", "file_path", "book_id", "message"}
        assert set(result.keys()) == required_keys

        assert isinstance(result["success"], bool)
        assert isinstance(result["file_path"], str)
        assert isinstance(result["book_id"], str)
        assert isinstance(result["message"], str)

        assert result["success"] is True
        assert result["file_path"] == str(temp_file)
        assert len(result["book_id"]) == 6
        assert "Created new HNPX document" in result["message"]

    def test_create_document_in_subdirectory(self, temp_dir):
        """Test creating document in a subdirectory."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        file_path = subdir / "document.hnpx"

        result = create_document(str(file_path))

        assert result["success"] is True
        assert file_path.exists()

    def test_create_document_with_relative_path(self, temp_dir):
        """Test creating document with relative path."""
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            result = create_document("relative_document.hnpx")

            assert result["success"] is True
            assert (temp_dir / "relative_document.hnpx").exists()
        finally:
            os.chdir(original_cwd)

    @patch("src.mcp_hnpx.tools.document.format_xml_for_output")
    def test_create_document_format_error(self, mock_format, temp_file):
        """Test handling of XML formatting errors."""
        mock_format.side_effect = Exception("Formatting error")

        with pytest.raises(OSError) as exc_info:
            create_document(str(temp_file))

        assert "Cannot create file" in str(exc_info.value)

    def test_create_document_id_validation(self, temp_file):
        """Test that generated book ID follows validation rules."""
        result = create_document(str(temp_file))
        book_id = result["book_id"]

        # Test ID format
        assert len(book_id) == 6
        assert all(c.islower() or c.isdigit() for c in book_id)

        # Test that ID would pass validation
        from src.mcp_hnpx.hnpx_utils import validate_id_format

        assert validate_id_format(book_id) is True
