import os
import tempfile

from lxml import etree

import mcp_hnpx


def test_create_document():
    """Test creating a new HNPX document"""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = mcp_hnpx.server.create_document.fn(tmp_path)
        assert "Created book with id" in result
        assert os.path.exists(tmp_path)

        # Verify the document structure
        tree = mcp_hnpx.server.parse_document(tmp_path)
        root = tree.getroot()
        assert root.tag == "book"
        assert "id" in root.attrib
        assert len(root) == 1  # Should have one summary element
        assert root[0].tag == "summary"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_generate_unique_id():
    """Test ID generation"""
    existing_ids = {"abc123", "def456"}
    new_id = mcp_hnpx.server.generate_unique_id(existing_ids)
    assert len(new_id) == 6
    assert new_id not in existing_ids
    assert new_id.isalnum()
    assert new_id.islower()


def test_find_node():
    """Test finding nodes by ID"""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Create a document
        mcp_hnpx.server.create_document.fn(tmp_path)
        tree = mcp_hnpx.server.parse_document(tmp_path)
        book_id = tree.getroot().get("id")

        # Test finding the book
        node = mcp_hnpx.server.find_node(tree, book_id)
        assert node is not None
        assert node.tag == "book"

        # Test finding non-existent node
        node = mcp_hnpx.server.find_node(tree, "nonexistent")
        assert node is None
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_render_paragraph():
    """Test paragraph rendering with different modes"""
    # Test narration (default)
    paragraph = etree.Element("paragraph")
    paragraph.text = "This is narration."
    result = mcp_hnpx.server.render_paragraph(paragraph)
    assert result == "This is narration."

    # Test dialogue
    paragraph = etree.Element("paragraph", mode="dialogue", char="john")
    paragraph.text = "Hello there."
    result = mcp_hnpx.server.render_paragraph(paragraph)
    assert result == 'john: "Hello there."'

    # Test internal
    paragraph = etree.Element("paragraph", mode="internal")
    paragraph.text = "This is a thought."
    result = mcp_hnpx.server.render_paragraph(paragraph)
    assert result == "*This is a thought.*"


def test_get_all_ids():
    """Test getting all IDs from a document"""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Create a document
        mcp_hnpx.server.create_document.fn(tmp_path)
        tree = mcp_hnpx.server.parse_document(tmp_path)

        # Get all IDs
        ids = mcp_hnpx.server.get_all_ids(tree)
        assert len(ids) == 1  # Should have just the book ID

        # Verify it's the book ID
        book_id = tree.getroot().get("id")
        assert book_id in ids
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
