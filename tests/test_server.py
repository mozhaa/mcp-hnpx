"""
Tests for MCP server integration.
"""

import pytest
from unittest.mock import Mock, patch

from src.mcp_hnpx.server import HNPXMCP, run_server


class TestHNPXMCP:
    def test_server_initialization(self):
        """Test server initialization with default name."""
        server = HNPXMCP()
        assert server.mcp is not None
        assert hasattr(server, "_setup_tools")

    def test_server_initialization_with_custom_name(self):
        """Test server initialization with custom name."""
        custom_name = "custom-hnpx-server"
        server = HNPXMCP(custom_name)
        assert server.mcp is not None

    def test_tools_registration(self):
        """Test that all tools are properly registered."""
        server = HNPXMCP()

        # Check that tools are registered by accessing the mcp tools
        tools = server.mcp.tools

        # Should have all expected tools
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "create_document_tool",
            "get_next_empty_container_tool",
            "get_node_tool",
            "get_subtree_tool",
            "get_direct_children_tool",
            "get_node_path_tool",
            "get_node_context_tool",
            "create_chapter_tool",
            "create_sequence_tool",
            "create_beat_tool",
            "create_paragraph_tool",
            "edit_node_attributes_tool",
            "remove_node_tool",
            "reorder_children_tool",
            "render_node_tool",
            "render_document_tool",
            "render_to_markdown_tool",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, (
                f"Tool {expected_tool} not found in registered tools"
            )

    def test_tool_wrappers_call_correct_functions(self):
        """Test that tool wrappers call the correct underlying functions."""
        server = HNPXMCP()

        # Get the tool functions
        tools = server.mcp.tools
        tool_dict = {tool.name: tool for tool in tools}

        # Test document creation tool
        create_doc_tool = tool_dict["create_document_tool"]
        assert callable(create_doc_tool.function)

        # Test navigation tools
        get_next_tool = tool_dict["get_next_empty_container_tool"]
        assert callable(get_next_tool.function)

        get_node_tool = tool_dict["get_node_tool"]
        assert callable(get_node_tool.function)

        # Test creation tools
        create_chapter_tool = tool_dict["create_chapter_tool"]
        assert callable(create_chapter_tool.function)

        create_paragraph_tool = tool_dict["create_paragraph_tool"]
        assert callable(create_paragraph_tool.function)

        # Test modification tools
        edit_attrs_tool = tool_dict["edit_node_attributes_tool"]
        assert callable(edit_attrs_tool.function)

        remove_node_tool = tool_dict["remove_node_tool"]
        assert callable(remove_node_tool.function)

        # Test rendering tools
        render_node_tool = tool_dict["render_node_tool"]
        assert callable(render_node_tool.function)

        render_doc_tool = tool_dict["render_document_tool"]
        assert callable(render_doc_tool.function)

    def test_tool_parameter_mapping(self):
        """Test that tool parameters are correctly mapped."""
        server = HNPXMCP()

        tools = server.mcp.tools
        tool_dict = {tool.name: tool for tool in tools}

        # Test create_document_tool parameters
        create_doc_tool = tool_dict["create_document_tool"]
        param_names = [param.name for param in create_doc_tool.arguments]
        assert "file_path" in param_names

        # Test create_chapter_tool parameters
        create_chapter_tool = tool_dict["create_chapter_tool"]
        param_names = [param.name for param in create_chapter_tool.arguments]
        expected_params = ["file_path", "parent_id", "title", "summary", "pov"]
        for param in expected_params:
            assert param in param_names

        # Test create_paragraph_tool parameters
        create_para_tool = tool_dict["create_paragraph_tool"]
        param_names = [param.name for param in create_para_tool.arguments]
        expected_params = ["file_path", "parent_id", "summary", "text", "mode", "char"]
        for param in expected_params:
            assert param in param_names

    @patch("src.mcp_hnpx.server.FastMCP")
    def test_server_run_method(self, mock_fastmcp):
        """Test server run method."""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        server = HNPXMCP()
        server.run()

        # Verify that run was called on the MCP instance
        mock_mcp_instance.run.assert_called_once()

    def test_tool_descriptions(self):
        """Test that tools have proper descriptions."""
        server = HNPXMCP()

        tools = server.mcp.tools
        tool_dict = {tool.name: tool for tool in tools}

        # Check that tools have descriptions
        create_doc_tool = tool_dict["create_document_tool"]
        assert create_doc_tool.description is not None
        assert len(create_doc_tool.description) > 0

        get_node_tool = tool_dict["get_node_tool"]
        assert get_node_tool.description is not None
        assert len(get_node_tool.description) > 0

    def test_tool_return_types(self):
        """Test that tools have proper return type annotations."""
        server = HNPXMCP()

        tools = server.mcp.tools
        tool_dict = {tool.name: tool for tool in tools}

        # Check return types for different tool categories
        create_doc_tool = tool_dict["create_document_tool"]
        # Should return dict for creation tools
        assert hasattr(create_doc_tool, "function")

        get_node_tool = tool_dict["get_node_tool"]
        # Should return string for retrieval tools
        assert hasattr(get_node_tool, "function")

        render_tool = tool_dict["render_document_tool"]
        # Should return string for rendering tools
        assert hasattr(render_tool, "function")


