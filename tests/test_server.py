from pathlib import Path


from mcp_hnpx.hnpx import HNPXDocument, create_element, generate_id


def test_hnpx_document_loading():
    """Test loading the example document."""
    doc = HNPXDocument("tests/resources/example.xml")
    assert doc.file_path == Path("tests/resources/example.xml")
    assert doc.root.tag is not None


def test_hnpx_element_by_id():
    """Test getting a node by ID."""
    doc = HNPXDocument("tests/resources/example.xml")
    # Get the first element with an ID from the document
    elements_with_ids = doc.root.xpath("//*[@id]")
    assert len(elements_with_ids) > 0, "No elements with IDs found in example.xml"

    first_element_id = elements_with_ids[0].get("id")
    node = doc.get_element_by_id(first_element_id)
    assert node is not None
    assert node.tag is not None
    attributes = doc.get_element_attributes(node)
    assert isinstance(attributes, dict)
    summary = doc.get_element_summary(node)
    assert isinstance(summary, str)


def test_hnpx_element_context():
    """Test getting element context (parent and siblings)."""
    doc = HNPXDocument("tests/resources/example.xml")
    # Find a paragraph element to test context
    paragraphs = doc.root.xpath("//paragraph[@id]")
    if len(paragraphs) > 0:
        paragraph_id = paragraphs[0].get("id")
        node = doc.get_element_by_id(paragraph_id)
        if node is not None:
            parent = doc.get_parent(node)
            assert parent is not None
            assert parent.tag is not None

            siblings = doc.get_siblings(node)
            assert isinstance(siblings, list)
            for sibling in siblings[:3]:
                assert sibling.tag is not None
                # Only check for ID on elements that should have them (not summary elements)
                if sibling.tag != "summary":
                    assert sibling.get("id") is not None
                # Summary elements don't have their own summary, so skip the check for them
                if sibling.tag != "summary":
                    assert isinstance(doc.get_element_summary(sibling), str)


def test_hnpx_empty_containers():
    """Test finding empty containers."""
    doc = HNPXDocument("tests/resources/example.xml")
    empty_containers = doc.find_empty_containers(5)
    assert isinstance(empty_containers, list)
    for container in empty_containers:
        assert container.tag is not None
        assert container.get("id") is not None
        assert isinstance(doc.get_element_summary(container), str)


def test_hnpx_search():
    """Test search functionality."""
    doc = HNPXDocument("tests/resources/example.xml")
    results = doc.search_elements(text_contains="Boogiepop")
    assert isinstance(results, list)
    for result in results[:3]:
        assert result.tag is not None
        # Only check for ID on elements that should have them (not summary elements)
        if result.tag != "summary":
            assert result.get("id") is not None
        # Summary elements don't have their own summary, so skip the check for them
        if result.tag != "summary":
            assert isinstance(doc.get_element_summary(result), str)


def test_hnpx_validation():
    """Test document validation."""
    doc = HNPXDocument("tests/resources/example.xml")
    is_valid, errors = doc.validate()
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)
    if errors:
        for error in errors[:3]:
            assert isinstance(error, str)


def test_hnpx_statistics():
    """Test document statistics."""
    doc = HNPXDocument("tests/resources/example.xml")
    stats = doc.get_document_stats()
    assert isinstance(stats, dict)
    assert "total_elements" in stats
    assert "total_paragraphs" in stats
    assert "total_words" in stats
    assert "max_depth" in stats
    assert "pov_characters" in stats
    assert "narrative_modes" in stats


def test_id_generation():
    """Test ID generation."""
    for _ in range(5):
        id_val = generate_id()
        assert isinstance(id_val, str)
        assert len(id_val) == 6  # IDs should be exactly 6 characters
        # Check that ID contains only lowercase letters and digits
        assert all(c.islower() or c.isdigit() for c in id_val)


