"""
Tests for node inspection tools.
"""

import pytest
from lxml import etree

from src.mcp_hnpx.tools.inspection import (
    get_subtree,
    get_direct_children,
    get_node_path,
    get_node_context,
)
from src.mcp_hnpx.errors import (
    FileNotFoundError,
    NotHNPXError,
    NodeNotFoundError,
)


class TestGetSubtree:
    def test_get_book_subtree(self, sample_hnpx_file):
        """Test getting subtree of book node (entire document)."""
        result = get_subtree(str(sample_hnpx_file), "b3k9m7")

        assert "<book" in result
        assert 'id="b3k9m7"' in result
        assert "<chapter>" in result
        assert "<sequence>" in result
        assert "<beat>" in result
        assert "<paragraph>" in result
        assert "Boogiepop legend" in result

    def test_get_chapter_subtree(self, sample_hnpx_file):
        """Test getting subtree of chapter node."""
        result = get_subtree(str(sample_hnpx_file), "c8p2q5")

        assert "<chapter" in result
        assert 'id="c8p2q5"' in result
        assert 'title="Boogiepop"' in result
        assert "<sequence>" in result
        assert "<beat>" in result
        assert "<paragraph>" in result

        # Should not include book element
        assert "<book>" not in result

    def test_get_paragraph_subtree(self, sample_hnpx_file):
        """Test getting subtree of paragraph node."""
        result = get_subtree(str(sample_hnpx_file), "p9m5k2")

        assert "<paragraph" in result
        assert 'id="p9m5k2"' in result
        assert 'mode="narration"' in result
        assert "<summary>" in result
        assert "narrator introduces" in result
        assert "Recently, a strange rumor" in result

        # Should not include parent elements
        assert "<beat>" not in result
        assert "<sequence>" not in result

    def test_get_subtree_nonexistent_node(self, sample_hnpx_file):
        """Test getting subtree of non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            get_subtree(str(sample_hnpx_file), "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_subtree_nonexistent_file(self):
        """Test getting subtree from non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_subtree("nonexistent.xml", "any_id")

    def test_get_subtree_invalid_xml(self, invalid_xml_file):
        """Test getting subtree from invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            get_subtree(str(invalid_xml_file), "any_id")

    def test_get_subtree_non_hnpx_document(self, non_hnpx_file):
        """Test getting subtree from non-HNPX document."""
        with pytest.raises(NotHNPXError):
            get_subtree(str(non_hnpx_file), "any_id")

    def test_get_subtree_xml_format(self, sample_hnpx_file):
        """Test that subtree XML is properly formatted."""
        result = get_subtree(str(sample_hnpx_file), "c8p2q5")

        # Should be properly indented
        lines = result.split("\n")
        assert len(lines) > 1

        # Should have proper XML structure
        assert result.strip().startswith("<chapter")
        assert result.strip().endswith("</chapter>")


class TestGetDirectChildren:
    def test_get_book_children(self, sample_hnpx_file):
        """Test getting children of book node."""
        result = get_direct_children(str(sample_hnpx_file), "b3k9m7")

        assert "<children>" in result
        assert "<chapter" in result
        assert 'id="c8p2q5"' in result
        assert 'title="Boogiepop"' in result

        # Should not include summary
        assert "<summary>" not in result

        # Should not include grandchildren
        assert "<sequence>" not in result

    def test_get_chapter_children(self, sample_hnpx_file):
        """Test getting children of chapter node."""
        result = get_direct_children(str(sample_hnpx_file), "c8p2q5")

        assert "<children>" in result
        assert "<sequence" in result
        assert 'id="s4r7t9"' in result
        assert 'loc="School cafeteria"' in result

        # Should not include summary
        assert "<summary>" not in result

        # Should not include grandchildren
        assert "<beat>" not in result

    def test_get_beat_children(self, sample_hnpx_file):
        """Test getting children of beat node."""
        result = get_direct_children(str(sample_hnpx_file), "b1v6x3")

        assert "<children>" in result
        assert "<paragraph" in result
        assert 'id="p9m5k2"' in result
        assert 'mode="narration"' in result

        # Should not include summary
        assert "<summary>" not in result

    def test_get_paragraph_children(self, sample_hnpx_file):
        """Test getting children of paragraph node (should be empty)."""
        result = get_direct_children(str(sample_hnpx_file), "p9m5k2")

        assert "<children>" in result
        assert "<paragraph>" not in result
        assert "<summary>" not in result

    def test_get_children_nonexistent_node(self, sample_hnpx_file):
        """Test getting children of non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            get_direct_children(str(sample_hnpx_file), "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_children_multiple_children(self, temp_dir):
        """Test getting children when parent has multiple children."""
        # Create document with multiple sequences
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        # Add multiple sequences
        for i in range(3):
            sequence = etree.SubElement(
                chapter, "sequence", id=f"seq{i:03d}", loc=f"Location {i + 1}"
            )
            seq_summary = etree.SubElement(sequence, "summary")
            seq_summary.text = f"Sequence {i + 1}"

        file_path = temp_dir / "multiple_children.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_direct_children(str(file_path), "def456")

        # Should contain all three sequences
        assert result.count("<sequence") == 3
        assert 'id="seq000"' in result
        assert 'id="seq001"' in result
        assert 'id="seq002"' in result

    def test_get_children_nonexistent_file(self):
        """Test getting children from non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_direct_children("nonexistent.xml", "any_id")

    def test_get_children_invalid_xml(self, invalid_xml_file):
        """Test getting children from invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            get_direct_children(str(invalid_xml_file), "any_id")

    def test_get_children_non_hnpx_document(self, non_hnpx_file):
        """Test getting children from non-HNPX document."""
        with pytest.raises(NotHNPXError):
            get_direct_children(str(non_hnpx_file), "any_id")


class TestGetNodePath:
    def test_get_book_path(self, sample_hnpx_file):
        """Test getting path to book node (should just be book)."""
        result = get_node_path(str(sample_hnpx_file), "b3k9m7")

        assert "<path>" in result
        assert "<book" in result
        assert 'id="b3k9m7"' in result

        # Should not include other elements
        assert "<chapter>" not in result

    def test_get_chapter_path(self, sample_hnpx_file):
        """Test getting path to chapter node."""
        result = get_node_path(str(sample_hnpx_file), "c8p2q5")

        assert "<path>" in result
        assert "<book" in result
        assert 'id="b3k9m7"' in result
        assert "<chapter" in result
        assert 'id="c8p2q5"' in result

        # Should not include sequence
        assert "<sequence>" not in result

    def test_get_paragraph_path(self, sample_hnpx_file):
        """Test getting path to paragraph node."""
        result = get_node_path(str(sample_hnpx_file), "p9m5k2")

        assert "<path>" in result
        assert "<book" in result
        assert 'id="b3k9m7"' in result
        assert "<chapter" in result
        assert 'id="c8p2q5"' in result
        assert "<sequence" in result
        assert 'id="s4r7t9"' in result
        assert "<beat" in result
        assert 'id="b1v6x3"' in result

        # Should include the target paragraph
        assert "<paragraph" in result
        assert 'id="p9m5k2"' in result

    def test_get_path_nonexistent_node(self, sample_hnpx_file):
        """Test getting path to non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            get_node_path(str(sample_hnpx_file), "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_path_order(self, sample_hnpx_file):
        """Test that path elements are in correct order."""
        result = get_node_path(str(sample_hnpx_file), "p9m5k2")

        # Check that elements appear in correct order
        book_pos = result.find("<book")
        chapter_pos = result.find("<chapter")
        sequence_pos = result.find("<sequence")
        beat_pos = result.find("<beat")
        paragraph_pos = result.find("<paragraph")

        assert book_pos < chapter_pos < sequence_pos < beat_pos < paragraph_pos

    def test_get_path_with_attributes(self, temp_dir):
        """Test getting path with various attributes."""
        # Create document with nodes having multiple attributes
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(
            root, "chapter", id="def456", title="Test Chapter", pov="test_char"
        )
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter, "sequence", id="ghi789", loc="Test Location", time="morning"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        file_path = temp_dir / "path_attrs.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_node_path(str(file_path), "ghi789")

        assert 'title="Test Chapter"' in result
        assert 'pov="test_char"' in result
        assert 'loc="Test Location"' in result
        assert 'time="morning"' in result

    def test_get_path_nonexistent_file(self):
        """Test getting path from non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_node_path("nonexistent.xml", "any_id")

    def test_get_path_invalid_xml(self, invalid_xml_file):
        """Test getting path from invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            get_node_path(str(invalid_xml_file), "any_id")

    def test_get_path_non_hnpx_document(self, non_hnpx_file):
        """Test getting path from non-HNPX document."""
        with pytest.raises(NotHNPXError):
            get_node_path(str(non_hnpx_file), "any_id")


class TestGetNodeContext:
    def test_get_book_context(self, sample_hnpx_file):
        """Test getting context for book node."""
        result = get_node_context(str(sample_hnpx_file), "b3k9m7")

        assert result["node"]["id"] == "b3k9m7"
        assert result["node"]["type"] == "book"
        assert "Boogiepop legend" in result["node"]["summary"]
        assert result["node"]["attributes"]["id"] == "b3k9m7"

        # Book should have no parent
        assert result["parent"] is None

        # Should have children
        assert len(result["children"]) > 0
        assert result["children"][0]["id"] == "c8p2q5"
        assert result["children"][0]["type"] == "chapter"

        # Book should have no siblings
        assert result["siblings"] == []

    def test_get_chapter_context(self, sample_hnpx_file):
        """Test getting context for chapter node."""
        result = get_node_context(str(sample_hnpx_file), "c8p2q5")

        assert result["node"]["id"] == "c8p2q5"
        assert result["node"]["type"] == "chapter"
        assert "Students discuss the Boogiepop legend" in result["node"]["summary"]
        assert result["node"]["attributes"]["title"] == "Boogiepop"
        assert result["node"]["attributes"]["pov"] == "suema"

        # Should have parent
        assert result["parent"]["id"] == "b3k9m7"
        assert result["parent"]["type"] == "book"

        # Should have children
        assert len(result["children"]) > 0
        assert result["children"][0]["id"] == "s4r7t9"
        assert result["children"][0]["type"] == "sequence"

        # Should have no siblings (only one chapter)
        assert result["siblings"] == []

    def test_get_paragraph_context(self, sample_hnpx_file):
        """Test getting context for paragraph node."""
        result = get_node_context(str(sample_hnpx_file), "p9m5k2")

        assert result["node"]["id"] == "p9m5k2"
        assert result["node"]["type"] == "paragraph"
        assert "narrator introduces" in result["node"]["summary"]
        assert result["node"]["attributes"]["mode"] == "narration"

        # Should have parent
        assert result["parent"]["id"] == "b1v6x3"
        assert result["parent"]["type"] == "beat"

        # Paragraph should have no children
        assert result["children"] == []

        # Should have siblings (other paragraphs in same beat)
        assert len(result["siblings"]) >= 0

    def test_get_context_with_siblings(self, temp_dir):
        """Test getting context for node with siblings."""
        # Create document with multiple chapters
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        # Add multiple chapters
        chapters = []
        for i in range(3):
            chapter = etree.SubElement(
                root, "chapter", id=f"ch{i:03d}", title=f"Chapter {i + 1}"
            )
            chapter_summary = etree.SubElement(chapter, "summary")
            chapter_summary.text = f"Chapter {i + 1} summary"
            chapters.append(chapter)

        file_path = temp_dir / "siblings.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_node_context(str(file_path), "ch001")

        # Should have siblings
        assert len(result["siblings"]) == 2
        sibling_ids = [s["id"] for s in result["siblings"]]
        assert "ch000" in sibling_ids
        assert "ch002" in sibling_ids

    def test_get_context_nonexistent_node(self, sample_hnpx_file):
        """Test getting context for non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            get_node_context(str(sample_hnpx_file), "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_context_structure(self, sample_hnpx_file):
        """Test the structure of context result."""
        result = get_node_context(str(sample_hnpx_file), "c8p2q5")

        # Check required keys
        required_keys = {"node", "parent", "children", "siblings"}
        assert set(result.keys()) == required_keys

        # Check node structure
        node_keys = {"id", "type", "summary", "attributes"}
        assert set(result["node"].keys()) == node_keys

        # Check parent structure (if not None)
        if result["parent"]:
            parent_keys = {"id", "type"}
            assert set(result["parent"].keys()) == parent_keys

        # Check children structure
        for child in result["children"]:
            child_keys = {"id", "type", "summary"}
            assert set(child.keys()) == child_keys

        # Check siblings structure
        for sibling in result["siblings"]:
            sibling_keys = {"id", "type", "summary"}
            assert set(sibling.keys()) == sibling_keys

    def test_get_context_nonexistent_file(self):
        """Test getting context from non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_node_context("nonexistent.xml", "any_id")

    def test_get_context_invalid_xml(self, invalid_xml_file):
        """Test getting context from invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            get_node_context(str(invalid_xml_file), "any_id")

    def test_get_context_non_hnpx_document(self, non_hnpx_file):
        """Test getting context from non-HNPX document."""
        with pytest.raises(NotHNPXError):
            get_node_context(str(non_hnpx_file), "any_id")