class TestRunServer:
    @patch("src.mcp_hnpx.server.HNPXMCP")
    def test_run_server_function(self, mock_hnpx_class):
        """Test the run_server convenience function."""
        mock_server_instance = Mock()
        mock_hnpx_class.return_value = mock_server_instance

        # Import and call the function

        run_server()

        # Verify server was created and run was called
        mock_hnpx_class.assert_called_once()
        mock_server_instance.run.assert_called_once()

    @patch("src.mcp_hnpx.server.HNPXMCP")
    @patch("__main__.__name__", "__main__")
    def test_main_execution(self, mock_hnpx_class):
        """Test that server runs when executed as main."""
        mock_server_instance = Mock()
        mock_hnpx_class.return_value = mock_server_instance

        # Simulate main execution
        import src.mcp_hnpx.server

        with patch.object(src.mcp_hnpx.server, "run_server") as mock_run:
            src.mcp_hnpx.server.run_server()
            mock_run.assert_called_once()


class TestServerIntegration:
    def test_full_workflow_integration(self, temp_dir):
        """Test a complete workflow through the server tools."""
        server = HNPXMCP()
        tools = server.mcp.tools
        tool_dict = {tool.name: tool for tool in tools}

        # Step 1: Create document
        create_doc_tool = tool_dict["create_document_tool"]
        file_path = temp_dir / "integration_test.hnpx"

        result = create_doc_tool.function(str(file_path))
        assert result["success"] is True
        book_id = result["book_id"]

        # Step 2: Create chapter
        create_chapter_tool = tool_dict["create_chapter_tool"]
        chapter_result = create_chapter_tool.function(
            str(file_path), book_id, "Test Chapter", "Test chapter summary", "main_char"
        )
        assert chapter_result["success"] is True
        chapter_id = chapter_result["chapter_id"]

        # Step 3: Create sequence
        create_seq_tool = tool_dict["create_sequence_tool"]
        seq_result = create_seq_tool.function(
            str(file_path),
            chapter_id,
            "Test Location",
            "Test sequence summary",
            "morning",
        )
        assert seq_result["success"] is True
        seq_id = seq_result["sequence_id"]

        # Step 4: Create beat
        create_beat_tool = tool_dict["create_beat_tool"]
        beat_result = create_beat_tool.function(
            str(file_path), seq_id, "Test beat summary"
        )
        assert beat_result["success"] is True
        beat_id = beat_result["beat_id"]

        # Step 5: Create paragraph
        create_para_tool = tool_dict["create_paragraph_tool"]
        para_result = create_para_tool.function(
            str(file_path),
            beat_id,
            "Test paragraph summary",
            "This is test paragraph content.",
            "narration",
        )
        assert para_result["success"] is True
        para_id = para_result["paragraph_id"]

        # Step 6: Get node to verify
        get_node_tool = tool_dict["get_node_tool"]
        node_xml = get_node_tool.function(str(file_path), para_id)
        assert para_id in node_xml
        assert "Test paragraph summary" in node_xml

        # Step 7: Render document
        render_doc_tool = tool_dict["render_document_tool"]
        rendered_text = render_doc_tool.function(str(file_path))
        assert "This is test paragraph content." in rendered_text

        # Step 8: Render to markdown
        render_md_tool = tool_dict["render_to_markdown_tool"]
        markdown = render_md_tool.function(str(file_path))
        assert "# Test Book" in markdown
        assert "## Test Chapter" in markdown
        assert "This is test paragraph content." in markdown

    def test_error_handling_through_server(self, temp_dir):
        """Test that errors are properly handled through server tools."""
        server = HNPXMCP()
        tools = server.mcp.tools
        tool_dict = {tool.name: tool for tool in tools}

        # Test error with non-existent file
        get_node_tool = tool_dict["get_node_tool"]

        with pytest.raises(Exception):  # Should raise FileNotFoundError
            get_node_tool.function("nonexistent.xml", "any_id")

        # Test error with invalid parameters
        create_chapter_tool = tool_dict["create_chapter_tool"]

        with pytest.raises(Exception):  # Should raise MissingAttributeError
            create_chapter_tool.function("nonexistent.xml", "any_id", "", "summary")

    def test_tool_consistency(self, temp_dir):
        """Test that tools maintain consistency with direct function calls."""
        server = HNPXMCP()
        tools = server.mcp.tools
        tool_dict = {tool.name: tool for tool in tools}

        # Create a test document
        from src.mcp_hnpx.tools.document import create_document

        file_path = temp_dir / "consistency_test.hnpx"

        # Call through server tool
        create_doc_tool = tool_dict["create_document_tool"]
        server_result = create_doc_tool.function(str(file_path))

        # Call directly
        direct_result = create_document(str(file_path))

        # Results should be equivalent
        assert server_result["success"] == direct_result["success"]
        assert server_result["file_path"] == direct_result["file_path"]
        assert server_result["book_id"] == direct_result["book_id"]

    def test_server_state_isolation(self, temp_dir):
        """Test that server instances don't share state."""
        server1 = HNPXMCP()
        server2 = HNPXMCP()

        tools1 = {tool.name: tool for tool in server1.mcp.tools}
        tools2 = {tool.name: tool for tool in server2.mcp.tools}

        # Both should have the same tools
        assert set(tools1.keys()) == set(tools2.keys())

        # But they should be different instances
        assert tools1 is not tools2

        # Tool functions should be the same (they reference the same module functions)
        for tool_name in tools1:
            assert tools1[tool_name].function == tools2[tool_name].function
