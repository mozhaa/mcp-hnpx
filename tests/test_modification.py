"""
Tests for node modification tools.
"""

import pytest
from lxml import etree

from src.mcp_hnpx.tools.modification import (
    edit_node_attributes,
    remove_node,
    reorder_children,
)
from src.mcp_hnpx.errors import (
    FileNotFoundError,
    NotHNPXError,
    NodeNotFoundError,
    ReadOnlyError,
    ValidationFailedError,
    ImmutableRootError,
)


class TestEditNodeAttributes:
    def test_edit_chapter_attributes(self, sample_hnpx_file):
        """Test editing chapter attributes."""
        result = edit_node_attributes(
            str(sample_hnpx_file),
            "c8p2q5",
            {"title": "Updated Chapter Title", "pov": "new_character"},
        )

        assert result["success"] is True
        assert result["node_id"] == "c8p2q5"
        assert result["node_type"] == "chapter"
        assert result["updated_attributes"]["title"] == "Updated Chapter Title"
        assert result["updated_attributes"]["pov"] == "new_character"
        assert "Updated attributes" in result["message"]

        # Verify file was modified
        with open(sample_hnpx_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Updated Chapter Title" in content
            assert "new_character" in content

    def test_edit_sequence_attributes(self, sample_hnpx_file):
        """Test editing sequence attributes."""
        result = edit_node_attributes(
            str(sample_hnpx_file),
            "s4r7t9",
            {"loc": "Updated Location", "time": "evening", "pov": "updated_char"},
        )

        assert result["success"] is True
        assert result["node_type"] == "sequence"
        assert result["updated_attributes"]["loc"] == "Updated Location"
        assert result["updated_attributes"]["time"] == "evening"
        assert result["updated_attributes"]["pov"] == "updated_char"

    def test_edit_paragraph_attributes(self, sample_hnpx_file):
        """Test editing paragraph attributes."""
        result = edit_node_attributes(
            str(sample_hnpx_file), "p9m5k2", {"mode": "dialogue", "char": "speaker"}
        )

        assert result["success"] is True
        assert result["node_type"] == "paragraph"
        assert result["updated_attributes"]["mode"] == "dialogue"
        assert result["updated_attributes"]["char"] == "speaker"

    def test_edit_remove_attribute(self, sample_hnpx_file):
        """Test removing an attribute by setting it to None."""
        result = edit_node_attributes(
            str(sample_hnpx_file),
            "c8p2q5",
            {
                "pov": None  # Remove POV attribute
            },
        )

        assert result["success"] is True
        assert result["updated_attributes"]["pov"] is None

        # Verify attribute was removed
        with open(sample_hnpx_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert 'pov="suema"' not in content

    def test_edit_remove_attribute_with_empty_string(self, sample_hnpx_file):
        """Test removing an attribute by setting it to empty string."""
        result = edit_node_attributes(
            str(sample_hnpx_file),
            "c8p2q5",
            {
                "pov": ""  # Remove POV attribute with empty string
            },
        )

        assert result["success"] is True
        assert result["updated_attributes"]["pov"] is None

    def test_edit_nonexistent_node(self, sample_hnpx_file):
        """Test editing attributes of non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            edit_node_attributes(
                str(sample_hnpx_file), "nonexistent", {"title": "New Title"}
            )

        assert "nonexistent" in str(exc_info.value)

    def test_edit_readonly_id_attribute(self, sample_hnpx_file):
        """Test that ID attribute cannot be modified."""
        with pytest.raises(ReadOnlyError) as exc_info:
            edit_node_attributes(str(sample_hnpx_file), "c8p2q5", {"id": "new_id"})

        assert "id" in str(exc_info.value)

    def test_edit_chapter_empty_title(self, sample_hnpx_file):
        """Test editing chapter with empty title."""
        with pytest.raises(ValidationFailedError) as exc_info:
            edit_node_attributes(str(sample_hnpx_file), "c8p2q5", {"title": ""})

        assert "empty" in str(exc_info.value).lower()

    def test_edit_sequence_empty_location(self, sample_hnpx_file):
        """Test editing sequence with empty location."""
        with pytest.raises(ValidationFailedError) as exc_info:
            edit_node_attributes(str(sample_hnpx_file), "s4r7t9", {"loc": ""})

        assert "empty" in str(exc_info.value).lower()

    def test_edit_paragraph_dialogue_without_char(self, sample_hnpx_file):
        """Test editing paragraph to dialogue mode without character."""
        with pytest.raises(ValidationFailedError) as exc_info:
            edit_node_attributes(
                str(sample_hnpx_file), "p9m5k2", {"mode": "dialogue", "char": None}
            )

        assert "dialogue" in str(exc_info.value).lower()
        assert "char" in str(exc_info.value).lower()

    def test_edit_paragraph_invalid_mode(self, sample_hnpx_file):
        """Test editing paragraph with invalid mode."""
        with pytest.raises(Exception):  # Should raise InvalidAttributeError
            edit_node_attributes(
                str(sample_hnpx_file), "p9m5k2", {"mode": "invalid_mode"}
            )

    def test_edit_nonexistent_file(self):
        """Test editing attributes in non-existent file."""
        with pytest.raises(FileNotFoundError):
            edit_node_attributes("nonexistent.xml", "any_id", {"title": "New Title"})

    def test_edit_invalid_xml(self, invalid_xml_file):
        """Test editing attributes in invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            edit_node_attributes(
                str(invalid_xml_file), "any_id", {"title": "New Title"}
            )

    def test_edit_non_hnpx_document(self, non_hnpx_file):
        """Test editing attributes in non-HNPX document."""
        with pytest.raises(NotHNPXError):
            edit_node_attributes(str(non_hnpx_file), "any_id", {"title": "New Title"})


class TestRemoveNode:
    def test_remove_chapter(self, temp_dir):
        """Test removing a chapter node."""
        # Create document with multiple chapters
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter1 = etree.SubElement(root, "chapter", id="def456", title="Chapter 1")
        chapter1_summary = etree.SubElement(chapter1, "summary")
        chapter1_summary.text = "First chapter"

        chapter2 = etree.SubElement(root, "chapter", id="ghi789", title="Chapter 2")
        chapter2_summary = etree.SubElement(chapter2, "summary")
        chapter2_summary.text = "Second chapter"

        file_path = temp_dir / "remove_chapter.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = remove_node(str(file_path), "def456")

        assert result["success"] is True
        assert result["node_id"] == "def456"
        assert result["node_type"] == "chapter"
        assert result["summary"] == "First chapter"
        assert "Removed chapter" in result["message"]

        # Verify file was modified
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Chapter 1" not in content
            assert "Chapter 2" in content

    def test_remove_sequence(self, sample_hnpx_file):
        """Test removing a sequence node."""
        result = remove_node(str(sample_hnpx_file), "s4r7t9")

        assert result["success"] is True
        assert result["node_id"] == "s4r7t9"
        assert result["node_type"] == "sequence"
        assert "Lunch conversation" in result["summary"]
        assert "Removed sequence" in result["message"]

        # Verify file was modified
        with open(sample_hnpx_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "School cafeteria" not in content

    def test_remove_paragraph(self, sample_hnpx_file):
        """Test removing a paragraph node."""
        result = remove_node(str(sample_hnpx_file), "p9m5k2")

        assert result["success"] is True
        assert result["node_id"] == "p9m5k2"
        assert result["node_type"] == "paragraph"
        assert "narrator introduces" in result["summary"]
        assert "Removed paragraph" in result["message"]

    def test_remove_nonexistent_node(self, sample_hnpx_file):
        """Test removing non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            remove_node(str(sample_hnpx_file), "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_remove_book_node(self, sample_hnpx_file):
        """Test that book node cannot be removed."""
        with pytest.raises(ImmutableRootError) as exc_info:
            remove_node(str(sample_hnpx_file), "b3k9m7")

        assert "book" in str(exc_info.value).lower()
        assert "root" in str(exc_info.value).lower()

    def test_remove_node_with_children(self, sample_hnpx_file):
        """Test removing node that has children (should remove entire subtree)."""
        result = remove_node(
            str(sample_hnpx_file), "b1v6x3"
        )  # Remove beat with paragraphs

        assert result["success"] is True
        assert result["node_type"] == "beat"

        # Verify entire subtree was removed
        with open(sample_hnpx_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Introduction to the Boogiepop rumor" not in content
            assert "Recently, a strange rumor" not in content

    def test_remove_nonexistent_file(self):
        """Test removing node from non-existent file."""
        with pytest.raises(FileNotFoundError):
            remove_node("nonexistent.xml", "any_id")

    def test_remove_invalid_xml(self, invalid_xml_file):
        """Test removing node from invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            remove_node(str(invalid_xml_file), "any_id")

    def test_remove_non_hnpx_document(self, non_hnpx_file):
        """Test removing node from non-HNPX document."""
        with pytest.raises(NotHNPXError):
            remove_node(str(non_hnpx_file), "any_id")


class TestReorderChildren:
    def test_reorder_chapters(self, temp_dir):
        """Test reordering chapters."""
        # Create document with multiple chapters
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter1 = etree.SubElement(root, "chapter", id="ch001", title="Chapter 1")
        chapter1_summary = etree.SubElement(chapter1, "summary")
        chapter1_summary.text = "First chapter"

        chapter2 = etree.SubElement(root, "chapter", id="ch002", title="Chapter 2")
        chapter2_summary = etree.SubElement(chapter2, "summary")
        chapter2_summary.text = "Second chapter"

        chapter3 = etree.SubElement(root, "chapter", id="ch003", title="Chapter 3")
        chapter3_summary = etree.SubElement(chapter3, "summary")
        chapter3_summary.text = "Third chapter"

        file_path = temp_dir / "reorder_chapters.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Reorder chapters: 2, 3, 1
        result = reorder_children(
            str(file_path),
            "abc123",  # book ID
            ["ch002", "ch003", "ch001"],
        )

        assert result["success"] is True
        assert result["parent_id"] == "abc123"
        assert result["parent_type"] == "book"
        assert result["new_order"] == ["ch002", "ch003", "ch001"]
        assert "Reordered children" in result["message"]

        # Verify file was modified
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Chapter 2 should come first
            ch2_pos = content.find("Chapter 2")
            ch3_pos = content.find("Chapter 3")
            ch1_pos = content.find("Chapter 1")
            assert ch2_pos < ch3_pos < ch1_pos

    def test_reorder_sequences(self, sample_hnpx_file):
        """Test reordering sequences within a chapter."""
        # First, add another sequence to the sample document
        from src.mcp_hnpx.tools.creation import create_sequence

        create_sequence(
            str(sample_hnpx_file),
            "c8p2q5",  # chapter ID
            "Another Location",
            "Another sequence summary",
            "afternoon",
        )

        # Get the new sequence ID
        from src.mcp_hnpx.tools.navigation import get_direct_children

        children_xml = get_direct_children(str(sample_hnpx_file), "c8p2q5")
        import re

        sequence_ids = re.findall(r'id="([^"]+)"', children_xml)

        if len(sequence_ids) >= 2:
            # Reorder sequences
            result = reorder_children(
                str(sample_hnpx_file),
                "c8p2q5",
                [sequence_ids[1], sequence_ids[0]],  # Reverse order
            )

            assert result["success"] is True
            assert result["parent_type"] == "chapter"

    def test_reorder_paragraphs(self, temp_dir):
        """Test reordering paragraphs within a beat."""
        # Create document with multiple paragraphs
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
        para1 = etree.SubElement(beat, "paragraph", id="p001", mode="narration")
        para1_summary = etree.SubElement(para1, "summary")
        para1_summary.text = "First paragraph"
        para1.text = "First paragraph text."

        para2 = etree.SubElement(
            beat, "paragraph", id="p002", mode="dialogue", char="speaker"
        )
        para2_summary = etree.SubElement(para2, "summary")
        para2_summary.text = "Second paragraph"
        para2.text = "Second paragraph text."

        para3 = etree.SubElement(
            beat, "paragraph", id="p003", mode="internal", char="thinker"
        )
        para3_summary = etree.SubElement(para3, "summary")
        para3_summary.text = "Third paragraph"
        para3.text = "Third paragraph text."

        file_path = temp_dir / "reorder_paragraphs.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Reorder paragraphs: 3, 1, 2
        result = reorder_children(
            str(file_path),
            "jkl012",  # beat ID
            ["p003", "p001", "p002"],
        )

        assert result["success"] is True
        assert result["parent_type"] == "beat"
        assert result["new_order"] == ["p003", "p001", "p002"]

    def test_reorder_nonexistent_node(self, sample_hnpx_file):
        """Test reordering children of non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            reorder_children(str(sample_hnpx_file), "nonexistent", ["child1", "child2"])

        assert "nonexistent" in str(exc_info.value)

    def test_reorder_nonexistent_child(self, sample_hnpx_file):
        """Test reordering with non-existent child ID."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            reorder_children(
                str(sample_hnpx_file),
                "c8p2q5",  # chapter ID
                ["s4r7t9", "nonexistent_child"],
            )

        assert "nonexistent_child" in str(exc_info.value)

    def test_reorder_missing_children(self, sample_hnpx_file):
        """Test reordering without including all children."""
        with pytest.raises(ValidationFailedError) as exc_info:
            reorder_children(
                str(sample_hnpx_file),
                "c8p2q5",  # chapter ID
                ["s4r7t9"],  # Only one child, but there might be more
            )

        assert "all children" in str(exc_info.value).lower()

    def test_reorder_empty_children_list(self, temp_dir):
        """Test reordering with empty children list."""
        # Create document with no children
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        file_path = temp_dir / "empty_children.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        with pytest.raises(ValidationFailedError) as exc_info:
            reorder_children(
                str(file_path),
                "abc123",
                [],  # Empty list
            )

        assert "all children" in str(exc_info.value).lower()

    def test_reorder_nonexistent_file(self):
        """Test reordering children in non-existent file."""
        with pytest.raises(FileNotFoundError):
            reorder_children("nonexistent.xml", "any_id", ["child1", "child2"])

    def test_reorder_invalid_xml(self, invalid_xml_file):
        """Test reordering children in invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            reorder_children(str(invalid_xml_file), "any_id", ["child1", "child2"])

    def test_reorder_non_hnpx_document(self, non_hnpx_file):
        """Test reordering children in non-HNPX document."""
        with pytest.raises(NotHNPXError):
            reorder_children(str(non_hnpx_file), "any_id", ["child1", "child2"])


class TestModificationIntegration:
    def test_complex_modification_workflow(self, temp_dir):
        """Test a complex workflow with multiple modifications."""
        # Create document with structure
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter1 = etree.SubElement(root, "chapter", id="ch001", title="Chapter 1")
        chapter1_summary = etree.SubElement(chapter1, "summary")
        chapter1_summary.text = "First chapter"

        chapter2 = etree.SubElement(root, "chapter", id="ch002", title="Chapter 2")
        chapter2_summary = etree.SubElement(chapter2, "summary")
        chapter2_summary.text = "Second chapter"

        file_path = temp_dir / "complex_modification.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Step 1: Edit chapter 1 attributes
        edit_result1 = edit_node_attributes(
            str(file_path), "ch001", {"title": "Updated Chapter 1", "pov": "main_char"}
        )
        assert edit_result1["success"] is True

        # Step 2: Edit chapter 2 attributes
        edit_result2 = edit_node_attributes(
            str(file_path),
            "ch002",
            {"title": "Updated Chapter 2", "pov": "secondary_char"},
        )
        assert edit_result2["success"] is True

        # Step 3: Reorder chapters (2, 1)
        reorder_result = reorder_children(str(file_path), "abc123", ["ch002", "ch001"])
        assert reorder_result["success"] is True

        # Step 4: Remove chapter 1
        remove_result = remove_node(str(file_path), "ch001")
        assert remove_result["success"] is True

        # Verify final state
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Updated Chapter 2" in content
        assert "secondary_char" in content
        assert "Updated Chapter 1" not in content  # Should be removed
        assert "main_char" not in content  # Should be removed with chapter 1

        # Chapter 2 should come first (and only)
        ch2_pos = content.find("Updated Chapter 2")
        assert ch2_pos != -1