def test_element_creation():
    """Test element creation."""
    # Create a paragraph with auto-generated ID
    para = create_element("paragraph", "Test paragraph summary", mode="narration")
    para.text = "This is test paragraph content."
    assert para.tag == "paragraph"
    assert para.get("id") is not None
    assert len(para.get("id")) == 6
    assert para.find("summary").text == "Test paragraph summary"
    assert para.text == "This is test paragraph content."

    # Create a beat with auto-generated ID
    beat = create_element("beat", "Test beat summary")
    beat.append(para)
    assert beat.tag == "beat"
    assert beat.get("id") is not None
    assert len(beat.get("id")) == 6
    # Beat should have 2 children total: summary and paragraph
    assert len(list(beat)) == 2
    # But get_children should exclude summary, so only 1 child (paragraph)
    doc = HNPXDocument("tests/resources/example.xml")
    assert len(doc.get_children(beat)) == 1

    # Test creating elements with auto-generated IDs
    auto_para = create_element("paragraph", "Auto-generated paragraph")
    assert auto_para.tag == "paragraph"
    assert auto_para.get("id") is not None
    assert len(auto_para.get("id")) == 6
    assert auto_para.find("summary").text == "Auto-generated paragraph"

    auto_beat = create_element("beat", "Auto-generated beat")
    assert auto_beat.tag == "beat"
    assert auto_beat.get("id") is not None
    assert len(auto_beat.get("id")) == 6
    assert auto_beat.find("summary").text == "Auto-generated beat"


def test_mcp_server_get_node():
    """Test MCP server get_node functionality."""
    from mcp_hnpx.server import get_node

    # Get the first element with an ID from the document
    doc = HNPXDocument("tests/resources/example.xml")
    elements_with_ids = doc.root.xpath("//*[@id]")
    assert len(elements_with_ids) > 0, "No elements with IDs found in example.xml"

    first_element_id = elements_with_ids[0].get("id")

    # Access the underlying function from the FastMCP tool
    result = get_node.fn("tests/resources/example.xml", first_element_id)
    assert result is not None
    assert isinstance(result, str)
    # Should be valid JSON
    import json

    parsed_result = json.loads(result)
    assert "id" in parsed_result
    assert "tag" in parsed_result
    assert "attributes" in parsed_result
    assert "summary" in parsed_result


def test_mcp_server_get_empty_containers():
    """Test MCP server get_empty_containers functionality."""
    from mcp_hnpx.server import get_empty_containers

    # Access the underlying function from the FastMCP tool
    result = get_empty_containers.fn("tests/resources/example.xml", 3)
    assert result is not None
    assert isinstance(result, str)
    # Should be valid JSON
    import json

    parsed_result = json.loads(result)
    assert isinstance(parsed_result, list)
    assert len(parsed_result) <= 3
    for container in parsed_result:
        assert "id" in container
        assert "tag" in container
        assert "summary" in container


def test_mcp_server_search_nodes():
    """Test that search_nodes was removed - this test should be skipped."""
    # search_nodes was removed in the redesign, so this test is no longer relevant
    # AI agents should use get_node and render_node for navigation instead
    assert True


def test_incomplete_document_loading():
    """Test loading the incomplete document."""
    doc = HNPXDocument("tests/resources/incomplete.xml")
    assert doc.file_path == Path("tests/resources/incomplete.xml")
    assert doc.root.tag is not None
    assert doc.root.tag == "book"


def test_incomplete_document_empty_paragraphs():
    """Test finding empty paragraphs in the incomplete document."""
    doc = HNPXDocument("tests/resources/incomplete.xml")

    # Find all paragraphs
    paragraphs = doc.root.xpath("//paragraph[@id]")
    assert len(paragraphs) > 0

    # Check for paragraphs with summaries but no text content
    empty_paragraphs = []
    for paragraph in paragraphs:
        text = doc.get_element_text(paragraph)
        summary = doc.get_element_summary(paragraph)

        # If there's a summary but no text, it's an incomplete paragraph
        if summary and not text.strip():
            empty_paragraphs.append(paragraph)

    # The incomplete.xml should have some empty paragraphs
    assert len(empty_paragraphs) > 0

    # Verify they have summaries but no text
    for para in empty_paragraphs:
        assert doc.get_element_summary(para) is not None
        assert doc.get_element_summary(para).strip() != ""
        assert doc.get_element_text(para).strip() == ""


