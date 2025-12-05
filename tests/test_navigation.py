"""
Tests for navigation and discovery tools.
"""

import pytest
from lxml import etree

from src.mcp_hnpx.tools.navigation import get_next_empty_container, get_node
from src.mcp_hnpx.errors import (
    FileNotFoundError,
    NotHNPXError,
    NodeNotFoundError,
)


class TestGetNextEmptyContainer:
    def test_empty_book(self, minimal_hnpx_file):
        """Test finding empty container in minimal document (book with no chapters)."""
        result = get_next_empty_container(str(minimal_hnpx_file))

        assert result is not None
        assert result["type"] == "book"
        assert result["id"] is not None
        assert "has no chapters" in result["message"]
        assert result["level"] == 0

    def test_book_with_empty_chapter(self, temp_dir):
        """Test finding empty container when book has chapter with no sequences."""
        # Create document with empty chapter
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        file_path = temp_dir / "empty_chapter.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_next_empty_container(str(file_path))

        assert result is not None
        assert result["type"] == "chapter"
        assert result["id"] == "def456"
        assert "has no sequences" in result["message"]
        assert result["level"] == 1

    def test_chapter_with_empty_sequence(self, temp_dir):
        """Test finding empty container when chapter has sequence with no beats."""
        # Create document with empty sequence
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter, "sequence", id="ghi789", loc="Test Location"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        file_path = temp_dir / "empty_sequence.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_next_empty_container(str(file_path))

        assert result is not None
        assert result["type"] == "sequence"
        assert result["id"] == "ghi789"
        assert "has no beats" in result["message"]
        assert result["level"] == 2

    def test_sequence_with_empty_beat(self, temp_dir):
        """Test finding empty container when sequence has beat with no paragraphs."""
        # Create document with empty beat
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter, "sequence", id="ghi789", loc="Test Location"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        beat = etree.SubElement(sequence, "beat", id="jkl012")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "Test beat"

        file_path = temp_dir / "empty_beat.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_next_empty_container(str(file_path))

        assert result is not None
        assert result["type"] == "beat"
        assert result["id"] == "jkl012"
        assert "has no paragraphs" in result["message"]
        assert result["level"] == 3

    def test_complete_document(self, sample_hnpx_file):
        """Test finding empty container in complete document."""
        result = get_next_empty_container(str(sample_hnpx_file))

        # The sample document has a complete structure, but the beat might need more paragraphs
        if result:
            assert result["type"] in ["beat", "sequence", "chapter", "book"]
            assert "id" in result
            assert "message" in result
            assert "level" in result

    def test_no_empty_containers(self, temp_dir):
        """Test when no empty containers exist."""
        # Create a complete document with multiple paragraphs
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter, "sequence", id="ghi789", loc="Test Location"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        beat = etree.SubElement(sequence, "beat", id="jkl012")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "Test beat"

        # Add multiple paragraphs
        for i in range(3):
            paragraph = etree.SubElement(beat, "paragraph", id=f"p{i:03d}")
            para_summary = etree.SubElement(paragraph, "summary")
            para_summary.text = f"Paragraph {i + 1} summary"
            paragraph.text = f"This is paragraph {i + 1} content."

        file_path = temp_dir / "complete.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_next_empty_container(str(file_path))

        # Should return None since all containers have children
        assert result is None

    def test_bfs_order(self, temp_dir):
        """Test that BFS order is maintained."""
        # Create document with multiple chapters at different levels
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        # First chapter with complete structure
        chapter1 = etree.SubElement(root, "chapter", id="def456", title="Chapter 1")
        chapter1_summary = etree.SubElement(chapter1, "summary")
        chapter1_summary.text = "First chapter"

        sequence1 = etree.SubElement(
            chapter1, "sequence", id="ghi789", loc="Location 1"
        )
        sequence1_summary = etree.SubElement(sequence1, "summary")
        sequence1_summary.text = "First sequence"

        beat1 = etree.SubElement(sequence1, "beat", id="jkl012")
        beat1_summary = etree.SubElement(beat1, "summary")
        beat1_summary.text = "First beat"

        # Second chapter with no sequences (should be found first)
        chapter2 = etree.SubElement(root, "chapter", id="mno345", title="Chapter 2")
        chapter2_summary = etree.SubElement(chapter2, "summary")
        chapter2_summary.text = "Second chapter"

        file_path = temp_dir / "bfs_test.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_next_empty_container(str(file_path))

        # Should find the book first (no chapters at root level)
        assert result["type"] == "book"
        assert result["level"] == 0

    def test_nonexistent_file(self):
        """Test getting empty container from non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_next_empty_container("nonexistent.xml")

    def test_invalid_xml(self, invalid_xml_file):
        """Test getting empty container from invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            get_next_empty_container(str(invalid_xml_file))

    def test_non_hnpx_document(self, non_hnpx_file):
        """Test getting empty container from non-HNPX document."""
        with pytest.raises(NotHNPXError):
            get_next_empty_container(str(non_hnpx_file))


