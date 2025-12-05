"""
MCP Server for HNPX document manipulation.
"""

import json
from pathlib import Path
from typing import Dict, List

from lxml import etree
from fastmcp import FastMCP

from .hnpx import HNPXDocument, generate_id, create_element

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
        "text": doc.get_element_text(element) if element.tag == "paragraph" else None,
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
def remove_node(file_path: str, node_id: str) -> str:
    """Remove a node by ID."""
    doc = get_document(file_path)
    element = doc.get_element_by_id(node_id)
    
    if element is None:
        return json.dumps({
            "success": False,
            "error": f"Node with ID '{node_id}' not found"
        })
    
    # Cannot remove root element
    if element.tag == "book":
        return json.dumps({
            "success": False,
            "error": "Cannot remove the root book element"
        })
    
    success = doc.remove_element(node_id)
    
    if success:
        # Auto-validate and auto-save
        is_valid, errors = doc.validate()
        doc.save()
        
        return json.dumps({
            "success": True,
            "validation": {"valid": is_valid, "errors": errors},
            "message": f"Successfully removed node '{node_id}'"
        })
    else:
        return json.dumps({
            "success": False,
            "error": f"Failed to remove node '{node_id}'"
        })


@mcp.tool()
def edit_node_attributes(
    file_path: str, node_id: str, attributes: Dict[str, str]
) -> str:
    """Edit node attributes with validation."""
    doc = get_document(file_path)
    element = doc.get_element_by_id(node_id)
    
    if element is None:
        return json.dumps({
            "success": False,
            "error": f"Node with ID '{node_id}' not found"
        })
    
    # Validate attributes
    is_valid_attrs, attr_errors = doc.validate_attributes(element.tag, attributes)
    
    if not is_valid_attrs:
        return json.dumps({
            "success": False,
            "error": f"Invalid attributes: {'; '.join(attr_errors)}"
        })
    
    # Apply changes
    for attr_name, attr_value in attributes.items():
        element.set(attr_name, attr_value)
    
    # Auto-validate and auto-save
    is_valid, errors = doc.validate()
    doc.save()
    
    return json.dumps({
        "success": True,
        "validation": {"valid": is_valid, "errors": errors},
        "message": f"Successfully updated attributes for node '{node_id}'"
    })


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
def get_document_stats(file_path: str) -> str:
    """Get statistics about the HNPX document."""
    doc = get_document(file_path)
    stats = doc.get_document_stats()
    return json.dumps(stats, indent=2)


@mcp.tool()
def export_document(file_path: str, include_summaries: bool = True) -> str:
    """Export HNPX document to plain text format."""
    doc = get_document(file_path)
    return export_plain_text(doc, include_summaries)


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


@mcp.tool()
def create_document(file_path: str, title: str = "Untitled Book") -> str:
    """Create a new empty HNPX document with basic structure."""
    try:
        # Create the basic HNPX document structure
        book = create_element("book", f"Book: {title}")

        # Create a single chapter with a placeholder title
        chapter = create_element("chapter", "Chapter 1", title="Chapter 1")

        # Create a single sequence with a placeholder location
        sequence = create_element("sequence", "Opening scene", loc="Unknown")

        # Create a single beat with a placeholder summary
        beat = create_element("beat", "Opening beat")

        # Create a single paragraph with placeholder content
        paragraph = create_element("paragraph", "Opening paragraph", mode="narration")
        paragraph.text = "Begin your story here..."

        # Build the document hierarchy
        beat.append(paragraph)
        sequence.append(beat)
        chapter.append(sequence)
        book.append(chapter)

        # Create the XML tree
        tree = etree.ElementTree(book)

        # Ensure the directory exists
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the document
        tree.write(
            str(output_path), encoding="utf-8", xml_declaration=True, pretty_print=True
        )

        # Add to document cache
        abs_path = str(output_path.resolve())
        documents[abs_path] = HNPXDocument(abs_path)

        return f"Successfully created new HNPX document at '{file_path}' with title '{title}'"

    except Exception as e:
        return f"Failed to create HNPX document: {str(e)}"


