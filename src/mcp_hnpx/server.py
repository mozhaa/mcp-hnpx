#!/usr/bin/env python3
"""
MCP Server for HNPX document manipulation.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Prompt,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    TextContent,
    Tool,
)

from lxml import etree
from .hnpx_utils import HNPXDocument, generate_id, create_element


class HNPXMCPServer:
    """MCP Server for HNPX document operations."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("hnpx-server")
        self.documents: Dict[str, HNPXDocument] = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List all available tools."""
            tools = [
                Tool(
                    name="get_node",
                    description="Get a node by ID and read its attributes and summary",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "ID of the node to retrieve"
                            }
                        },
                        "required": ["file_path", "node_id"]
                    }
                ),
                Tool(
                    name="get_node_context",
                    description="Get context for a node (siblings, parent, parent's siblings)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "ID of the node to get context for"
                            },
                            "include_text": {
                                "type": "boolean",
                                "description": "Whether to include full text content",
                                "default": False
                            }
                        },
                        "required": ["file_path", "node_id"]
                    }
                ),
                Tool(
                    name="set_node_children",
                    description="Replace a node's entire children list",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "ID of the node to modify"
                            },
                            "children_xml": {
                                "type": "string",
                                "description": "XML string representing the new children"
                            }
                        },
                        "required": ["file_path", "node_id", "children_xml"]
                    }
                ),
                Tool(
                    name="append_node_children",
                    description="Append children to a node's existing children list",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "ID of the node to modify"
                            },
                            "children_xml": {
                                "type": "string",
                                "description": "XML string representing the children to append"
                            }
                        },
                        "required": ["file_path", "node_id", "children_xml"]
                    }
                ),
                Tool(
                    name="remove_node",
                    description="Remove a node by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "ID of the node to remove"
                            }
                        },
                        "required": ["file_path", "node_id"]
                    }
                ),
                Tool(
                    name="edit_node_attributes",
                    description="Edit node attributes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "ID of the node to edit"
                            },
                            "attributes": {
                                "type": "object",
                                "description": "Dictionary of attributes to set",
                                "additionalProperties": {"type": "string"}
                            }
                        },
                        "required": ["file_path", "node_id", "attributes"]
                    }
                ),
                Tool(
                    name="get_empty_containers",
                    description="Get first N container tags that need children populated",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of containers to return",
                                "default": 10
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="search_nodes",
                    description="Search for nodes matching criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "tag": {
                                "type": "string",
                                "description": "Element tag to search for (optional)"
                            },
                            "attributes": {
                                "type": "object",
                                "description": "Attributes to match (optional)",
                                "additionalProperties": {"type": "string"}
                            },
                            "text_contains": {
                                "type": "string",
                                "description": "Text content to search for (optional)"
                            },
                            "summary_contains": {
                                "type": "string",
                                "description": "Summary content to search for (optional)"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="validate_document",
                    description="Validate HNPX document against schema",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_document_stats",
                    description="Get statistics about the HNPX document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="export_document",
                    description="Export HNPX document to other formats",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "format": {
                                "type": "string",
                                "description": "Export format (plain, markdown)",
                                "enum": ["plain", "markdown"]
                            },
                            "include_summaries": {
                                "type": "boolean",
                                "description": "Whether to include summaries in export",
                                "default": True
                            }
                        },
                        "required": ["file_path", "format"]
                    }
                ),
                Tool(
                    name="save_document",
                    description="Save changes to the HNPX document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the HNPX file"
                            },
                            "output_path": {
                                "type": "string",
                                "description": "Output path (optional, defaults to input path)"
                            }
                        },
                        "required": ["file_path"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "get_node":
                    return await self._get_node(arguments)
                elif name == "get_node_context":
                    return await self._get_node_context(arguments)
                elif name == "set_node_children":
                    return await self._set_node_children(arguments)
                elif name == "append_node_children":
                    return await self._append_node_children(arguments)
                elif name == "remove_node":
                    return await self._remove_node(arguments)
                elif name == "edit_node_attributes":
                    return await self._edit_node_attributes(arguments)
                elif name == "get_empty_containers":
                    return await self._get_empty_containers(arguments)
                elif name == "search_nodes":
                    return await self._search_nodes(arguments)
                elif name == "validate_document":
                    return await self._validate_document(arguments)
                elif name == "get_document_stats":
                    return await self._get_document_stats(arguments)
                elif name == "export_document":
                    return await self._export_document(arguments)
                elif name == "save_document":
                    return await self._save_document(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                        isError=True
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    def _get_document(self, file_path: str) -> HNPXDocument:
        """Get or load a document."""
        abs_path = str(Path(file_path).resolve())
        if abs_path not in self.documents:
            self.documents[abs_path] = HNPXDocument(abs_path)
        return self.documents[abs_path]
    
    async def _get_node(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get a node by ID."""
        file_path = arguments["file_path"]
        node_id = arguments["node_id"]
        
        doc = self._get_document(file_path)
        element = doc.get_element_by_id(node_id)
        
        if element is None:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Node with ID '{node_id}' not found")],
                isError=True
            )
        
        result = {
            "id": node_id,
            "tag": element.tag,
            "attributes": doc.get_element_attributes(element),
            "summary": doc.get_element_summary(element),
            "text": doc.get_element_text(element) if element.tag == "paragraph" else None
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _get_node_context(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get context for a node."""
        file_path = arguments["file_path"]
        node_id = arguments["node_id"]
        include_text = arguments.get("include_text", False)
        
        doc = self._get_document(file_path)
        element = doc.get_element_by_id(node_id)
        
        if element is None:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Node with ID '{node_id}' not found")],
                isError=True
            )
        
        # Get parent
        parent = doc.get_parent(element)
        parent_info = None
        if parent:
            parent_info = {
                "id": parent.get("id"),
                "tag": parent.tag,
                "summary": doc.get_element_summary(parent)
            }
        
        # Get siblings
        siblings = doc.get_siblings(element)
        sibling_info = []
        for sibling in siblings:
            sibling_data = {
                "id": sibling.get("id"),
                "tag": sibling.tag,
                "summary": doc.get_element_summary(sibling)
            }
            if include_text and sibling.tag == "paragraph":
                sibling_data["text"] = doc.get_element_text(sibling)
            sibling_info.append(sibling_data)
        
        # Get parent's siblings
        parent_siblings = []
        if parent:
            for parent_sibling in doc.get_siblings(parent):
                parent_sibling_data = {
                    "id": parent_sibling.get("id"),
                    "tag": parent_sibling.tag,
                    "summary": doc.get_element_summary(parent_sibling)
                }
                parent_siblings.append(parent_sibling_data)
        
        result = {
            "node": {
                "id": node_id,
                "tag": element.tag,
                "summary": doc.get_element_summary(element)
            },
            "parent": parent_info,
            "siblings": sibling_info,
            "parent_siblings": parent_siblings
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _set_node_children(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Replace a node's children list."""
        file_path = arguments["file_path"]
        node_id = arguments["node_id"]
        children_xml = arguments["children_xml"]
        
        doc = self._get_document(file_path)
        
        try:
            # Parse the children XML
            parser = etree.XMLParser(remove_blank_text=True)
            children_fragment = etree.fromstring(f"<root>{children_xml}</root>", parser)
            new_children = list(children_fragment)
            
            success = doc.set_node_children(node_id, new_children)
            
            if success:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Successfully updated children for node '{node_id}'")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Failed to update children for node '{node_id}'")],
                    isError=True
                )
        except etree.XMLSyntaxError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Invalid XML in children: {e}")],
                isError=True
            )
    
    async def _append_node_children(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Append children to a node."""
        file_path = arguments["file_path"]
        node_id = arguments["node_id"]
        children_xml = arguments["children_xml"]
        
        doc = self._get_document(file_path)
        
        try:
            # Parse the children XML
            parser = etree.XMLParser(remove_blank_text=True)
            children_fragment = etree.fromstring(f"<root>{children_xml}</root>", parser)
            new_children = list(children_fragment)
            
            success = doc.append_children(node_id, new_children)
            
            if success:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Successfully appended children to node '{node_id}'")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Failed to append children to node '{node_id}'")],
                    isError=True
                )
        except etree.XMLSyntaxError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Invalid XML in children: {e}")],
                isError=True
            )
    
    async def _remove_node(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Remove a node by ID."""
        file_path = arguments["file_path"]
        node_id = arguments["node_id"]
        
        doc = self._get_document(file_path)
        success = doc.remove_element(node_id)
        
        if success:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Successfully removed node '{node_id}'")]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Failed to remove node '{node_id}'")],
                isError=True
            )
    
    async def _edit_node_attributes(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Edit node attributes."""
        file_path = arguments["file_path"]
        node_id = arguments["node_id"]
        attributes = arguments["attributes"]
        
        doc = self._get_document(file_path)
        success = doc.edit_element_attributes(node_id, attributes)
        
        if success:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Successfully updated attributes for node '{node_id}'")]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Failed to update attributes for node '{node_id}'")],
                isError=True
            )
    
    async def _get_empty_containers(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get empty containers that need children."""
        file_path = arguments["file_path"]
        limit = arguments.get("limit", 10)
        
        doc = self._get_document(file_path)
        empty_containers = doc.find_empty_containers(limit)
        
        result = []
        for container in empty_containers:
            container_data = {
                "id": container.get("id"),
                "tag": container.tag,
                "summary": doc.get_element_summary(container),
                "attributes": doc.get_element_attributes(container)
            }
            result.append(container_data)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _search_nodes(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search for nodes."""
        file_path = arguments["file_path"]
        tag = arguments.get("tag")
        attributes = arguments.get("attributes")
        text_contains = arguments.get("text_contains")
        summary_contains = arguments.get("summary_contains")
        
        doc = self._get_document(file_path)
        results = doc.search_elements(tag, attributes, text_contains, summary_contains)
        
        result_data = []
        for element in results:
            element_data = {
                "id": element.get("id"),
                "tag": element.tag,
                "summary": doc.get_element_summary(element),
                "attributes": doc.get_element_attributes(element)
            }
            if element.tag == "paragraph":
                element_data["text"] = doc.get_element_text(element)
            result_data.append(element_data)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result_data, indent=2))]
        )
    
    async def _validate_document(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Validate document against schema."""
        file_path = arguments["file_path"]
        
        doc = self._get_document(file_path)
        is_valid, errors = doc.validate()
        
        result = {
            "valid": is_valid,
            "errors": errors
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _get_document_stats(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get document statistics."""
        file_path = arguments["file_path"]
        
        doc = self._get_document(file_path)
        stats = doc.get_document_stats()
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(stats, indent=2))]
        )
    
    async def _export_document(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Export document to other formats."""
        file_path = arguments["file_path"]
        format_type = arguments["format"]
        include_summaries = arguments.get("include_summaries", True)
        
        doc = self._get_document(file_path)
        
        if format_type == "plain":
            exported = self._export_plain_text(doc, include_summaries)
        elif format_type == "markdown":
            exported = self._export_markdown(doc, include_summaries)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unsupported export format: {format_type}")],
                isError=True
            )
        
        return CallToolResult(
            content=[TextContent(type="text", text=exported)]
        )
    
    def _export_plain_text(self, doc: HNPXDocument, include_summaries: bool) -> str:
        """Export document as plain text."""
        lines = []
        
        # Add book summary
        if include_summaries:
            book_summary = doc.get_element_summary(doc.root)
            if book_summary:
                lines.append(f"BOOK: {book_summary}")
                lines.append("")
        
        # Process chapters
        for chapter in doc.root.xpath("chapter"):
            if include_summaries:
                chapter_summary = doc.get_element_summary(chapter)
                chapter_title = chapter.get("title", "Untitled Chapter")
                lines.append(f"CHAPTER: {chapter_title}")
                if chapter_summary:
                    lines.append(f"Summary: {chapter_summary}")
                lines.append("")
            
            # Process sequences
            for sequence in chapter.xpath("sequence"):
                if include_summaries:
                    sequence_summary = doc.get_element_summary(sequence)
                    sequence_loc = sequence.get("loc", "Unknown Location")
                    lines.append(f"SEQUENCE: {sequence_loc}")
                    if sequence_summary:
                        lines.append(f"Summary: {sequence_summary}")
                    lines.append("")
                
                # Process beats
                for beat in sequence.xpath("beat"):
                    if include_summaries:
                        beat_summary = doc.get_element_summary(beat)
                        if beat_summary:
                            lines.append(f"Beat: {beat_summary}")
                    
                    # Process paragraphs
                    for paragraph in beat.xpath("paragraph"):
                        text = doc.get_element_text(paragraph)
                        if text:
                            lines.append(text)
                    
                    if include_summaries and beat_summary:
                        lines.append("")
                
                if include_summaries:
                    lines.append("")
            
            if include_summaries:
                lines.append("")
        
        return "\n".join(lines)
    
    def _export_markdown(self, doc: HNPXDocument, include_summaries: bool) -> str:
        """Export document as Markdown."""
        lines = []
        
        # Add book summary
        if include_summaries:
            book_summary = doc.get_element_summary(doc.root)
            if book_summary:
                lines.append(f"# {book_summary}")
                lines.append("")
        
        # Process chapters
        for chapter in doc.root.xpath("chapter"):
            chapter_title = chapter.get("title", "Untitled Chapter")
            lines.append(f"## {chapter_title}")
            
            if include_summaries:
                chapter_summary = doc.get_element_summary(chapter)
                if chapter_summary:
                    lines.append(f"*{chapter_summary}*")
                lines.append("")
            
            # Process sequences
            for sequence in chapter.xpath("sequence"):
                sequence_loc = sequence.get("loc", "Unknown Location")
                lines.append(f"### {sequence_loc}")
                
                if include_summaries:
                    sequence_summary = doc.get_element_summary(sequence)
                    if sequence_summary:
                        lines.append(f"*{sequence_summary}*")
                    lines.append("")
                
                # Process beats
                for beat in sequence.xpath("beat"):
                    if include_summaries:
                        beat_summary = doc.get_element_summary(beat)
                        if beat_summary:
                            lines.append(f"**{beat_summary}**")
                    
                    # Process paragraphs
                    for paragraph in beat.xpath("paragraph"):
                        text = doc.get_element_text(paragraph)
                        mode = paragraph.get("mode", "narration")
                        char = paragraph.get("char")
                        
                        if mode == "dialogue":
                            lines.append(f"> **{char}**: {text}")
                        elif mode == "internal":
                            lines.append(f"*{char} (thoughts): {text}*")
                        else:
                            lines.append(text)
                    
                    if include_summaries and beat_summary:
                        lines.append("")
                
                if include_summaries:
                    lines.append("")
            
            if include_summaries:
                lines.append("")
        
        return "\n".join(lines)
    
    async def _save_document(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Save document to file."""
        file_path = arguments["file_path"]
        output_path = arguments.get("output_path", file_path)
        
        doc = self._get_document(file_path)
        success = doc.save(output_path)
        
        if success:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Successfully saved document to '{output_path}'")]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Failed to save document to '{output_path}'")],
                isError=True
            )


async def main():
    """Main entry point for the MCP server."""
    hnpx_server = HNPXMCPServer()
    
    # Use stdio server
    async with stdio_server() as (read_stream, write_stream):
        await hnpx_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="hnpx-server",
                server_version="0.1.0",
                capabilities=hnpx_server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())