import pytest

import mcp_hnpx.tools as tools
from mcp_hnpx.exceptions import (
    InvalidAttributeError,
    InvalidHierarchyError,
    InvalidOperationError,
    MissingAttributeError,
    NodeNotFoundError,
)


def test_create_document(temp_file):
    tools.create_document(temp_file)

    tree = tools.hnpx.parse_document(temp_file)
    assert tree.getroot().tag == "book"
    assert tree.getroot().get("id") is not None


def test_create_document_invalid_path():
    with pytest.raises(Exception):
        tools.create_document("/invalid/path/test.xml")


def test_get_next_empty_container(incomplete_xml_path):
    result = tools.get_next_empty_container(str(incomplete_xml_path))

    assert "gr5peb" in result
    assert "<beat" in result


def test_get_next_empty_container_complete(complete_xml_path):
    result = tools.get_next_empty_container(str(complete_xml_path))

    assert "No empty containers found" in result


def test_get_next_empty_container_in_node(incomplete_xml_path):
    result = tools.get_next_empty_container_in_node(str(incomplete_xml_path), "3295p0")

    assert "gr5peb" in result
    assert "<beat" in result


def test_get_next_empty_container_in_node_not_found(incomplete_xml_path):
    with pytest.raises(NodeNotFoundError):
        tools.get_next_empty_container_in_node(str(incomplete_xml_path), "nonexistent")


def test_get_node(complete_xml_path):
    result = tools.get_node(str(complete_xml_path), "glyjor")

    assert "<book" in result
    assert 'id="glyjor"' in result
    assert "chapter" not in result


def test_get_node_not_found(complete_xml_path):
    with pytest.raises(NodeNotFoundError):
        tools.get_node(str(complete_xml_path), "nonexistent")


def test_get_subtree(complete_xml_path):
    result = tools.get_subtree(str(complete_xml_path), "3295p0")

    assert "<chapter" in result
    assert 'id="3295p0"' in result
    assert "<sequence" in result
    assert "<beat" in result
    assert "<paragraph" in result
    assert "One instant, I pray of you." in result


def test_get_direct_children(complete_xml_path):
    result = tools.get_direct_children(str(complete_xml_path), "3295p0")

    assert "<sequence" in result
    assert 'id="104lac"' in result
    assert "beat" not in result
    assert "paragraph" not in result
    assert "The interrogation of Parker begins." in result
    assert "As we entered the room" not in result


def test_get_node_path(complete_xml_path):
    result = tools.get_node_path(str(complete_xml_path), "gr5peb")

    assert "<book" in result
    assert "<chapter" in result
    assert "<sequence" in result
    assert "<beat" in result


def test_get_document_at_depth_full(complete_xml_path):
    result = tools.get_document_at_depth(str(complete_xml_path), "full")

    assert "<book" in result
    assert "<chapter" in result
    assert "<sequence" in result
    assert "<beat" in result
    assert "<paragraph" in result


def test_get_document_at_depth_beat(complete_xml_path):
    result = tools.get_document_at_depth(str(complete_xml_path), "beat")

    assert "<book" in result
    assert "<chapter" in result
    assert "<sequence" in result
    assert "<beat" in result
    assert "<paragraph" not in result


def test_get_document_at_depth_invalid_level(complete_xml_path):
    with pytest.raises(InvalidAttributeError):
        tools.get_document_at_depth(str(complete_xml_path), "invalid")


def test_create_chapter(temp_file, complete_xml_path):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.create_chapter(
        temp_file, "glyjor", "Test Chapter", "Test summary", "test_char"
    )

    tree = tools.hnpx.parse_document(temp_file)
    chapters = tree.xpath("//chapter")
    assert len(chapters) == 2
    assert chapters[1].get("title") == "Test Chapter"
    assert chapters[1].get("pov") == "test_char"


def test_create_sequence(temp_file, complete_xml_path):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.create_sequence(
        temp_file, "3295p0", "Test Location", "Test summary", "morning", "test_char"
    )

    tree = tools.hnpx.parse_document(temp_file)
    sequences = tree.xpath("//sequence")
    assert len(sequences) == 2
    assert sequences[1].get("location") == "Test Location"
    assert sequences[1].get("time") == "morning"
    assert sequences[1].get("pov") == "test_char"


def test_create_beat(temp_file, complete_xml_path):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.create_beat(temp_file, "104lac", "Test beat summary")

    tree = tools.hnpx.parse_document(temp_file)
    beats = tree.xpath("//beat")
    assert len(beats) == 2


def test_create_paragraph(temp_file, complete_xml_path):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.create_paragraph(
        temp_file,
        "gr5peb",
        "Test text",
        "dialogue",
        "test_char",
    )

    tree = tools.hnpx.parse_document(temp_file)
    paragraphs = tree.xpath("//paragraph")
    assert len(paragraphs) == 6
    assert paragraphs[5].get("mode") == "dialogue"
    assert paragraphs[5].get("char") == "test_char"
    assert paragraphs[5].text == "Test text"


def test_create_paragraph_dialogue_missing_char(temp_file, complete_xml_path):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(MissingAttributeError):
        tools.create_paragraph(temp_file, "gr5peb", "Test text", "dialogue")


