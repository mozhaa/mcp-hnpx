"""
Rendering and export tools for HNPX MCP server.
"""

import logging
from lxml import etree
from ..hnpx_utils import parse_xml_file, is_valid_hnpx_document, find_node_by_id
from ..errors import NotHNPXError, NodeNotFoundError

logger = logging.getLogger(__name__)


def _render_paragraph_text(paragraph: etree.Element) -> str:
    """Render a single paragraph's text with proper formatting."""
    mode = paragraph.get("mode", "narration")
    char = paragraph.get("char", "")
    text = paragraph.text or ""

    logger.debug(
        "Rendering paragraph text: mode=%s, char=%s, text_length=%d",
        mode,
        char,
        len(text),
    )

    if mode == "dialogue":
        if text.startswith('"') and text.endswith('"'):
            result = f"{char}: {text}"
        else:
            result = f'{char}: "{text}"'
        logger.debug("Rendered dialogue: %s", result)
        return result
    elif mode == "internal":
        result = f"*{text}*"
        logger.debug("Rendered internal monologue: %s", result)
        return result
    else:
        logger.debug("Rendered narration: %s", text)
        return text


def _format_element(element: etree.Element, indent: int = 0) -> str:
    """Format an element for rendering with proper indentation."""
    indent_str = "  " * indent
    logger.debug("Formatting element: %s at indent level %d", element.tag, indent)

    if element.tag == "book":
        summary = element.findtext("summary", "").strip()
        result = f"{indent_str}[{element.get('id')}] Book: {summary}"
        logger.debug("Formatted book: %s", result)
        return result

    elif element.tag == "chapter":
        title = element.get("title", "")
        pov = element.get("pov", "")
        summary = element.findtext("summary", "").strip()
        pov_str = f" (POV: {pov})" if pov else ""
        result = f"{indent_str}[{element.get('id')}] Chapter: {title}{pov_str}\n{indent_str}  Summary: {summary}"
        logger.debug("Formatted chapter: %s", result)
        return result

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

        result = f"{indent_str}[{element.get('id')}] Sequence: {location_str}\n{indent_str}  Summary: {summary}"
        logger.debug("Formatted sequence: %s", result)
        return result

    elif element.tag == "beat":
        summary = element.findtext("summary", "").strip()
        result = f"{indent_str}[{element.get('id')}] Beat: {summary}"
        logger.debug("Formatted beat: %s", result)
        return result

    elif element.tag == "paragraph":
        summary = element.findtext("summary", "").strip()
        text = _render_paragraph_text(element)
        result = f"{indent_str}[{element.get('id')}] {summary}\n{indent_str}{text}"
        logger.debug("Formatted paragraph: %s", result)
        return result

    logger.debug("Unknown element type: %s", element.tag)
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
    logger.info("Rendering node %s from file: %s", node_id, file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for node rendering: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    node = find_node_by_id(root, node_id)
    if node is None:
        logger.error("Node with ID %s not found in file: %s", node_id, file_path)
        raise NodeNotFoundError(node_id)

    logger.debug("Found node to render: %s with ID: %s", node.tag, node_id)

    result_lines = []
    nodes_processed = 0

    # Use BFS to render hierarchy
    queue = [(node, 0)]

    while queue:
        current_node, level = queue.pop(0)
        nodes_processed += 1

        # Skip summary elements (they're included in parent rendering)
        if current_node.tag == "summary":
            continue

        # Render this node
        formatted_element = _format_element(current_node, level)
        result_lines.append(formatted_element)
        logger.debug("Rendered element at level %d: %s", level, current_node.tag)

        # Add children to queue
        for child in current_node:
            if child.tag != "summary":  # Skip summary elements
                queue.append((child, level + 1))

    result = "\n".join(result_lines)
    logger.info(
        "Node rendering completed: %d nodes processed, output length: %d",
        nodes_processed,
        len(result),
    )
    return result


def render_document(file_path: str) -> str:
    """
    Exports entire document to plain text.

    Args:
        file_path: Path to HNPX XML file

    Returns:
        Full text of written content as continuous prose
    """
    logger.info("Rendering document to plain text: %s", file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for document rendering: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    paragraphs = []
    paragraph_count = 0

    # Collect all paragraphs in order
    for paragraph in root.xpath("//paragraph"):
        text = _render_paragraph_text(paragraph)
        if text:
            paragraphs.append(text)
            paragraph_count += 1
            logger.debug("Added paragraph %d to document render", paragraph_count)

    result = "\n\n".join(paragraphs)
    logger.info(
        "Document rendering completed: %d paragraphs, output length: %d",
        paragraph_count,
        len(result),
    )
    return result


def render_to_markdown(file_path: str) -> str:
    """
    Renders entire document to formatted markdown with hierarchy.

    Args:
        file_path: Path to HNPX XML file

    Returns:
        Markdown formatted document
    """
    logger.info("Rendering document to markdown: %s", file_path)

    root = parse_xml_file(file_path)
    logger.debug("Successfully parsed file for markdown rendering: %s", file_path)

    if not is_valid_hnpx_document(root):
        logger.error("Invalid HNPX document: %s", file_path)
        raise NotHNPXError()

    result_lines = []
    chapter_count = 0
    sequence_count = 0
    beat_count = 0
    paragraph_count = 0

    # Start with book title/summary
    book_summary = root.findtext("summary", "").strip()
    result_lines.append(f"# {book_summary}")
    result_lines.append(f"*Book ID: {root.get('id', '')}*")
    result_lines.append("")
    logger.debug("Added book header and summary")

    # Process each chapter
    for chapter in root.findall("chapter"):
        chapter_count += 1
        chapter_title = chapter.get("title", "")
        chapter_summary = chapter.findtext("summary", "").strip()
        chapter_pov = chapter.get("pov", "")

        result_lines.append(f"## {chapter_title}")
        if chapter_pov:
            result_lines.append(f"*POV: {chapter_pov}*")
        result_lines.append(f"*{chapter_summary}*")
        result_lines.append("")
        logger.debug("Added chapter %d: %s", chapter_count, chapter_title)

        # Process each sequence
        for sequence in chapter.findall("sequence"):
            sequence_count += 1
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
            logger.debug("Added sequence %d: %s", sequence_count, location_str)

            # Process each beat
            for beat in sequence.findall("beat"):
                beat_count += 1
                beat_summary = beat.findtext("summary", "").strip()

                result_lines.append(f"#### {beat_summary}")
                result_lines.append("")
                logger.debug("Added beat %d: %s", beat_count, beat_summary)

                # Process each paragraph
                for paragraph in beat.findall("paragraph"):
                    paragraph_count += 1
                    text = _render_paragraph_text(paragraph)
                    result_lines.append(text)
                    result_lines.append("")
                    logger.debug("Added paragraph %d", paragraph_count)

    result = "\n".join(result_lines)
    logger.info(
        "Markdown rendering completed: %d chapters, %d sequences, %d beats, %d paragraphs, output length: %d",
        chapter_count,
        sequence_count,
        beat_count,
        paragraph_count,
        len(result),
    )
    return result
