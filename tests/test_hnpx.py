import pytest
from lxml import etree
import mcp_hnpx.hnpx as hnpx
from mcp_hnpx.exceptions import ValidationError


def test_parse_document(complete_xml_path):
    tree = hnpx.parse_document(str(complete_xml_path))
    assert isinstance(tree, etree.ElementTree)
    assert tree.getroot().tag == "book"


def test_validate_document_valid(complete_xml_path):
    tree = hnpx.parse_document(str(complete_xml_path))
    hnpx.validate_document(tree)


def test_validate_document_invalid_missing_attributes():
    invalid_xml = """<book>
  <summary>Test book</summary>
  <chapter>
    <summary>Test chapter</summary>
  </chapter>
</book>"""

    tree = etree.fromstring(invalid_xml)
    tree = etree.ElementTree(tree)

    with pytest.raises(ValidationError):
        hnpx.validate_document(tree)


def test_validate_document_invalid_wrong_hierarchy():
    invalid_xml = """<book id="test01">
  <summary>Test book</summary>
  <paragraph id="para01">
    Test paragraph
  </paragraph>
</book>"""

    tree = etree.fromstring(invalid_xml)
    tree = etree.ElementTree(tree)

    with pytest.raises(ValidationError):
        hnpx.validate_document(tree)


def test_validate_document_invalid_duplicate_ids():
    invalid_xml = """<book id="test01">
  <summary>Test book</summary>
  <chapter id="test01">
    <summary>Test chapter</summary>
  </chapter>
</book>"""

    tree = etree.fromstring(invalid_xml)
    tree = etree.ElementTree(tree)

    with pytest.raises(ValidationError):
        hnpx.validate_document(tree)


def test_save_document(temp_file):
    book = etree.Element("book", id="test01")
    summary = etree.SubElement(book, "summary")
    summary.text = "Test book"
    tree = etree.ElementTree(book)

    hnpx.save_document(tree, temp_file)

    saved_tree = hnpx.parse_document(temp_file)
    assert saved_tree.getroot().get("id") == "test01"


def test_get_all_ids(complete_xml_path):
    tree = hnpx.parse_document(str(complete_xml_path))
    ids = hnpx.get_all_ids(tree)

    expected_ids = {
        "glyjor",
        "3295p0",
        "104lac",
        "gr5peb",
        "uvxuqh",
        "gu81br",
        "ef955x",
        "bqrrw4",
        "nxf930",
    }
    assert ids == expected_ids


def test_generate_unique_id():
    existing_ids = {"abc123", "def456"}
    new_id = hnpx.generate_unique_id(existing_ids)

    assert len(new_id) == 6
    assert new_id not in existing_ids
    assert all(c.islower() or c.isdigit() for c in new_id)


def test_find_node_exists(complete_xml_path):
    tree = hnpx.parse_document(str(complete_xml_path))
    node = hnpx.find_node(tree, "glyjor")

    assert node is not None
    assert node.tag == "book"
    assert node.get("id") == "glyjor"


def test_find_node_not_exists(complete_xml_path):
    tree = hnpx.parse_document(str(complete_xml_path))
    node = hnpx.find_node(tree, "nonexistent")

    assert node is None


def test_get_child_count(complete_xml_path):
    tree = hnpx.parse_document(str(complete_xml_path))
    book = hnpx.find_node(tree, "glyjor")
    chapter = hnpx.find_node(tree, "3295p0")

    assert hnpx.get_child_count(book) == 1
    assert hnpx.get_child_count(chapter) == 1


def test_find_first_empty_container_complete(complete_xml_path):
    tree = hnpx.parse_document(str(complete_xml_path))
    empty = hnpx.find_first_empty_container(tree)

    assert empty is None


def test_find_first_empty_container_incomplete(incomplete_xml_path):
    tree = hnpx.parse_document(str(incomplete_xml_path))
    empty = hnpx.find_first_empty_container(tree)

    assert empty is not None
    assert empty.tag == "beat"
    assert empty.get("id") == "gr5peb"


def test_find_first_empty_container_with_start_node(incomplete_xml_path):
    tree = hnpx.parse_document(str(incomplete_xml_path))
    chapter = hnpx.find_node(tree, "3295p0")
    empty = hnpx.find_first_empty_container(tree, chapter)

    assert empty is not None
    assert empty.tag == "beat"
    assert empty.get("id") == "gr5peb"


def test_render_paragraph_narration():
    paragraph = etree.Element("paragraph", mode="narration")
    paragraph.text = "This is a test paragraph."

    result = hnpx.render_paragraph(paragraph)
    assert result == "This is a test paragraph."


def test_render_paragraph_dialogue():
    paragraph = etree.Element("paragraph", mode="dialogue", char="john")
    paragraph.text = "Hello there!"

    result = hnpx.render_paragraph(paragraph)
    assert result == "Hello there!"


def test_render_paragraph_internal():
    paragraph = etree.Element("paragraph", mode="internal")
    paragraph.text = "This is a thought."

    result = hnpx.render_paragraph(paragraph)
    assert result == "This is a thought."


def test_render_paragraph_empty():
    paragraph = etree.Element("paragraph", mode="narration")
    paragraph.text = ""

    result = hnpx.render_paragraph(paragraph)
    assert result == ""
