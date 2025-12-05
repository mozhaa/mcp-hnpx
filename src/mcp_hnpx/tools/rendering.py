"""
Rendering and export tools for HNPX MCP server.
"""

from lxml import etree
from ..hnpx_utils import parse_xml_file, is_valid_hnpx_document, find_node_by_id
from ..errors import NotHNPXError, NodeNotFoundError


def _render_paragraph_text(paragraph: etree.Element) -> str:
    """Render a single paragraph's text with proper formatting."""
    mode = paragraph.get("mode", "narration")
    char = paragraph.get("char", "")
    text = paragraph.text or ""

    if mode == "dialogue":
        if text.startswith('"') and text.endswith('"'):
            return f"{char}: {text}"
        else:
            return f'{char}: "{text}"'
    elif mode == "internal":
        return f"*{text}*"
    else:
        return text


def _format_element(element: etree.Element, indent: int = 0) -> str:
    """Format an element for rendering with proper indentation."""
    indent_str = "  " * indent

    if element.tag == "book":
        summary = element.findtext("summary", "").strip()
        return f"{indent_str}[{element.get('id')}] Book: {summary}"

    elif element.tag == "chapter":
        title = element.get("title", "")
        pov = element.get("pov", "")
        summary = element.findtext("summary", "").strip()
        pov_str = f" (POV: {pov})" if pov else ""
        return f"{indent_str}[{element.get('id')}] Chapter: {title}{pov_str}\n{indent_str}  Summary: {summary}"

    elif element.tag == "sequence":
        location = element.get("loc", "")
        time = element.get("time", "")
        pov = element.get("pov", "")
        summary = element.findtext("summary", "").strip()

        location_str = f"{location}"
        if time:
            location_str += f" at {time}"
        if pov:
            location_str += f" (POV: {pov})"

        return f"{indent_str}[{element.get('id')}] Sequence: {location_str}\n{indent_str}  Summary: {summary}"

    elif element.tag == "beat":
        summary = element.findtext("summary", "").strip()
        return f"{indent_str}[{element.get('id')}] Beat: {summary}"

    elif element.tag == "paragraph":
        summary = element.findtext("summary", "").strip()
        text = _render_paragraph_text(element)
        return f"{indent_str}[{element.get('id')}] {summary}\n{indent_str}{text}"

    return ""


def render_node(file_path: str, node_id: str) -> str:
    """
    Renders a node and descendants as formatted markdown.

    Args:
        file_path: Path to HNPX XML file
        node_id: ID of node to render

    Returns:
        Formatted markdown string
    """
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        raise NodeNotFoundError(node_id)

    result_lines = []

    # Use BFS to render hierarchy
    queue = [(node, 0)]

    while queue:
        current_node, level = queue.pop(0)

        # Skip summary elements (they're included in parent rendering)
        if current_node.tag == "summary":
            continue

        # Render this node
        result_lines.append(_format_element(current_node, level))

        # Add children to queue
        for child in current_node:
            if child.tag != "summary":  # Skip summary elements
                queue.append((child, level + 1))

    return "\n".join(result_lines)


def render_document(file_path: str) -> str:
    """
    Exports entire document to plain text.

    Args:
        file_path: Path to HNPX XML file

    Returns:
        Full text of written content as continuous prose
    """
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    paragraphs = []

    # Collect all paragraphs in order
    for paragraph in root.xpath("//paragraph"):
        text = _render_paragraph_text(paragraph)
        if text:
            paragraphs.append(text)

    # Join paragraphs with double newlines for readability
    return "\n\n".join(paragraphs)


def render_to_markdown(file_path: str) -> str:
    """
    Renders entire document to formatted markdown with hierarchy.

    Args:
        file_path: Path to HNPX XML file

    Returns:
        Markdown formatted document
    """
    root = parse_xml_file(file_path)

    if not is_valid_hnpx_document(root):
        raise NotHNPXError()

    result_lines = []

    # Start with book title/summary
    book_summary = root.findtext("summary", "").strip()
    result_lines.append(f"# {book_summary}")
    result_lines.append(f"*Book ID: {root.get('id', '')}*")
    result_lines.append("")

    # Process each chapter
    for chapter in root.findall("chapter"):
        chapter_title = chapter.get("title", "")
        chapter_summary = chapter.findtext("summary", "").strip()
        chapter_pov = chapter.get("pov", "")

        result_lines.append(f"## {chapter_title}")
        if chapter_pov:
            result_lines.append(f"*POV: {chapter_pov}*")
        result_lines.append(f"*{chapter_summary}*")
        result_lines.append("")

        # Process each sequence
        for sequence in chapter.findall("sequence"):
            location = sequence.get("loc", "")
            time = sequence.get("time", "")
            sequence_summary = sequence.findtext("summary", "").strip()
            sequence_pov = sequence.get("pov", "")

            location_str = f"**{location}**"
            if time:
                location_str += f" ({time})"
            if sequence_pov and sequence_pov != chapter_pov:
                location_str += f" [POV: {sequence_pov}]"

            result_lines.append(f"### {location_str}")
            result_lines.append(f"*{sequence_summary}*")
            result_lines.append("")

            # Process each beat
            for beat in sequence.findall("beat"):
                beat_summary = beat.findtext("summary", "").strip()

                result_lines.append(f"#### {beat_summary}")
                result_lines.append("")

                # Process each paragraph
                for paragraph in beat.findall("paragraph"):
                    text = _render_paragraph_text(paragraph)
                    result_lines.append(text)
                    result_lines.append("")

    return "\n".join(result_lines)
