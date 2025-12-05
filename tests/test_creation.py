"""
Tests for node creation tools.
"""

import pytest
from lxml import etree

from src.mcp_hnpx.tools.creation import (
    create_chapter,
    create_sequence,
    create_beat,
    create_paragraph,
)
from src.mcp_hnpx.errors import (
    FileNotFoundError,
    NotHNPXError,
    NodeNotFoundError,
    InvalidParentError,
    MissingAttributeError,
    ValidationFailedError,
)


class TestCreateChapter:
    def test_create_chapter_success(self, minimal_hnpx_file, valid_node_data):
        """Test successful chapter creation."""
        data = valid_node_data["chapter"]
        result = create_chapter(
            str(minimal_hnpx_file),
            "abc123",  # book ID
            data["title"],
            data["summary"],
            data["pov"],
        )

        assert result["success"] is True
        assert "chapter_id" in result
        assert len(result["chapter_id"]) == 6
        assert result["title"] == data["title"]
        assert result["summary"] == data["summary"]
        assert result["pov"] == data["pov"]
        assert "Created chapter" in result["message"]

        # Verify file was modified
        with open(minimal_hnpx_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert data["title"] in content
            assert data["summary"] in content
            assert data["pov"] in content

    def test_create_chapter_without_pov(self, minimal_hnpx_file, valid_node_data):
        """Test creating chapter without POV."""
        data = valid_node_data["chapter"]
        result = create_chapter(
            str(minimal_hnpx_file), "abc123", data["title"], data["summary"]
        )

        assert result["success"] is True
        assert result["pov"] is None

    def test_create_chapter_missing_title(self, minimal_hnpx_file):
        """Test creating chapter with missing title."""
        with pytest.raises(MissingAttributeError) as exc_info:
            create_chapter(
                str(minimal_hnpx_file),
                "abc123",
                "",  # empty title
                "Test summary",
            )

        assert "title" in str(exc_info.value)

    def test_create_chapter_missing_summary(self, minimal_hnpx_file):
        """Test creating chapter with missing summary."""
        with pytest.raises(MissingAttributeError) as exc_info:
            create_chapter(
                str(minimal_hnpx_file),
                "abc123",
                "Test Title",
                "",  # empty summary
            )

        assert "summary" in str(exc_info.value)

    def test_create_chapter_nonexistent_file(self):
        """Test creating chapter in non-existent file."""
        with pytest.raises(FileNotFoundError):
            create_chapter("nonexistent.xml", "abc123", "Test Title", "Test summary")

    def test_create_chapter_invalid_parent(self, sample_hnpx_file):
        """Test creating chapter with non-book parent."""
        with pytest.raises(InvalidParentError) as exc_info:
            create_chapter(
                str(sample_hnpx_file),
                "c8p2q5",  # chapter ID, not book
                "Test Title",
                "Test summary",
            )

        assert "chapter" in str(exc_info.value)
        assert "book" in str(exc_info.value)

    def test_create_chapter_nonexistent_parent(self, sample_hnpx_file):
        """Test creating chapter with non-existent parent."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            create_chapter(
                str(sample_hnpx_file), "nonexistent", "Test Title", "Test summary"
            )

        assert "nonexistent" in str(exc_info.value)

    def test_create_chapter_duplicate_title(self, temp_dir):
        """Test creating chapter with duplicate title."""
        # Create document with existing chapter
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter1 = etree.SubElement(
            root, "chapter", id="def456", title="Duplicate Title"
        )
        chapter1_summary = etree.SubElement(chapter1, "summary")
        chapter1_summary.text = "First chapter"

        file_path = temp_dir / "duplicate_title.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        with pytest.raises(ValidationFailedError) as exc_info:
            create_chapter(
                str(file_path),
                "abc123",
                "Duplicate Title",  # Same title as existing chapter
                "Second chapter",
            )

        assert "duplicate" in str(exc_info.value).lower()

    def test_create_chapter_non_hnpx_document(self, non_hnpx_file):
        """Test creating chapter in non-HNPX document."""
        with pytest.raises(NotHNPXError):
            create_chapter(str(non_hnpx_file), "abc123", "Test Title", "Test summary")


class TestCreateSequence:
    def test_create_sequence_success(self, temp_dir, valid_node_data):
        """Test successful sequence creation."""
        # Create document with chapter
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        file_path = temp_dir / "sequence_test.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        data = valid_node_data["sequence"]
        result = create_sequence(
            str(file_path),
            "def456",  # chapter ID
            data["location"],
            data["summary"],
            data["time"],
            data["pov"],
        )

        assert result["success"] is True
        assert "sequence_id" in result
        assert len(result["sequence_id"]) == 6
        assert result["location"] == data["location"]
        assert result["summary"] == data["summary"]
        assert result["time"] == data["time"]
        assert result["pov"] == data["pov"]
        assert "Created sequence" in result["message"]

    def test_create_sequence_minimal(self, temp_dir):
        """Test creating sequence with only required parameters."""
        # Create document with chapter
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        file_path = temp_dir / "sequence_minimal.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = create_sequence(
            str(file_path), "def456", "Test Location", "Test summary"
        )

        assert result["success"] is True
        assert result["time"] is None
        assert result["pov"] is None

    def test_create_sequence_missing_location(self, minimal_hnpx_file):
        """Test creating sequence with missing location."""
        with pytest.raises(MissingAttributeError) as exc_info:
            create_sequence(
                str(minimal_hnpx_file),
                "abc123",
                "",  # empty location
                "Test summary",
            )

        assert "location" in str(exc_info.value)

    def test_create_sequence_missing_summary(self, minimal_hnpx_file):
        """Test creating sequence with missing summary."""
        with pytest.raises(MissingAttributeError) as exc_info:
            create_sequence(
                str(minimal_hnpx_file),
                "abc123",
                "Test Location",
                "",  # empty summary
            )

        assert "summary" in str(exc_info.value)

    def test_create_sequence_invalid_parent(self, sample_hnpx_file):
        """Test creating sequence with non-chapter parent."""
        with pytest.raises(InvalidParentError) as exc_info:
            create_sequence(
                str(sample_hnpx_file),
                "b3k9m7",  # book ID, not chapter
                "Test Location",
                "Test summary",
            )

        assert "sequence" in str(exc_info.value)
        assert "chapter" in str(exc_info.value)

    def test_create_sequence_nonexistent_parent(self, sample_hnpx_file):
        """Test creating sequence with non-existent parent."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            create_sequence(
                str(sample_hnpx_file), "nonexistent", "Test Location", "Test summary"
            )

        assert "nonexistent" in str(exc_info.value)


