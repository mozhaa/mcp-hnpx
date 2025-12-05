import pytest

from mcp_hnpx.hnpx_utils import HNPXDocument, create_element, generate_id


def test_hnpx_document_loading():
    """Test loading the example document."""
    doc = HNPXDocument("example.xml")
    assert doc.file_path == "example.xml"
    assert doc.root.tag is not None


def test_hnpx_element_by_id():
    """Test getting a node by ID."""
    doc = HNPXDocument("example.xml")
    node = doc.get_element_by_id("b3k9m7")
    assert node is not None
    assert node.tag is not None
    attributes = doc.get_element_attributes(node)
    assert isinstance(attributes, dict)
    summary = doc.get_element_summary(node)
    assert isinstance(summary, str)


def test_hnpx_element_context():
    """Test getting element context (parent and siblings)."""
    doc = HNPXDocument("example.xml")
    node = doc.get_element_by_id("p9m5k2")
    if node:
        parent = doc.get_parent(node)
        assert parent is not None
        assert parent.tag is not None

        siblings = doc.get_siblings(node)
        assert isinstance(siblings, list)
        for sibling in siblings[:3]:
            assert sibling.tag is not None
            assert sibling.get("id") is not None
            assert isinstance(doc.get_element_summary(sibling), str)


def test_hnpx_empty_containers():
    """Test finding empty containers."""
    doc = HNPXDocument("example.xml")
    empty_containers = doc.find_empty_containers(5)
    assert isinstance(empty_containers, list)
    for container in empty_containers:
        assert container.tag is not None
        assert container.get("id") is not None
        assert isinstance(doc.get_element_summary(container), str)


def test_hnpx_search():
    """Test search functionality."""
    doc = HNPXDocument("example.xml")
    results = doc.search_elements(text_contains="Boogiepop")
    assert isinstance(results, list)
    for result in results[:3]:
        assert result.tag is not None
        assert result.get("id") is not None
        assert isinstance(doc.get_element_summary(result), str)


def test_hnpx_validation():
    """Test document validation."""
    doc = HNPXDocument("example.xml")
    is_valid, errors = doc.validate()
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)
    if errors:
        for error in errors[:3]:
            assert isinstance(error, str)


def test_hnpx_statistics():
    """Test document statistics."""
    doc = HNPXDocument("example.xml")
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
        assert len(id_val) > 0


def test_element_creation():
    """Test element creation."""
    # Create a paragraph
    para = create_element(
        "paragraph", "x1y2z3", "Test paragraph summary", mode="narration"
    )
    para.text = "This is test paragraph content."
    assert para.tag == "paragraph"
    assert para.get("id") == "x1y2z3"
    assert para.find("summary").text == "Test paragraph summary"
    assert para.text == "This is test paragraph content."

    # Create a beat
    beat = create_element("beat", "a1b2c3", "Test beat summary")
    beat.append(para)
    assert beat.tag == "beat"
    assert beat.get("id") == "a1b2c3"
    assert len(list(beat)) == 1


@pytest.mark.asyncio
async def test_mcp_server_get_node():
    """Test MCP server get_node functionality."""
    from mcp_hnpx.server import HNPXMCPServer

    server = HNPXMCPServer()
    result = await server._get_node({"file_path": "example.xml", "node_id": "b3k9m7"})
    assert result is not None
    assert len(result.content) > 0
    assert isinstance(result.content[0].text, str)


@pytest.mark.asyncio
async def test_mcp_server_get_empty_containers():
    """Test MCP server get_empty_containers functionality."""
    from mcp_hnpx.server import HNPXMCPServer

    server = HNPXMCPServer()
    result = await server._get_empty_containers(
        {"file_path": "example.xml", "limit": 3}
    )
    assert result is not None
    assert len(result.content) > 0
    assert isinstance(result.content[0].text, str)


@pytest.mark.asyncio
async def test_mcp_server_search_nodes():
    """Test MCP server search_nodes functionality."""
    from mcp_hnpx.server import HNPXMCPServer

    server = HNPXMCPServer()
    result = await server._search_nodes(
        {"file_path": "example.xml", "text_contains": "Boogiepop"}
    )
    assert result is not None
    assert len(result.content) > 0
    assert isinstance(result.content[0].text, str)
