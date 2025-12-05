"""
Tests for HNPX utility functions.
"""

from unittest.mock import patch, mock_open

import pytest
from lxml import etree

from src.mcp_hnpx.hnpx_utils import (
    generate_random_id,
    validate_id_format,
    parse_xml_file,
    create_minimal_hnpx_document,
    format_xml_for_output,
    get_all_ids,
    is_valid_hnpx_document,
    get_element_type,
    validate_narrative_mode,
    get_pov_for_paragraph,
    find_node_by_id,
    get_parent_node,
    get_required_children,
)
from src.mcp_hnpx.errors import (
    FileNotFoundError,
    InvalidXMLError,
    InvalidAttributeError,
    MissingCharError,
)


class TestGenerateRandomID:
    def test_generate_unique_id(self, existing_ids):
        """Test generating a unique ID."""
        new_id = generate_random_id(existing_ids)
        assert new_id not in existing_ids
        assert len(new_id) == 6
        assert all(c.islower() or c.isdigit() for c in new_id)

    def test_generate_id_without_existing(self):
        """Test generating ID without existing IDs."""
        new_id = generate_random_id()
        assert len(new_id) == 6
        assert all(c.islower() or c.isdigit() for c in new_id)

    def test_generate_id_with_empty_set(self):
        """Test generating ID with empty set."""
        new_id = generate_random_id(set())
        assert len(new_id) == 6
        assert all(c.islower() or c.isdigit() for c in new_id)

    def test_generate_id_collision_handling(self):
        """Test that ID generation handles collisions."""
        # Create a set with many possible IDs to force potential collisions
        existing_ids = {f"{i:06d}"[:6].lower() for i in range(1000)}
        # This should still work even with many existing IDs
        new_id = generate_random_id(existing_ids)
        assert new_id not in existing_ids


class TestValidateIDFormat:
    def test_valid_ids(self):
        """Test validation of valid ID formats."""
        valid_ids = ["a1b2c3", "123456", "abc123", "z9y8x7"]
        for id_str in valid_ids:
            assert validate_id_format(id_str) is True

    def test_invalid_length(self):
        """Test validation of IDs with invalid length."""
        invalid_ids = ["abc", "12345", "abcdefg", "1234567"]
        for id_str in invalid_ids:
            assert validate_id_format(id_str) is False

    def test_invalid_characters(self):
        """Test validation of IDs with invalid characters."""
        invalid_ids = ["ABC123", "abc-12", "abc_12", "abc!23", "abc 23"]
        for id_str in invalid_ids:
            assert validate_id_format(id_str) is False

    def test_empty_id(self):
        """Test validation of empty ID."""
        assert validate_id_format("") is False


class TestParseXMLFile:
    def test_parse_valid_file(self, sample_hnpx_file):
        """Test parsing a valid XML file."""
        root = parse_xml_file(str(sample_hnpx_file))
        assert root.tag == "book"
        assert root.get("id") == "b3k9m7"

    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_xml_file("nonexistent_file.xml")

    def test_parse_invalid_xml(self, invalid_xml_file):
        """Test parsing an invalid XML file."""
        with pytest.raises(InvalidXMLError):
            parse_xml_file(str(invalid_xml_file))

    @patch("builtins.open", mock_open(read_data="<root><item>test</item></root>"))
    @patch("os.path.exists", return_value=True)
    def test_parse_with_mock(self, mock_exists, mock_file):
        """Test parsing with mocked file operations."""
        root = parse_xml_file("test.xml")
        assert root.tag == "root"