def test_incomplete_document_statistics():
    """Test document statistics with incomplete content."""
    doc = HNPXDocument("tests/resources/incomplete.xml")
    stats = doc.get_document_stats()

    assert isinstance(stats, dict)
    assert "total_elements" in stats
    assert "total_paragraphs" in stats
    assert "total_words" in stats
    assert "max_depth" in stats
    assert "pov_characters" in stats
    assert "narrative_modes" in stats

    # The incomplete document should have fewer words than the complete one
    # since some paragraphs have no text content
    assert stats["total_words"] >= 0

    # Should still have the correct number of paragraphs
    assert stats["total_paragraphs"] > 0


def test_incomplete_document_export():
    """Test exporting incomplete document to plain text format."""
    from mcp_hnpx.server import export_plain_text

    doc = HNPXDocument("tests/resources/incomplete.xml")

    # Test plain text export
    plain_text = export_plain_text(doc, include_summaries=True)
    assert isinstance(plain_text, str)
    assert len(plain_text) > 0

    # Export should include summaries even when text is missing
    assert "Summary:" in plain_text or "BOOK:" in plain_text


def test_incomplete_document_validation():
    """Test validation of incomplete document."""
    doc = HNPXDocument("tests/resources/incomplete.xml")
    is_valid, errors = doc.validate()

    # The document should be valid even with empty paragraphs
    # (assuming the schema allows empty text content)
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)


def test_incomplete_document_search():
    """Test search functionality with incomplete document."""
    doc = HNPXDocument("tests/resources/incomplete.xml")

    # Search for elements with specific summary content
    results = doc.search_elements(summary_contains="Boogiepop")
    assert isinstance(results, list)

    # Should find elements even if they have no text content
    for result in results:
        assert result.tag is not None
        summary = doc.get_element_summary(result)
        assert summary is not None
        assert "boogiepop" in summary.lower()

    # Search for elements with text content (should find fewer results)
    text_results = doc.search_elements(text_contains="Boogiepop")
    assert isinstance(text_results, list)

    # The incomplete document might have fewer text matches than summary matches
    # since some paragraphs lack text content


def test_mcp_server_with_incomplete_document():
    """Test MCP server functionality with incomplete document."""
    from mcp_hnpx.server import get_node, get_empty_containers

    # Test get_node with a paragraph from incomplete document
    doc = HNPXDocument("tests/resources/incomplete.xml")
    paragraphs = doc.root.xpath("//paragraph[@id]")
    assert len(paragraphs) > 0

    paragraph_id = paragraphs[0].get("id")
    result = get_node.fn("tests/resources/incomplete.xml", paragraph_id)
    assert result is not None
    assert isinstance(result, str)

    import json

    parsed_result = json.loads(result)
    assert "id" in parsed_result
    assert "tag" in parsed_result
    assert "summary" in parsed_result
    assert "text" in parsed_result  # Should be present but might be empty

    # Test get_empty_containers
    empty_result = get_empty_containers.fn("tests/resources/incomplete.xml", 5)
    assert empty_result is not None
    assert isinstance(empty_result, str)

    parsed_empty = json.loads(empty_result)
    assert isinstance(parsed_empty, list)

    # Note: search_nodes was removed in redesign
    # AI agents should use get_node and render_node for navigation instead