def test_edit_node_attributes(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.edit_node_attributes(
        temp_file, "3295p0", {"title": "New Title", "pov": "new_pov"}
    )

    tree = tools.hnpx.parse_document(temp_file)
    chapter = tools.hnpx.find_node(tree, "3295p0")
    assert chapter.get("title") == "New Title"
    assert chapter.get("pov") == "new_pov"


def test_edit_node_attributes_invalid_id(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(NodeNotFoundError):
        tools.edit_node_attributes(temp_file, "nonexistent", {"title": "New Title"})


def test_edit_node_attributes_cannot_modify_id(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(InvalidOperationError):
        tools.edit_node_attributes(temp_file, "3295p0", {"id": "new_id"})


def test_remove_node(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.remove_node(temp_file, "gr5peb")

    tree = tools.hnpx.parse_document(temp_file)
    beat = tools.hnpx.find_node(tree, "gr5peb")
    assert beat is None


def test_remove_node_not_found(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(NodeNotFoundError):
        tools.remove_node(temp_file, "nonexistent")


def test_remove_node_book(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(InvalidOperationError):
        tools.remove_node(temp_file, "glyjor")


def test_reorder_children(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tree = tools.hnpx.parse_document(temp_file)
    beat = tools.hnpx.find_node(tree, "gr5peb")
    paragraphs = [child for child in beat if child.tag != "summary"]
    paragraph_ids = [p.get("id") for p in paragraphs]

    reversed_ids = list(reversed(paragraph_ids))

    tools.reorder_children(temp_file, "gr5peb", reversed_ids)

    new_tree = tools.hnpx.parse_document(temp_file)
    new_beat = tools.hnpx.find_node(new_tree, "gr5peb")
    new_paragraphs = [child for child in new_beat if child.tag != "summary"]
    new_paragraph_ids = [p.get("id") for p in new_paragraphs]

    assert new_paragraph_ids == reversed_ids


def test_reorder_children_invalid_ids(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(InvalidOperationError):
        tools.reorder_children(temp_file, "gr5peb", ["nonexistent1", "nonexistent2"])


def test_edit_summary(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.edit_summary(temp_file, "3295p0", "New summary text")

    tree = tools.hnpx.parse_document(temp_file)
    chapter = tools.hnpx.find_node(tree, "3295p0")
    summary = chapter.find("summary")
    assert summary.text == "New summary text"


def test_edit_summary_not_found(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(NodeNotFoundError):
        tools.edit_summary(temp_file, "nonexistent", "New summary text")


def test_edit_paragraph_text(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.edit_paragraph_text(temp_file, "uvxuqh", "New paragraph text")

    tree = tools.hnpx.parse_document(temp_file)
    paragraph = tools.hnpx.find_node(tree, "uvxuqh")
    assert paragraph.text == "New paragraph text"


def test_edit_paragraph_text_not_found(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(NodeNotFoundError):
        tools.edit_paragraph_text(temp_file, "nonexistent", "New text")


def test_edit_paragraph_text_not_paragraph(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(InvalidOperationError):
        tools.edit_paragraph_text(temp_file, "3295p0", "New text")


def test_move_nodes_single(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.move_nodes(temp_file, ["gr5peb"], "104lac")

    tree = tools.hnpx.parse_document(temp_file)
    beat = tools.hnpx.find_node(tree, "gr5peb")
    parent = beat.getparent()
    assert parent.get("id") == "104lac"


def test_move_nodes_multiple(mixed_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(mixed_xml_path).read())

    child_ids = ["76w5gp", "9zgowk"]
    tools.move_nodes(temp_file, child_ids, "en92qn")

    new_tree = tools.hnpx.parse_document(temp_file)
    parent2 = tools.hnpx.find_node(new_tree, "en92qn")
    children2 = [child.get("id") for child in parent2 if child.tag != "summary"]
    assert children2 == ["ybqiqe", "tmwumx"] + child_ids

    parent1 = tools.hnpx.find_node(new_tree, "wyxbo0")
    children1 = [child.get("id") for child in parent1 if child.tag != "summary"]
    assert children1 == ["zexcv5"]


def test_move_nodes_not_found(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(NodeNotFoundError):
        tools.move_nodes(temp_file, ["nonexistent"], "104lac")


def test_move_nodes_invalid_hierarchy(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(InvalidHierarchyError):
        tools.move_nodes(temp_file, ["uvxuqh"], "glyjor")


def test_remove_node_children(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    tools.remove_node_children(temp_file, "gr5peb")

    tree = tools.hnpx.parse_document(temp_file)
    beat = tools.hnpx.find_node(tree, "gr5peb")
    children = [child for child in beat if child.tag != "summary"]
    assert len(children) == 0


def test_remove_node_children_not_found(complete_xml_path, temp_file):
    with open(temp_file, "w") as f:
        f.write(open(complete_xml_path).read())

    with pytest.raises(NodeNotFoundError):
        tools.remove_node_children(temp_file, "nonexistent")


def test_render_node(complete_xml_path):
    result = tools.render_node(str(complete_xml_path), "gr5peb")

    assert "[gr5peb] Beat: Initial confrontation and accusation of blackmail." in result
    assert "On arrival at The Larches" in result


def test_render_node_not_found(complete_xml_path):
    with pytest.raises(NodeNotFoundError):
        tools.render_node(str(complete_xml_path), "nonexistent")


def test_render_document(complete_xml_path):
    result = tools.render_document(str(complete_xml_path))

    assert "On arrival at The Larches" in result
    assert "poirot: 'Good morning, Parker,'" in result


def test_unicode_xml_output(unicode_xml_path, temp_file):
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(open(unicode_xml_path, encoding="utf-8").read())

    result = tools.get_node(temp_file, "c8e4d1")

    assert "Улики 🔍" in result
    assert "sheppard" in result

    result = tools.get_node(temp_file, "x7j5m2")

    assert "Гостиная 🛋️" in result
    assert "вечер 🌙" in result

    result = tools.get_node(temp_file, "z5y2x4")

    assert "пуаро" in result
    assert "Надеюсь, вы не расстроены?" in result
