"""
Main MCP Server implementation for HNPX document processing.
Uses fastmcp module.
"""

from typing import Any
from fastmcp import FastMCP

from .errors import create_error_response
from .tools.document import create_document
from .tools.navigation import get_next_empty_container, get_node
from .tools.inspection import (
    get_subtree,
    get_direct_children,
    get_node_path,
    get_node_context,
)
from .tools.creation import (
    create_chapter,
    create_sequence,
    create_beat,
    create_paragraph,
)
from .tools.modification import edit_node_attributes, remove_node, reorder_children
from .tools.rendering import render_node, render_document, render_to_markdown


class HNPXMCP:
    """MCP Server for HNPX document processing."""

    def __init__(self, name: str = "hnpx-mcp-server"):
        self.mcp = FastMCP(name)
        self._setup_tools()

    def _setup_tools(self):
        """Register all MCP tools following the specification."""

        @self.mcp.tool()
        def create_document_tool(file_path: str) -> dict[str, Any]:
            """Creates a new empty HNPX document with a root <book> element."""
            try:
                return create_document(file_path)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def get_next_empty_container_tool(file_path: str) -> dict[str, Any]:
            """Finds the next container node in BFS order that needs children."""
            try:
                result = get_next_empty_container(file_path)
                if result is None:
                    return {
                        "message": "Document is fully expanded",
                        "fully_expanded": True,
                    }
                return result
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def get_node_tool(file_path: str, node_id: str) -> str:
            """Retrieves XML representation of a specific node (without descendants)."""
            try:
                return get_node(file_path, node_id)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def get_subtree_tool(file_path: str, node_id: str) -> str:
            """Retrieves XML representation of a node including all its descendants."""
            try:
                return get_subtree(file_path, node_id)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def get_direct_children_tool(file_path: str, node_id: str) -> str:
            """Retrieves immediate child nodes of a specified parent."""
            try:
                return get_direct_children(file_path, node_id)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def get_node_path_tool(file_path: str, node_id: str) -> str:
            """Returns the complete hierarchical path from document root to specified node."""
            try:
                return get_node_path(file_path, node_id)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def get_node_context_tool(file_path: str, node_id: str) -> dict[str, Any]:
            """Gets comprehensive context about a node including parent, children, and siblings."""
            try:
                return get_node_context(file_path, node_id)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def create_chapter_tool(
            file_path: str, parent_id: str, title: str, summary: str, pov: str = None
        ) -> dict[str, Any]:
            """Creates a new chapter element."""
            try:
                return create_chapter(file_path, parent_id, title, summary, pov)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def create_sequence_tool(
            file_path: str,
            parent_id: str,
            location: str,
            summary: str,
            time: str = None,
            pov: str = None,
        ) -> dict[str, Any]:
            """Creates a new sequence element."""
            try:
                return create_sequence(
                    file_path, parent_id, location, summary, time, pov
                )
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def create_beat_tool(
            file_path: str, parent_id: str, summary: str
        ) -> dict[str, Any]:
            """Creates a new beat element."""
            try:
                return create_beat(file_path, parent_id, summary)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def create_paragraph_tool(
            file_path: str,
            parent_id: str,
            summary: str,
            text: str,
            mode: str = "narration",
            char: str = None,
        ) -> dict[str, Any]:
            """Creates a new paragraph element."""
            try:
                return create_paragraph(file_path, parent_id, summary, text, mode, char)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def edit_node_attributes_tool(
            file_path: str, node_id: str, attributes: dict[str, Any]
        ) -> dict[str, Any]:
            """Modifies attributes of an existing node."""
            try:
                return edit_node_attributes(file_path, node_id, attributes)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def remove_node_tool(file_path: str, node_id: str) -> dict[str, Any]:
            """Permanently removes a node and all its descendants."""
            try:
                return remove_node(file_path, node_id)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def reorder_children_tool(
            file_path: str, parent_id: str, child_ids: list[str]
        ) -> dict[str, Any]:
            """Reorganizes the order of child elements."""
            try:
                return reorder_children(file_path, parent_id, child_ids)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def render_node_tool(file_path: str, node_id: str) -> str:
            """Renders a node and descendants as formatted markdown."""
            try:
                return render_node(file_path, node_id)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def render_document_tool(file_path: str) -> str:
            """Exports entire document to plain text."""
            try:
                return render_document(file_path)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

        @self.mcp.tool()
        def render_to_markdown_tool(file_path: str) -> str:
            """Renders entire document to formatted markdown with hierarchy."""
            try:
                return render_to_markdown(file_path)
            except Exception as e:
                error_code = getattr(e, "code", "UNKNOWN_ERROR")
                return create_error_response(error_code, str(e))

    def run(self):
        """Run the MCP server."""
        self.mcp.run()


def run_server():
    """Convenience function to run the server."""
    server = HNPXMCP()
    server.run()


if __name__ == "__main__":
    run_server()