class TestCreateBeat:
    def test_create_beat_success(self, temp_dir):
        """Test successful beat creation."""
        # Create document with sequence
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

        file_path = temp_dir / "beat_test.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = create_beat(
            str(file_path),
            "ghi789",  # sequence ID
            "Test beat summary",
        )

        assert result["success"] is True
        assert "beat_id" in result
        assert len(result["beat_id"]) == 6
        assert result["summary"] == "Test beat summary"
        assert "Created beat" in result["message"]

    def test_create_beat_missing_summary(self, minimal_hnpx_file):
        """Test creating beat with missing summary."""
        with pytest.raises(MissingAttributeError) as exc_info:
            create_beat(
                str(minimal_hnpx_file),
                "abc123",
                "",  # empty summary
            )

        assert "summary" in str(exc_info.value)

    def test_create_beat_invalid_parent(self, sample_hnpx_file):
        """Test creating beat with non-sequence parent."""
        with pytest.raises(InvalidParentError) as exc_info:
            create_beat(
                str(sample_hnpx_file),
                "c8p2q5",  # chapter ID, not sequence
                "Test beat summary",
            )

        assert "beat" in str(exc_info.value)
        assert "sequence" in str(exc_info.value)

    def test_create_beat_nonexistent_parent(self, sample_hnpx_file):
        """Test creating beat with non-existent parent."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            create_beat(str(sample_hnpx_file), "nonexistent", "Test beat summary")

        assert "nonexistent" in str(exc_info.value)


class TestCreateParagraph:
    def test_create_paragraph_success(self, temp_dir):
        """Test successful paragraph creation."""
        # Create document with beat
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

        file_path = temp_dir / "paragraph_test.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = create_paragraph(
            str(file_path),
            "jkl012",  # beat ID
            "Test paragraph summary",
            "This is the paragraph text content.",
            "dialogue",
            "test_char",
        )

        assert result["success"] is True
        assert "paragraph_id" in result
        assert len(result["paragraph_id"]) == 6
        assert result["summary"] == "Test paragraph summary"
        assert result["text"] == "This is the paragraph text content."
        assert result["mode"] == "dialogue"
        assert result["char"] == "test_char"
        assert "Created paragraph" in result["message"]

    def test_create_paragraph_narration_mode(self, temp_dir):
        """Test creating paragraph with narration mode."""
        # Create document with beat
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

        file_path = temp_dir / "paragraph_narration.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = create_paragraph(
            str(file_path),
            "jkl012",
            "Test paragraph summary",
            "This is narration text.",
            "narration",
        )

        assert result["success"] is True
        assert result["mode"] == "narration"
        assert result["char"] is None

    def test_create_paragraph_internal_mode(self, temp_dir):
        """Test creating paragraph with internal mode."""
        # Create document with beat
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

        file_path = temp_dir / "paragraph_internal.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = create_paragraph(
            str(file_path),
            "jkl012",
            "Test paragraph summary",
            "This is internal thought text.",
            "internal",
            "test_char",
        )

        assert result["success"] is True
        assert result["mode"] == "internal"
        assert result["char"] == "test_char"

    def test_create_paragraph_missing_summary(self, minimal_hnpx_file):
        """Test creating paragraph with missing summary."""
        with pytest.raises(MissingAttributeError) as exc_info:
            create_paragraph(
                str(minimal_hnpx_file),
                "abc123",
                "",  # empty summary
                "Test text",
            )

        assert "summary" in str(exc_info.value)

    def test_create_paragraph_missing_text(self, minimal_hnpx_file):
        """Test creating paragraph with missing text."""
        with pytest.raises(MissingAttributeError) as exc_info:
            create_paragraph(
                str(minimal_hnpx_file),
                "abc123",
                "Test summary",
                "",  # empty text
            )

        assert "text" in str(exc_info.value)

    def test_create_paragraph_dialogue_without_char(self, temp_dir):
        """Test creating dialogue paragraph without character."""
        # Create document with beat
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

        file_path = temp_dir / "paragraph_no_char.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        with pytest.raises(Exception):  # Should raise MissingCharError
            create_paragraph(
                str(file_path),
                "jkl012",
                "Test summary",
                "Test dialogue text.",
                "dialogue",  # dialogue mode without char
            )

    def test_create_paragraph_invalid_mode(self, minimal_hnpx_file):
        """Test creating paragraph with invalid mode."""
        with pytest.raises(Exception):  # Should raise InvalidAttributeError
            create_paragraph(
                str(minimal_hnpx_file),
                "abc123",
                "Test summary",
                "Test text.",
                "invalid_mode",
            )

    def test_create_paragraph_invalid_parent(self, sample_hnpx_file):
        """Test creating paragraph with non-beat parent."""
        with pytest.raises(InvalidParentError) as exc_info:
            create_paragraph(
                str(sample_hnpx_file),
                "s4r7t9",  # sequence ID, not beat
                "Test summary",
                "Test text.",
            )

        assert "paragraph" in str(exc_info.value)
        assert "beat" in str(exc_info.value)

    def test_create_paragraph_nonexistent_parent(self, sample_hnpx_file):
        """Test creating paragraph with non-existent parent."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            create_paragraph(
                str(sample_hnpx_file), "nonexistent", "Test summary", "Test text."
            )

        assert "nonexistent" in str(exc_info.value)