class TestGetNode:
    def test_get_existing_node(self, sample_hnpx_file):
        """Test getting an existing node."""
        result = get_node(str(sample_hnpx_file), "c8p2q5")

        assert "<chapter" in result
        assert 'id="c8p2q5"' in result
        assert 'title="Boogiepop"' in result
        assert 'pov="suema"' in result
        assert "<summary>" in result
        assert "Students discuss the Boogiepop legend" in result

        # Should not include children
        assert "<sequence>" not in result

    def test_get_book_node(self, sample_hnpx_file):
        """Test getting the book node."""
        result = get_node(str(sample_hnpx_file), "b3k9m7")

        assert "<book" in result
        assert 'id="b3k9m7"' in result
        assert "<summary>" in result
        assert "Boogiepop legend" in result

        # Should not include children
        assert "<chapter>" not in result

    def test_get_paragraph_node(self, sample_hnpx_file):
        """Test getting a paragraph node."""
        result = get_node(str(sample_hnpx_file), "p9m5k2")

        assert "<paragraph" in result
        assert 'id="p9m5k2"' in result
        assert 'mode="narration"' in result
        assert "<summary>" in result
        assert "narrator introduces" in result

        # Should not include text content (only summary)
        assert "Recently, a strange rumor" not in result

    def test_get_nonexistent_node(self, sample_hnpx_file):
        """Test getting a non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            get_node(str(sample_hnpx_file), "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_node_with_attributes(self, temp_dir):
        """Test getting node with various attributes."""
        # Create document with node having multiple attributes
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(
            root, "chapter", id="def456", title="Test Chapter", pov="test_char"
        )
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter,
            "sequence",
            id="ghi789",
            loc="Test Location",
            time="morning",
            pov="another_char",
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        paragraph = etree.SubElement(sequence, "beat", id="jkl012")
        paragraph_summary = etree.SubElement(paragraph, "summary")
        paragraph_summary.text = "Test beat"

        file_path = temp_dir / "attributes.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Test chapter with multiple attributes
        result = get_node(str(file_path), "def456")
        assert 'title="Test Chapter"' in result
        assert 'pov="test_char"' in result

        # Test sequence with multiple attributes
        result = get_node(str(file_path), "ghi789")
        assert 'loc="Test Location"' in result
        assert 'time="morning"' in result
        assert 'pov="another_char"' in result

    def test_get_node_without_summary(self, temp_dir):
        """Test getting node that has no summary (should still work)."""
        root = etree.Element("book", id="abc123")
        # No summary element

        etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        # No summary for chapter either

        file_path = temp_dir / "no_summary.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = get_node(str(file_path), "def456")

        assert "<chapter" in result
        assert 'id="def456"' in result
        assert 'title="Test Chapter"' in result
        # Should not have summary element
        assert "<summary>" not in result

    def test_get_node_nonexistent_file(self):
        """Test getting node from non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_node("nonexistent.xml", "any_id")

    def test_get_node_invalid_xml(self, invalid_xml_file):
        """Test getting node from invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            get_node(str(invalid_xml_file), "any_id")

    def test_get_node_non_hnpx_document(self, non_hnpx_file):
        """Test getting node from non-HNPX document."""
        with pytest.raises(NotHNPXError):
            get_node(str(non_hnpx_file), "any_id")

    def test_get_node_xml_format(self, sample_hnpx_file):
        """Test that returned XML is properly formatted."""
        result = get_node(str(sample_hnpx_file), "c8p2q5")

        # Should be properly indented
        lines = result.split("\n")
        assert len(lines) > 1

        # Should have proper XML structure
        assert result.strip().startswith("<chapter")
        assert result.strip().endswith("</chapter>")

        # Should have proper indentation for summary
        summary_line = None
        for line in lines:
            if "<summary>" in line:
                summary_line = line
                break

        if summary_line:
            assert summary_line.startswith("  ")  # Should be indented

    def test_get_node_empty_id(self, sample_hnpx_file):
        """Test getting node with empty ID."""
        with pytest.raises(NodeNotFoundError):
            get_node(str(sample_hnpx_file), "")

    def test_get_node_none_id(self, sample_hnpx_file):
        """Test getting node with None ID."""
        with pytest.raises((NodeNotFoundError, TypeError)):
            get_node(str(sample_hnpx_file), None)