# ===== NEW CREATION TOOLS =====

@mcp.tool()
def create_chapter(file_path: str, parent_id: str, title: str, summary: str, pov: str = None) -> str:
    """Create a new chapter element."""
    doc = get_document(file_path)
    
    # Validate parent exists and is a book
    parent = doc.get_element_by_id(parent_id)
    if parent is None:
        return json.dumps({
            "success": False,
            "error": f"Parent node with ID '{parent_id}' not found"
        })
    
    if parent.tag != "book":
        return json.dumps({
            "success": False,
            "error": f"Chapters can only be created under book elements, not '{parent.tag}'"
        })
    
    # Create attributes
    attributes = {"title": title}
    if pov:
        attributes["pov"] = pov
    
    # Create the chapter
    new_id = doc.create_child_element(parent_id, "chapter", summary, **attributes)
    
    if new_id:
        # Auto-validate
        is_valid, errors = doc.validate()
        return json.dumps({
            "success": True,
            "validation": {"valid": is_valid, "errors": errors},
            "new_ids": [new_id],
            "message": f"Successfully created chapter '{title}' with ID '{new_id}'"
        })
    else:
        return json.dumps({
            "success": False,
            "error": "Failed to create chapter"
        })


@mcp.tool()
def create_sequence(file_path: str, parent_id: str, location: str, summary: str, time: str = None, pov: str = None) -> str:
    """Create a new sequence element."""
    doc = get_document(file_path)
    
    # Validate parent exists and is a chapter
    parent = doc.get_element_by_id(parent_id)
    if parent is None:
        return json.dumps({
            "success": False,
            "error": f"Parent node with ID '{parent_id}' not found"
        })
    
    if parent.tag != "chapter":
        return json.dumps({
            "success": False,
            "error": f"Sequences can only be created under chapter elements, not '{parent.tag}'"
        })
    
    # Create attributes
    attributes = {"loc": location}
    if time:
        attributes["time"] = time
    if pov:
        attributes["pov"] = pov
    
    # Create the sequence
    new_id = doc.create_child_element(parent_id, "sequence", summary, **attributes)
    
    if new_id:
        # Auto-validate
        is_valid, errors = doc.validate()
        return json.dumps({
            "success": True,
            "validation": {"valid": is_valid, "errors": errors},
            "new_ids": [new_id],
            "message": f"Successfully created sequence at '{location}' with ID '{new_id}'"
        })
    else:
        return json.dumps({
            "success": False,
            "error": "Failed to create sequence"
        })


@mcp.tool()
def create_beat(file_path: str, parent_id: str, summary: str) -> str:
    """Create a new beat element."""
    doc = get_document(file_path)
    
    # Validate parent exists and is a sequence
    parent = doc.get_element_by_id(parent_id)
    if parent is None:
        return json.dumps({
            "success": False,
            "error": f"Parent node with ID '{parent_id}' not found"
        })
    
    if parent.tag != "sequence":
        return json.dumps({
            "success": False,
            "error": f"Beats can only be created under sequence elements, not '{parent.tag}'"
        })
    
    # Create the beat
    new_id = doc.create_child_element(parent_id, "beat", summary)
    
    if new_id:
        # Auto-validate
        is_valid, errors = doc.validate()
        return json.dumps({
            "success": True,
            "validation": {"valid": is_valid, "errors": errors},
            "new_ids": [new_id],
            "message": f"Successfully created beat with ID '{new_id}'"
        })
    else:
        return json.dumps({
            "success": False,
            "error": "Failed to create beat"
        })