class TestCreateMinimalHNPXDocument:
    def test_create_minimal_document(self):
        """Test creating a minimal HNPX document."""
        root = create_minimal_hnpx_document()
        assert root.tag == "book"
        assert root.get("id") is not None
        assert len(root.get("id")) == 6
        assert root.find("summary") is not None
        assert root.find("summary").text == "New book"

    def test_minimal_document_id_format(self):
        """Test that minimal document has valid ID format."""
        root = create_minimal_hnpx_document()
        book_id = root.get("id")
        assert validate_id_format(book_id) is True

    def test_minimal_document_unique_ids(self):
        """Test that multiple minimal documents have unique IDs."""
        ids = set()
        for _ in range(10):
            root = create_minimal_hnpx_document()
            book_id = root.get("id")
            assert book_id not in ids
            ids.add(book_id)


class TestFormatXMLOutput:
    def test_format_xml_output(self, sample_hnpx_document):
        """Test formatting XML for output."""
        xml_str = format_xml_for_output(sample_hnpx_document)
        assert "<book" in xml_str
        assert "b3k9m7" in xml_str
        assert "Boogiepop" in xml_str

    def test_format_empty_element(self):
        """Test formatting an empty element."""
        element = etree.Element("test")
        xml_str = format_xml_for_output(element)
        assert "<test" in xml_str

    def test_format_element_with_attributes(self):
        """Test formatting element with attributes."""
        element = etree.Element("test", attr1="value1", attr2="value2")
        xml_str = format_xml_for_output(element)
        assert 'attr1="value1"' in xml_str
        assert 'attr2="value2"' in xml_str


class TestGetAllIDs:
    def test_get_all_ids_from_sample(self, sample_hnpx_document):
        """Test extracting all IDs from sample document."""
        ids = get_all_ids(sample_hnpx_document)
        expected_ids = {"b3k9m7", "c8p2q5", "s4r7t9", "b1v6x3", "p9m5k2"}
        assert ids == expected_ids

    def test_get_all_ids_empty_document(self):
        """Test extracting IDs from empty document."""
        root = etree.Element("root")
        ids = get_all_ids(root)
        assert ids == set()

    def test_get_all_ids_no_id_attributes(self):
        """Test extracting IDs when no elements have ID attributes."""
        root = etree.Element("root")
        etree.SubElement(root, "child1")
        etree.SubElement(root, "child2")

        ids = get_all_ids(root)
        assert ids == set()