def test_mcp_server_create_document():
    """Test MCP server create_document functionality."""
    from mcp_hnpx.server import create_document
    import tempfile
    import os

    # Create a temporary file path for the new document
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test_new_document.xml")

        # Test creating a new document with default title
        result = create_document.fn(test_file)
        assert result is not None
        assert isinstance(result, str)
        assert "Successfully created" in result
        assert "test_new_document.xml" in result
        assert "Untitled Book" in result

        # Verify the file was created
        assert os.path.exists(test_file)

        # Load and verify the document structure
        doc = HNPXDocument(test_file)
        assert doc.root.tag == "book"
        assert doc.get_element_summary(doc.root) == "Book: Untitled Book"

        # Check for the expected hierarchy
        chapters = doc.root.xpath("chapter")
        assert len(chapters) == 1
        chapter = chapters[0]
        assert chapter.get("title") == "Chapter 1"
        assert doc.get_element_summary(chapter) == "Chapter 1"

        sequences = chapter.xpath("sequence")
        assert len(sequences) == 1
        sequence = sequences[0]
        assert sequence.get("loc") == "Unknown"
        assert doc.get_element_summary(sequence) == "Opening scene"

        beats = sequence.xpath("beat")
        assert len(beats) == 1
        beat = beats[0]
        assert doc.get_element_summary(beat) == "Opening beat"

        paragraphs = beat.xpath("paragraph")
        assert len(paragraphs) == 1
        paragraph = paragraphs[0]
        assert paragraph.get("mode") == "narration"
        assert doc.get_element_summary(paragraph) == "Opening paragraph"
        assert doc.get_element_text(paragraph) == "Begin your story here..."

        # Test creating a document with a custom title
        test_file2 = os.path.join(temp_dir, "test_custom_title.xml")
        result2 = create_document.fn(test_file2, "My Custom Story")
        assert "My Custom Story" in result2

        # Verify the custom title was used
        doc2 = HNPXDocument(test_file2)
        assert doc2.get_element_summary(doc2.root) == "Book: My Custom Story"


def test_mcp_server_create_document_nested_directory():
    """Test creating a document in a nested directory."""
    from mcp_hnpx.server import create_document
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a nested path that doesn't exist
        nested_dir = os.path.join(temp_dir, "nested", "path")
        test_file = os.path.join(nested_dir, "test_nested.xml")

        # The function should create the directory structure
        result = create_document.fn(test_file, "Nested Test")
        assert "Successfully created" in result

        # Verify the file was created in the nested directory
        assert os.path.exists(test_file)

        # Verify the document structure
        doc = HNPXDocument(test_file)
        assert doc.root.tag == "book"
        assert doc.get_element_summary(doc.root) == "Book: Nested Test"


# ===== TESTS FOR NEW TOOLS =====


def test_mcp_server_create_chapter():
    """Test MCP server create_chapter functionality."""
    import json
    from mcp_hnpx.server import create_chapter, create_document
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a basic document
    create_document.fn(test_file, "Test Book")

    # Get book ID
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    # Test creating a chapter
    result = create_chapter.fn(
        test_file, book_id, "New Chapter", "A new chapter summary"
    )
    parsed = json.loads(result)

    assert parsed["success"] is True
    assert "new_ids" in parsed
    assert len(parsed["new_ids"]) == 1
    assert "validation" in parsed
    assert parsed["validation"]["valid"] is True

    # Verify chapter was created
    new_chapter_id = parsed["new_ids"][0]
    chapter = doc.get_element_by_id(new_chapter_id)
    assert chapter is not None
    assert chapter.tag == "chapter"
    assert chapter.get("title") == "New Chapter"

    os.unlink(test_file)


