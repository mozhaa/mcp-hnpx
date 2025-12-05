"""
MCP Server for HNPX document manipulation.
"""

import json
from pathlib import Path
from typing import Any, Dict

from lxml import etree
from fastmcp import FastMCP
from mcp.types import TextContent

from .hnpx import HNPXDocument

# Initialize FastMCP server
mcp = FastMCP("hnpx-server")

# Document cache
documents: Dict[str, HNPXDocument] = {}


def get_document(file_path: str) -> HNPXDocument:
    """Get or load a document."""
    abs_path = str(Path(file_path).resolve())
    if abs_path not in documents:
        documents[abs_path] = HNPXDocument(abs_path)
    return documents[abs_path]

@mcp.tool()
def get_node(file_path: str, node_id: str) -> str:
    """Get a node by ID and read its attributes and summary."""
    doc = get_document(file_path)
    element = doc.get_element_by_id(node_id)

    if element is None:
        return f"Node with ID '{node_id}' not found"

    result = {
        "id": node_id,
        "tag": element.tag,
        "attributes": doc.get_element_attributes(element),
        "summary": doc.get_element_summary(element),
        "text": doc.get_element_text(element)
        if element.tag == "paragraph"
        else None,
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_node_context(file_path: str, node_id: str, include_text: bool = False) -> str:
    """Get context for a node (siblings, parent, parent's siblings)."""
    doc = get_document(file_path)
    element = doc.get_element_by_id(node_id)

    if element is None:
        return f"Node with ID '{node_id}' not found"

    # Get parent
    parent = doc.get_parent(element)
    parent_info = None
    if parent:
        parent_info = {
            "id": parent.get("id"),
            "tag": parent.tag,
            "summary": doc.get_element_summary(parent),
        }

    # Get siblings
    siblings = doc.get_siblings(element)
    sibling_info = []
    for sibling in siblings:
        sibling_data = {
            "id": sibling.get("id"),
            "tag": sibling.tag,
            "summary": doc.get_element_summary(sibling),
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
                "summary": doc.get_element_summary(parent_sibling),
            }
            parent_siblings.append(parent_sibling_data)

    result = {
        "node": {
            "id": node_id,
            "tag": element.tag,
            "summary": doc.get_element_summary(element),
        },
        "parent": parent_info,
        "siblings": sibling_info,
        "parent_siblings": parent_siblings,
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def set_node_children(file_path: str, node_id: str, children_xml: str) -> str:
    """Replace a node's entire children list."""
    doc = get_document(file_path)

    try:
        # Parse the children XML
        parser = etree.XMLParser(remove_blank_text=True)
        children_fragment = etree.fromstring(f"<root>{children_xml}</root>", parser)
        new_children = list(children_fragment)

        success = doc.set_node_children(node_id, new_children)

        if success:
            return f"Successfully updated children for node '{node_id}'"
        else:
            return f"Failed to update children for node '{node_id}'"
    except etree.XMLSyntaxError as e:
        return f"Invalid XML in children: {e}"


@mcp.tool()
def append_node_children(file_path: str, node_id: str, children_xml: str) -> str:
    """Append children to a node's existing children list."""
    doc = get_document(file_path)

    try:
        # Parse the children XML
        parser = etree.XMLParser(remove_blank_text=True)
        children_fragment = etree.fromstring(f"<root>{children_xml}</root>", parser)
        new_children = list(children_fragment)

        success = doc.append_children(node_id, new_children)

        if success:
            return f"Successfully appended children to node '{node_id}'"
        else:
            return f"Failed to append children to node '{node_id}'"
    except etree.XMLSyntaxError as e:
        return f"Invalid XML in children: {e}"


@mcp.tool()
def remove_node(file_path: str, node_id: str) -> str:
    """Remove a node by ID."""
    doc = get_document(file_path)
    success = doc.remove_element(node_id)

    if success:
        return f"Successfully removed node '{node_id}'"
    else:
        return f"Failed to remove node '{node_id}'"


@mcp.tool()
def edit_node_attributes(file_path: str, node_id: str, attributes: Dict[str, str]) -> str:
    """Edit node attributes."""
    doc = get_document(file_path)
    success = doc.edit_element_attributes(node_id, attributes)

    if success:
        return f"Successfully updated attributes for node '{node_id}'"
    else:
        return f"Failed to update attributes for node '{node_id}'"


@mcp.tool()
def get_empty_containers(file_path: str, limit: int = 10) -> str:
    """Get first N container tags that need children populated."""
    doc = get_document(file_path)
    empty_containers = doc.find_empty_containers(limit)

    result = []
    for container in empty_containers:
        container_data = {
            "id": container.get("id"),
            "tag": container.tag,
            "summary": doc.get_element_summary(container),
            "attributes": doc.get_element_attributes(container),
        }
        result.append(container_data)

    return json.dumps(result, indent=2)


@mcp.tool()
def search_nodes(
    file_path: str,
    tag: str = None,
    attributes: Dict[str, str] = None,
    text_contains: str = None,
    summary_contains: str = None
) -> str:
    """Search for nodes matching criteria."""
    doc = get_document(file_path)
    results = doc.search_elements(tag, attributes, text_contains, summary_contains)

    result_data = []
    for element in results:
        element_data = {
            "id": element.get("id"),
            "tag": element.tag,
            "summary": doc.get_element_summary(element),
            "attributes": doc.get_element_attributes(element),
        }
        if element.tag == "paragraph":
            element_data["text"] = doc.get_element_text(element)
        result_data.append(element_data)

    return json.dumps(result_data, indent=2)


@mcp.tool()
def validate_document(file_path: str) -> str:
    """Validate HNPX document against schema."""
    doc = get_document(file_path)
    is_valid, errors = doc.validate()

    result = {"valid": is_valid, "errors": errors}
    return json.dumps(result, indent=2)


@mcp.tool()
def get_document_stats(file_path: str) -> str:
    """Get statistics about the HNPX document."""
    doc = get_document(file_path)
    stats = doc.get_document_stats()
    return json.dumps(stats, indent=2)


@mcp.tool()
def export_document(file_path: str, format: str, include_summaries: bool = True) -> str:
    """Export HNPX document to other formats."""
    doc = get_document(file_path)

    if format == "plain":
        return export_plain_text(doc, include_summaries)
    elif format == "markdown":
        return export_markdown(doc, include_summaries)
    else:
        return f"Unsupported export format: {format}"


def export_plain_text(doc: HNPXDocument, include_summaries: bool) -> str:
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


def export_markdown(doc: HNPXDocument, include_summaries: bool) -> str:
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


@mcp.tool()
def save_document(file_path: str, output_path: str = None) -> str:
    """Save changes to the HNPX document."""
    if output_path is None:
        output_path = file_path

    doc = get_document(file_path)
    success = doc.save(output_path)

    if success:
        return f"Successfully saved document to '{output_path}'"
    else:
        return f"Failed to save document to '{output_path}'"


if __name__ == "__main__":
    mcp.run()