@mcp.tool()
def create_paragraph(file_path: str, parent_id: str, summary: str, text: str, mode: str = "narration", char: str = None) -> str:
    """Create a new paragraph element."""
    doc = get_document(file_path)
    
    # Validate parent exists and is a beat
    parent = doc.get_element_by_id(parent_id)
    if parent is None:
        return json.dumps({
            "success": False,
            "error": f"Parent node with ID '{parent_id}' not found"
        })
    
    if parent.tag != "beat":
        return json.dumps({
            "success": False,
            "error": f"Paragraphs can only be created under beat elements, not '{parent.tag}'"
        })
    
    # Create attributes
    attributes = {"mode": mode}
    if char:
        attributes["char"] = char
    
    # Create the paragraph
    new_id = doc.create_child_element(parent_id, "paragraph", summary, **attributes)
    
    if new_id:
        # Set the text content
        paragraph = doc.get_element_by_id(new_id)
        if paragraph is not None:
            paragraph.text = text
            
            # Auto-validate and save
            is_valid, errors = doc.validate()
            doc.save()
            
            return json.dumps({
                "success": True,
                "validation": {"valid": is_valid, "errors": errors},
                "new_ids": [new_id],
                "message": f"Successfully created paragraph with ID '{new_id}'"
            })
    
    return json.dumps({
        "success": False,
        "error": "Failed to create paragraph"
    })


# ===== NEW NAVIGATION TOOLS =====

@mcp.tool()
def get_node_path(file_path: str, node_id: str) -> str:
    """Get the full path from root to the specified node."""
    doc = get_document(file_path)
    path = doc.get_node_path(node_id)
    
    if not path:
        return json.dumps({
            "success": False,
            "error": f"Node with ID '{node_id}' not found"
        })
    
    return json.dumps({
        "success": True,
        "path": path,
        "node_id": node_id
    })


@mcp.tool()
def get_direct_children(file_path: str, node_id: str) -> str:
    """Get immediate children of a node (excluding summary elements)."""
    doc = get_document(file_path)
    element = doc.get_element_by_id(node_id)
    
    if element is None:
        return json.dumps({
            "success": False,
            "error": f"Node with ID '{node_id}' not found"
        })
    
    children = doc.get_children(element)
    result = []
    
    for child in children:
        child_data = {
            "id": child.get("id"),
            "tag": child.tag,
            "summary": doc.get_element_summary(child),
            "attributes": doc.get_element_attributes(child),
        }
        if child.tag == "paragraph":
            child_data["text"] = doc.get_element_text(child)
        result.append(child_data)
    
    return json.dumps(result, indent=2)


@mcp.tool()
def render_node(file_path: str, node_id: str, include_summaries: bool = True) -> str:
    """Render a node and its children as markdown with ID prefixes."""
    doc = get_document(file_path)
    rendered = doc.render_node_with_ids(node_id, include_summaries)
    
    if rendered.startswith(f"Element '{node_id}' not found"):
        return json.dumps({
            "success": False,
            "error": f"Node with ID '{node_id}' not found"
        })
    
    return json.dumps({
        "success": True,
        "rendered": rendered,
        "node_id": node_id
    })


# ===== NEW MANAGEMENT TOOLS =====

@mcp.tool()
def reorder_children(file_path: str, parent_id: str, child_ids: list) -> str:
    """Reorder children of an element based on provided ID list."""
    doc = get_document(file_path)
    
    # Validate parent exists
    parent = doc.get_element_by_id(parent_id)
    if parent is None:
        return json.dumps({
            "success": False,
            "error": f"Parent node with ID '{parent_id}' not found"
        })
    
    # Attempt to reorder
    success = doc.reorder_children(parent_id, child_ids)
    
    if success:
        # Auto-validate
        is_valid, errors = doc.validate()
        return json.dumps({
            "success": True,
            "validation": {"valid": is_valid, "errors": errors},
            "message": f"Successfully reordered children of node '{parent_id}'"
        })
    else:
        return json.dumps({
            "success": False,
            "error": "Failed to reorder children. Check that all child IDs are valid."
        })


if __name__ == "__main__":
    mcp.run()