def test_mcp_server_create_sequence():
    """Test MCP server create_sequence functionality."""
    import json
    from mcp_hnpx.server import create_sequence, create_document, create_chapter
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a basic document with a chapter
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    # Create a chapter first
    chapter_result = create_chapter.fn(test_file, book_id, "Chapter 1", "First chapter")
    chapter_parsed = json.loads(chapter_result)
    chapter_id = chapter_parsed["new_ids"][0]

    # Test creating a sequence
    result = create_sequence.fn(
        test_file, chapter_id, "Forest", "In dark forest", time="night"
    )
    parsed = json.loads(result)

    assert parsed["success"] is True
    assert "new_ids" in parsed
    assert len(parsed["new_ids"]) == 1

    # Verify sequence was created
    new_sequence_id = parsed["new_ids"][0]
    sequence = doc.get_element_by_id(new_sequence_id)
    assert sequence is not None
    assert sequence.tag == "sequence"
    assert sequence.get("loc") == "Forest"
    assert sequence.get("time") == "night"

    os.unlink(test_file)


def test_mcp_server_create_beat():
    """Test MCP server create_beat functionality."""
    import json
    from mcp_hnpx.server import (
        create_beat,
        create_document,
        create_chapter,
        create_sequence,
    )
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a basic document with chapter and sequence
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    chapter_result = create_chapter.fn(test_file, book_id, "Chapter 1", "First chapter")
    chapter_parsed = json.loads(chapter_result)
    chapter_id = chapter_parsed["new_ids"][0]

    sequence_result = create_sequence.fn(
        test_file, chapter_id, "Forest", "In the dark forest"
    )
    sequence_parsed = json.loads(sequence_result)
    sequence_id = sequence_parsed["new_ids"][0]

    # Test creating a beat
    result = create_beat.fn(test_file, sequence_id, "The discovery")
    parsed = json.loads(result)

    assert parsed["success"] is True
    assert "new_ids" in parsed
    assert len(parsed["new_ids"]) == 1

    # Verify beat was created
    new_beat_id = parsed["new_ids"][0]
    beat = doc.get_element_by_id(new_beat_id)
    assert beat is not None
    assert beat.tag == "beat"

    os.unlink(test_file)


def test_mcp_server_create_paragraph():
    """Test MCP server create_paragraph functionality."""
    import json
    from mcp_hnpx.server import (
        create_paragraph,
        create_document,
        create_chapter,
        create_sequence,
        create_beat,
    )
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a basic document with full hierarchy
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    chapter_result = create_chapter.fn(test_file, book_id, "Chapter 1", "First chapter")
    chapter_parsed = json.loads(chapter_result)
    chapter_id = chapter_parsed["new_ids"][0]

    sequence_result = create_sequence.fn(
        test_file, chapter_id, "Forest", "In the dark forest"
    )
    sequence_parsed = json.loads(sequence_result)
    sequence_id = sequence_parsed["new_ids"][0]

    beat_result = create_beat.fn(test_file, sequence_id, "The discovery")
    beat_parsed = json.loads(beat_result)
    beat_id = beat_parsed["new_ids"][0]

    # Test creating a paragraph
    result = create_paragraph.fn(
        test_file,
        beat_id,
        "Character speaks",
        "Hello world!",
        mode="dialogue",
        char="hero",
    )
    parsed = json.loads(result)

    assert parsed["success"] is True
    assert "new_ids" in parsed
    assert len(parsed["new_ids"]) == 1

    # Verify paragraph was created
    new_paragraph_id = parsed["new_ids"][0]
    paragraph = doc.get_element_by_id(new_paragraph_id)
    assert paragraph is not None
    assert paragraph.tag == "paragraph"
    assert paragraph.get("mode") == "dialogue"
    assert paragraph.get("char") == "hero"
    assert paragraph.text == "Hello world!"

    os.unlink(test_file)


