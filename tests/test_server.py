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
    # Create a paragraph with explicit ID
    para = create_element(
        "paragraph", "x1y2z3", "Test paragraph summary", mode="narration"
    )
    para.text = "This is test paragraph content."
    assert para.tag == "paragraph"
    assert para.get("id") == "x1y2z3"
    assert para.find("summary").text == "Test paragraph summary"
    assert para.text == "This is test paragraph content."

    # Create a beat with explicit ID
    beat = create_element("beat", "a1b2c3", "Test beat summary")
    beat.append(para)
    assert beat.tag == "beat"
    assert beat.get("id") == "a1b2c3"
    # Beat should have 2 children total: summary and paragraph
    assert len(list(beat)) == 2
    # But get_children should exclude summary, so only 1 child (paragraph)
    doc = HNPXDocument("tests/resources/example.xml")
    assert len(doc.get_children(beat)) == 1

    # Test creating elements with auto-generated IDs
    auto_para = create_element("paragraph", summary="Auto-generated paragraph")
    assert auto_para.tag == "paragraph"
    assert auto_para.get("id") is not None
    assert len(auto_para.get("id")) == 6
    assert auto_para.find("summary").text == "Auto-generated paragraph"

    auto_beat = create_element("beat", summary="Auto-generated beat")
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
    """Test MCP server search_nodes functionality."""
    from mcp_hnpx.server import search_nodes

    # Access the underlying function from the FastMCP tool
    result = search_nodes.fn("tests/resources/example.xml", text_contains="Boogiepop")
    assert result is not None
    assert isinstance(result, str)
    # Should be valid JSON
    import json

    parsed_result = json.loads(result)
    assert isinstance(parsed_result, list)
    for node in parsed_result:
        assert "id" in node
        assert "tag" in node
        assert "summary" in node