class TestCreationIntegration:
    def test_create_complete_structure(self, temp_dir):
        """Test creating a complete HNPX structure."""
        # Start with minimal document
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        file_path = temp_dir / "complete_structure.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Create chapter
        chapter_result = create_chapter(
            str(file_path),
            "abc123",
            "Test Chapter",
            "Test chapter summary",
            "main_char",
        )
        chapter_id = chapter_result["chapter_id"]

        # Create sequence
        sequence_result = create_sequence(
            str(file_path),
            chapter_id,
            "Test Location",
            "Test sequence summary",
            "morning",
            "main_char",
        )
        sequence_id = sequence_result["sequence_id"]

        # Create beat
        beat_result = create_beat(str(file_path), sequence_id, "Test beat summary")
        beat_id = beat_result["beat_id"]

        # Create paragraphs
        paragraph1_result = create_paragraph(
            str(file_path),
            beat_id,
            "First paragraph summary",
            "This is the first paragraph.",
            "narration",
        )

        paragraph2_result = create_paragraph(
            str(file_path),
            beat_id,
            "Second paragraph summary",
            "This is dialogue text.",
            "dialogue",
            "main_char",
        )

        # Verify all creations succeeded
        assert all(
            result["success"]
            for result in [
                chapter_result,
                sequence_result,
                beat_result,
                paragraph1_result,
                paragraph2_result,
            ]
        )

        # Verify final document structure
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Test Chapter" in content
        assert "Test Location" in content
        assert "Test beat summary" in content
        assert "This is the first paragraph" in content
        assert "This is dialogue text" in content
        assert "main_char" in content

    def test_unique_ids_across_creations(self, temp_dir):
        """Test that all created nodes have unique IDs."""
        # Start with minimal document
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        file_path = temp_dir / "unique_ids.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Create multiple nodes
        ids = set()

        for i in range(5):
            chapter_result = create_chapter(
                str(file_path), "abc123", f"Chapter {i + 1}", f"Chapter {i + 1} summary"
            )
            ids.add(chapter_result["chapter_id"])

        # Verify all IDs are unique
        assert len(ids) == 5
        assert all(len(id_str) == 6 for id_str in ids)