def test_mcp_server_get_node_path():
    """Test MCP server get_node_path functionality."""
    import json
    from mcp_hnpx.server import (
        get_node_path,
        create_document,
        create_chapter,
        create_sequence,
        create_beat,
        create_paragraph,
    )
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a document with nested structure
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    chapter_result = create_chapter.fn(test_file, book_id, "Chapter 1", "First chapter")
    chapter_parsed = json.loads(chapter_result)
    chapter_id = chapter_parsed["new_ids"][0]

    sequence_result = create_sequence.fn(
        test_file, chapter_id, "Forest", "In the dark forest"
    )
    sequence_parsed = json.loads(sequence_result)
    sequence_id = sequence_parsed["new_ids"][0]

    beat_result = create_beat.fn(test_file, sequence_id, "The discovery")
    beat_parsed = json.loads(beat_result)
    beat_id = beat_parsed["new_ids"][0]

    paragraph_result = create_paragraph.fn(
        test_file, beat_id, "Character speaks", "Hello world!"
    )
    paragraph_parsed = json.loads(paragraph_result)
    paragraph_id = paragraph_parsed["new_ids"][0]

    # Test getting node path
    result = get_node_path.fn(test_file, paragraph_id)
    parsed = json.loads(result)

    assert parsed["success"] is True
    assert "path" in parsed
    assert len(parsed["path"]) == 5  # book -> chapter -> sequence -> beat -> paragraph
    assert parsed["path"][0] == f"book[{book_id}]"
    assert parsed["path"][1] == f"chapter[{chapter_id}]"
    assert parsed["path"][2] == f"sequence[{sequence_id}]"
    assert parsed["path"][3] == f"beat[{beat_id}]"
    assert parsed["path"][4] == f"paragraph[{paragraph_id}]"

    os.unlink(test_file)


def test_mcp_server_get_direct_children():
    """Test MCP server get_direct_children functionality."""
    import json
    from mcp_hnpx.server import get_direct_children, create_document, create_chapter
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a document with multiple chapters
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    # Create multiple chapters
    chapter1_result = create_chapter.fn(
        test_file, book_id, "Chapter 1", "First chapter"
    )
    chapter2_result = create_chapter.fn(
        test_file, book_id, "Chapter 2", "Second chapter"
    )

    # Test getting direct children of book
    result = get_direct_children.fn(test_file, book_id)
    parsed = json.loads(result)

    assert isinstance(parsed, list)
    assert len(parsed) == 3  # Original chapter + 2 new ones

    # Check that all children are chapters
    for child in parsed:
        assert child["tag"] == "chapter"
        assert "id" in child
        assert "summary" in child
        assert "attributes" in child

    os.unlink(test_file)


def test_mcp_server_render_node():
    """Test MCP server render_node functionality."""
    import json
    from mcp_hnpx.server import (
        render_node,
        create_document,
        create_chapter,
        create_sequence,
        create_beat,
        create_paragraph,
    )
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a document with content
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    chapter_result = create_chapter.fn(test_file, book_id, "Chapter 1", "First chapter")
    chapter_parsed = json.loads(chapter_result)
    chapter_id = chapter_parsed["new_ids"][0]

    sequence_result = create_sequence.fn(
        test_file, chapter_id, "Forest", "In the dark forest"
    )
    sequence_parsed = json.loads(sequence_result)
    sequence_id = sequence_parsed["new_ids"][0]

    beat_result = create_beat.fn(test_file, sequence_id, "The discovery")
    beat_parsed = json.loads(beat_result)
    beat_id = beat_parsed["new_ids"][0]

    paragraph_result = create_paragraph.fn(
        test_file,
        beat_id,
        "Character speaks",
        "Hello world!",
        mode="dialogue",
        char="hero",
    )
    paragraph_parsed = json.loads(paragraph_result)
    paragraph_id = paragraph_parsed["new_ids"][0]

    # Test rendering chapter
    result = render_node.fn(test_file, chapter_id)
    parsed = json.loads(result)

    assert parsed["success"] is True
    assert "rendered" in parsed
    assert "node_id" in parsed
    assert parsed["node_id"] == chapter_id

    rendered = parsed["rendered"]
    assert isinstance(rendered, str)
    assert len(rendered) > 0
    assert f"[{chapter_id}]" in rendered  # ID should be included
    assert "Chapter 1" in rendered  # Title should be included
    assert "First chapter" in rendered  # Summary should be included

    # Test rendering with summaries disabled
    result_no_summaries = render_node.fn(test_file, chapter_id, include_summaries=False)
    parsed_no_summaries = json.loads(result_no_summaries)
    assert parsed_no_summaries["success"] is True
    rendered_no_summaries = parsed_no_summaries["rendered"]
    assert (
        "First chapter" not in rendered_no_summaries
    )  # Summary should not be included

    os.unlink(test_file)


