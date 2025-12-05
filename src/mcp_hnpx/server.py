"""
Main MCP Server implementation for HNPX document processing.
Uses fastmcp module.
"""

from typing import Any
from fastmcp import FastMCP

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
            return create_document(file_path)

        @self.mcp.tool()
        def get_next_empty_container_tool(file_path: str) -> dict[str, Any]:
            """Finds the next container node in BFS order that needs children."""
            result = get_next_empty_container(file_path)
            if result is None:
                return {
                    "message": "Document is fully expanded",
                    "fully_expanded": True,
                }
            return result

        @self.mcp.tool()
        def get_node_tool(file_path: str, node_id: str) -> str:
            """Retrieves XML representation of a specific node (without descendants)."""
            return get_node(file_path, node_id)

        @self.mcp.tool()
        def get_subtree_tool(file_path: str, node_id: str) -> str:
            """Retrieves XML representation of a node including all its descendants."""
            return get_subtree(file_path, node_id)

        @self.mcp.tool()
        def get_direct_children_tool(file_path: str, node_id: str) -> str:
            """Retrieves immediate child nodes of a specified parent."""
            return get_direct_children(file_path, node_id)

        @self.mcp.tool()
        def get_node_path_tool(file_path: str, node_id: str) -> str:
            """Returns the complete hierarchical path from document root to specified node."""
            return get_node_path(file_path, node_id)

        @self.mcp.tool()
        def get_node_context_tool(file_path: str, node_id: str) -> dict[str, Any]:
            """Gets comprehensive context about a node including parent, children, and siblings."""
            return get_node_context(file_path, node_id)

        @self.mcp.tool()
        def create_chapter_tool(
            file_path: str, parent_id: str, title: str, summary: str, pov: str = None
        ) -> dict[str, Any]:
            """Creates a new chapter element."""
            return create_chapter(file_path, parent_id, title, summary, pov)

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
            return create_sequence(file_path, parent_id, location, summary, time, pov)

        @self.mcp.tool()
        def create_beat_tool(
            file_path: str, parent_id: str, summary: str
        ) -> dict[str, Any]:
            """Creates a new beat element."""
            return create_beat(file_path, parent_id, summary)

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
            return create_paragraph(file_path, parent_id, summary, text, mode, char)

        @self.mcp.tool()
        def edit_node_attributes_tool(
            file_path: str, node_id: str, attributes: dict[str, Any]
        ) -> dict[str, Any]:
            """Modifies attributes of an existing node."""
            return edit_node_attributes(file_path, node_id, attributes)

        @self.mcp.tool()
        def remove_node_tool(file_path: str, node_id: str) -> dict[str, Any]:
            """Permanently removes a node and all its descendants."""
            return remove_node(file_path, node_id)

        @self.mcp.tool()
        def reorder_children_tool(
            file_path: str, parent_id: str, child_ids: list[str]
        ) -> dict[str, Any]:
            """Reorganizes the order of child elements."""
            return reorder_children(file_path, parent_id, child_ids)

        @self.mcp.tool()
        def render_node_tool(file_path: str, node_id: str) -> str:
            """Renders a node and descendants as formatted markdown."""
            return render_node(file_path, node_id)

        @self.mcp.tool()
        def render_document_tool(file_path: str) -> str:
            """Exports entire document to plain text."""
            return render_document(file_path)

        @self.mcp.tool()
        def render_to_markdown_tool(file_path: str) -> str:
            """Renders entire document to formatted markdown with hierarchy."""
            return render_to_markdown(file_path)

    def run(self):
        """Run the MCP server."""
        self.mcp.run()


def run_server():
    """Convenience function to run the server."""
    server = HNPXMCP()
    server.run()


if __name__ == "__main__":
    run_server()