class TestIsValidHNPXDocument:
    def test_valid_hnpx_document(self, sample_hnpx_document):
        """Test validation of valid HNPX document."""
        assert is_valid_hnpx_document(sample_hnpx_document) is True

    def test_invalid_root_element(self):
        """Test validation with wrong root element."""
        root = etree.Element("notbook", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test"
        assert is_valid_hnpx_document(root) is False

    def test_missing_book_id(self):
        """Test validation with missing book ID."""
        root = etree.Element("book")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test"
        assert is_valid_hnpx_document(root) is False

    def test_missing_book_summary(self):
        """Test validation with missing book summary."""
        root = etree.Element("book", id="abc123")
        assert is_valid_hnpx_document(root) is False

    def test_empty_book_summary(self):
        """Test validation with empty book summary."""
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = ""
        assert is_valid_hnpx_document(root) is False

    def test_whitespace_only_summary(self):
        """Test validation with whitespace-only summary."""
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "   \n\t  "
        assert is_valid_hnpx_document(root) is False


class TestGetElementType:
    def test_get_element_type(self, sample_hnpx_document):
        """Test getting element type."""
        book = sample_hnpx_document
        chapter = book.find("chapter")
        sequence = chapter.find("sequence")

        assert get_element_type(book) == "book"
        assert get_element_type(chapter) == "chapter"
        assert get_element_type(sequence) == "sequence"


class TestValidateNarrativeMode:
    def test_valid_narration_mode(self):
        """Test validation of narration mode."""
        validate_narrative_mode("narration", None)

    def test_valid_dialogue_mode_with_char(self):
        """Test validation of dialogue mode with character."""
        validate_narrative_mode("dialogue", "john")

    def test_valid_internal_mode(self):
        """Test validation of internal mode."""
        validate_narrative_mode("internal", None)
        validate_narrative_mode("internal", "john")

    def test_invalid_mode(self):
        """Test validation of invalid mode."""
        with pytest.raises(InvalidAttributeError):
            validate_narrative_mode("invalid", None)

    def test_dialogue_without_char(self):
        """Test dialogue mode without character."""
        with pytest.raises(MissingCharError):
            validate_narrative_mode("dialogue", None)


class TestGetPOVForParagraph:
    def test_direct_char_attribute(self, sample_hnpx_document):
        """Test getting POV from direct char attribute."""
        paragraph = sample_hnpx_document.xpath("//paragraph[@char]")[0]
        pov = get_pov_for_paragraph(paragraph, sample_hnpx_document)
        assert pov == paragraph.get("char")

    def test_internal_mode_inheritance(self, sample_hnpx_document):
        """Test POV inheritance for internal mode."""
        # Create a paragraph with internal mode but no char
        beat = sample_hnpx_document.find("//beat")
        paragraph = etree.SubElement(beat, "paragraph", id="test123", mode="internal")
        summary = etree.SubElement(paragraph, "summary")
        summary.text = "Test"

        pov = get_pov_for_paragraph(paragraph, sample_hnpx_document)
        # Should inherit from sequence POV
        assert pov == "suema"

    def test_no_pov_found(self, sample_hnpx_document):
        """Test when no POV is found."""
        # Create a paragraph with no POV info
        beat = sample_hnpx_document.find("//beat")
        paragraph = etree.SubElement(beat, "paragraph", id="test123")
        summary = etree.SubElement(paragraph, "summary")
        summary.text = "Test"

        pov = get_pov_for_paragraph(paragraph, sample_hnpx_document)
        assert pov is None


class TestFindNodeByID:
    def test_find_existing_node(self, sample_hnpx_document):
        """Test finding an existing node by ID."""
        node = find_node_by_id(sample_hnpx_document, "c8p2q5")
        assert node is not None
        assert node.tag == "chapter"
        assert node.get("id") == "c8p2q5"

    def test_find_nonexistent_node(self, sample_hnpx_document):
        """Test finding a non-existent node by ID."""
        node = find_node_by_id(sample_hnpx_document, "nonexistent")
        assert node is None

    def test_find_duplicate_ids(self):
        """Test finding node when duplicate IDs exist (should return first)."""
        root = etree.Element("root")
        child1 = etree.SubElement(root, "child", id="duplicate")
        etree.SubElement(root, "child", id="duplicate")

        node = find_node_by_id(root, "duplicate")
        assert node is not None
        assert node == child1


class TestGetParentNode:
    def test_get_parent_with_valid_parent(self, sample_hnpx_document):
        """Test getting parent of a node with valid parent."""
        chapter = sample_hnpx_document.find("chapter")
        parent = get_parent_node(sample_hnpx_document, chapter)
        assert parent == sample_hnpx_document

    def test_get_parent_of_root(self, sample_hnpx_document):
        """Test getting parent of root element."""
        parent = get_parent_node(sample_hnpx_document, sample_hnpx_document)
        assert parent is None

    def test_get_parent_of_orphan(self):
        """Test getting parent of orphaned element."""
        orphan = etree.Element("orphan")
        root = etree.Element("root")
        parent = get_parent_node(root, orphan)
        assert parent is None


class TestGetRequiredChildren:
    def test_get_required_children_for_all_types(self):
        """Test getting required children for all element types."""
        expected = {
            "book": ["chapter"],
            "chapter": ["sequence"],
            "sequence": ["beat"],
            "beat": ["paragraph"],
            "paragraph": [],
        }

        for element_type, expected_children in expected.items():
            children = get_required_children(element_type)
            assert children == expected_children

    def test_get_required_children_unknown_type(self):
        """Test getting required children for unknown element type."""
        children = get_required_children("unknown")
        assert children == []