def test_mcp_server_reorder_children():
    """Test MCP server reorder_children functionality."""
    import json
    from mcp_hnpx.server import reorder_children, create_document, create_chapter
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a document with multiple chapters
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    # Create multiple chapters
    chapter1_result = create_chapter.fn(
        test_file, book_id, "Chapter A", "First chapter"
    )
    chapter2_result = create_chapter.fn(
        test_file, book_id, "Chapter B", "Second chapter"
    )
    chapter3_result = create_chapter.fn(
        test_file, book_id, "Chapter C", "Third chapter"
    )

    # Get the chapter IDs
    chapter1_parsed = json.loads(chapter1_result)
    chapter2_parsed = json.loads(chapter2_result)
    chapter3_parsed = json.loads(chapter3_result)

    chapter1_id = chapter1_parsed["new_ids"][0]
    chapter2_id = chapter2_parsed["new_ids"][0]
    chapter3_id = chapter3_parsed["new_ids"][0]

    # Get current order
    children_before = doc.get_children(doc.root)
    original_order = [child.get("id") for child in children_before]

    # Test reordering children
    new_order = [chapter3_id, chapter1_id, chapter2_id]  # Reverse order
    result = reorder_children.fn(test_file, book_id, new_order)
    parsed = json.loads(result)

    assert parsed["success"] is True
    assert "validation" in parsed
    assert parsed["validation"]["valid"] is True

    # Verify new order
    children_after = doc.get_children(doc.root)
    new_order_result = [child.get("id") for child in children_after]
    assert new_order_result == new_order

    os.unlink(test_file)


def test_mcp_server_invalid_parent_child_relationship():
    """Test that creation tools validate parent-child relationships."""
    import json
    from mcp_hnpx.server import create_paragraph, create_document
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a basic document
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    # Try to create a paragraph under a book (should fail)
    result = create_paragraph.fn(
        test_file, book_id, "Invalid paragraph", "This should fail"
    )
    parsed = json.loads(result)

    assert parsed["success"] is False
    assert "error" in parsed
    assert "can only be created under beat elements" in parsed["error"]

    os.unlink(test_file)


def test_mcp_server_attribute_validation():
    """Test that attribute validation works correctly."""
    import json
    from mcp_hnpx.server import edit_node_attributes, create_document, create_chapter
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        test_file = f.name

    # Create a basic document with a chapter
    create_document.fn(test_file, "Test Book")
    doc = HNPXDocument(test_file)
    book_id = doc.root.get("id")

    chapter_result = create_chapter.fn(test_file, book_id, "Chapter 1", "First chapter")
    chapter_parsed = json.loads(chapter_result)
    chapter_id = chapter_parsed["new_ids"][0]

    # Test valid attribute edit
    valid_result = edit_node_attributes.fn(
        test_file, chapter_id, {"title": "Updated Title"}
    )
    valid_parsed = json.loads(valid_result)
    assert valid_parsed["success"] is True

    # Test invalid attribute edit
    invalid_result = edit_node_attributes.fn(
        test_file, chapter_id, {"invalid_attr": "value"}
    )
    invalid_parsed = json.loads(invalid_result)
    assert invalid_parsed["success"] is False
    assert "Invalid attribute" in invalid_parsed["error"]

    # Test invalid enum value
    invalid_enum_result = edit_node_attributes.fn(
        test_file, chapter_id, {"pov": "invalid_pov"}
    )
    invalid_enum_parsed = json.loads(invalid_enum_result)
    assert invalid_enum_parsed["success"] is False

    os.unlink(test_file)
