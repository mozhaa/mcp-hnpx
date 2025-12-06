import random
import string
from pathlib import Path
from typing import Optional
import fastmcp
from lxml import etree

# ============================================================================
# Exception Classes
# ============================================================================


class HNPXError(fastmcp.exceptions.ToolError):
    """Base exception for HNPX errors"""

    pass


class DuplicateIDError(HNPXError):
    def __init__(self, node_id: str):
        super().__init__(f"Node ID '{node_id}' already exists in the document")


class InvalidParentError(HNPXError):
    def __init__(self, parent_type: str, expected_type: str):
        super().__init__(f"Parent must be a {expected_type}, not {parent_type}")


class NodeNotFoundError(HNPXError):
    def __init__(self, node_id: str):
        super().__init__(f"Node with id '{node_id}' not found")


class InvalidAttributeError(HNPXError):
    def __init__(self, attr: str, value: str, reason: str):
        super().__init__(f"Invalid value '{value}' for attribute '{attr}': {reason}")


class MissingAttributeError(HNPXError):
    def __init__(self, attr: str):
        super().__init__(f"Missing required attribute: '{attr}'")


class InvalidHierarchyError(HNPXError):
    def __init__(self, parent_tag: str, child_tag: str):
        super().__init__(f"Cannot add {child_tag} to {parent_tag} - invalid hierarchy")


class ValidationError(HNPXError):
    def __init__(self, errors: list):
        error_messages = "\n".join([str(e) for e in errors])
        super().__init__(f"Schema validation failed:\n{error_messages}")


class InvalidOperationError(HNPXError):
    def __init__(self, operation: str, reason: str):
        super().__init__(f"Cannot {operation}: {reason}")


# ============================================================================
# Helper Functions
# ============================================================================


def load_schema() -> etree.XMLSchema:
    """Load HNPX schema from docs directory"""
    schema_path = Path(__file__).parent.parent.parent / "docs" / "HNPX.xml"
    schema_doc = etree.parse(str(schema_path))
    return etree.XMLSchema(schema_doc)


def parse_document(file_path: str) -> etree.ElementTree:
    """Parse XML file and return ElementTree"""
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(file_path, parser)


def validate_document(tree: etree.ElementTree, schema: etree.XMLSchema) -> None:
    """Validate document against schema, raise ValidationError if invalid"""
    if not schema.validate(tree):
        raise ValidationError(schema.error_log)

    error_log = []
    # Check dialogue paragraphs have char attribute
    for para in tree.xpath('//paragraph[@mode="dialogue"]'):
        if not para.get("char"):
            error_log.append(
                f"Dialogue paragraph {para.get('id')} missing char attribute"
            )

    # Check non-dialogue shouldn't have char
    for para in tree.xpath('//paragraph[@char][not(@mode="dialogue")]'):
        error_log.append(
            f"Paragraph {para.get('id')} has char but mode is {para.get('mode')}"
        )

    if len(error_log) > 0:
        raise ValidationError(error_log)


def save_document(tree: etree.ElementTree, file_path: str) -> None:
    """Save document to file with pretty printing"""
    tree.write(file_path, pretty_print=True, encoding="UTF-8", xml_declaration=True)


def get_all_ids(tree: etree.ElementTree) -> set:
    """Get all ID attributes in document"""
    return set(tree.xpath("//@id"))


def generate_unique_id(existing_ids: set) -> str:
    """Generate unique 6-character ID"""
    chars = string.ascii_lowercase + string.digits
    while True:
        new_id = "".join(random.choice(chars) for _ in range(6))
        if new_id not in existing_ids:
            return new_id


def find_node(tree: etree.ElementTree, node_id: str) -> Optional[etree.Element]:
    """Find node by ID, return None if not found"""
    nodes = tree.xpath(f"//*[@id='{node_id}']")
    return nodes[0] if nodes else None


def get_child_count(node: etree.Element) -> int:
    """Get count of children excluding summary"""
    return len([child for child in node if child.tag != "summary"])


def find_first_empty_container(
    tree: etree.ElementTree, start_node: Optional[etree.Element] = None
) -> Optional[etree.Element]:
    """
    Find first container node with no children (BFS order).
    Container nodes: book, chapter, sequence, beat

    Args:
        tree: The XML document tree
        start_node: If provided, search only within this node's subtree. If None, search from root.
    """
    if start_node is None:
        start_node = tree.getroot()

    queue = [start_node]

    while queue:
        node = queue.pop(0)

        # Check if this is a container node
        if node.tag in ["book", "chapter", "sequence", "beat"]:
            # Check if it has required children (excluding summary)
            if get_child_count(node) == 0:
                return node
        elif node.tag == "paragraph":
            # Check if paragraph has no text content
            if not (node.text or "").strip():
                return node

        # Add children to queue (BFS)
        queue.extend([child for child in node if child.tag != "summary"])

    return None


def render_paragraph(paragraph: etree.Element) -> str:
    """Render a single paragraph based on its mode"""
    text = (paragraph.text or "").strip()
    mode = paragraph.get("mode", "narration")
    char = paragraph.get("char", "")

    # Only render if there's actual text content
    if not text:
        return ""

    if mode == "dialogue" and char:
        return f'{char}: "{text}"'
    elif mode == "internal":
        return f"*{text}*"
    else:
        return text


# ============================================================================
# MCP Server Setup
# ============================================================================

app = fastmcp.FastMCP("hnpx-server", version="1.0.0")

# ============================================================================
# Document Management Tools
# ============================================================================


@app.tool()
def create_document(file_path: str) -> str:
    """Create a new empty HNPX document"""
    # Generate initial book ID
    book_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Create minimal document
    book = etree.Element("book", id=book_id)
    summary = etree.SubElement(book, "summary")
    summary.text = "New book"

    # Create tree and save
    tree = etree.ElementTree(book)
    save_document(tree, file_path)

    return f"Created book with id {book_id} at {file_path}"


# ============================================================================
# Navigation & Discovery Tools
# ============================================================================


@app.tool()
def get_next_empty_container(file_path: str) -> str:
    """Find next container node that needs children (BFS order)"""
    tree = parse_document(file_path)
    empty_node = find_first_empty_container(tree)

    if empty_node is None:
        return "No empty containers found - document is fully expanded"

    # Return node XML (like get_node)
    return etree.tostring(empty_node, encoding="unicode")


@app.tool()
def get_next_empty_container_in_node(file_path: str, node_id: str) -> str:
    """Find next container node that needs children within a specific node's subtree (BFS order)"""
    tree = parse_document(file_path)
    start_node = find_node(tree, node_id)

    if start_node is None:
        raise NodeNotFoundError(node_id)

    empty_node = find_first_empty_container(tree, start_node)

    if empty_node is None:
        return f"No empty containers found within node {node_id}"

    # Return node XML (like get_node)
    return etree.tostring(empty_node, encoding="unicode")


@app.tool()
def get_node(file_path: str, node_id: str) -> str:
    """Retrieve XML representation of a specific node (without descendants)"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Return node with all attributes and summary child
    return etree.tostring(node, encoding="unicode")


# ============================================================================
# Node Inspection Tools
# ============================================================================


@app.tool()
def get_subtree(file_path: str, node_id: str) -> str:
    """Retrieve XML representation of node including all descendants"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    return etree.tostring(node, encoding="unicode")


@app.tool()
def get_direct_children(file_path: str, node_id: str) -> str:
    """Retrieve immediate child nodes of a specified parent"""
    tree = parse_document(file_path)
    parent = find_node(tree, node_id)

    if parent is None:
        raise NodeNotFoundError(node_id)

    # Return concatenated XML of all direct children
    children_xml = []
    for child in parent:
        children_xml.append(etree.tostring(child, encoding="unicode"))

    return "\n".join(children_xml)


@app.tool()
def get_node_path(file_path: str, node_id: str) -> str:
    """Return hierarchical path from document root to specified node"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Collect ancestors
    ancestors = []
    current = node
    while current is not None:
        ancestors.insert(0, current)
        current = current.getparent()

    # Return concatenated XML of all ancestors
    path_xml = []
    for ancestor in ancestors:
        path_xml.append(etree.tostring(ancestor, encoding="unicode"))

    return "\n".join(path_xml)


@app.tool()
def get_document_at_depth(file_path: str, level: str = "full") -> str:
    """Retrieve XML representation of document at specified depth level

    Args:
        file_path: Path to HNPX document
        level: Depth level - one of:
            - "book": Only book element with summary
            - "chapter": Book with chapter children (no deeper)
            - "sequence": Book → chapters → sequences (no deeper)
            - "beat": Book → chapters → sequences → beats (no deeper)
            - "full": Complete document with all levels (default)

    Returns:
        XML string of document at requested depth
    """
    tree = parse_document(file_path)

    # Validate level parameter
    valid_levels = ["book", "chapter", "sequence", "beat", "full"]
    if level not in valid_levels:
        raise InvalidAttributeError(
            "level", level, f"Must be one of: {', '.join(valid_levels)}"
        )

    # Create a copy of the tree to modify
    from copy import deepcopy

    tree_copy = deepcopy(tree)
    root_copy = tree_copy.getroot()

    # Define hierarchy levels
    hierarchy = {"book": 0, "chapter": 1, "sequence": 2, "beat": 3, "paragraph": 4}

    max_depth = hierarchy[level]

    def prune_tree(node: etree.Element, current_depth: int) -> None:
        """Recursively remove nodes beyond max_depth"""
        if current_depth >= max_depth:
            # Remove all children except summary
            children_to_remove = []
            for child in node:
                if child.tag != "summary":
                    children_to_remove.append(child)

            for child in children_to_remove:
                node.remove(child)
        else:
            # Recursively process children
            for child in list(node):
                if child.tag in hierarchy:
                    prune_tree(child, current_depth + 1)

    # Start pruning from the root (book is at depth 0)
    prune_tree(root_copy, 0)

    # Return the pruned tree as XML
    return etree.tostring(root_copy, encoding="unicode", pretty_print=True)


# ============================================================================
# Node Creation Tools
# ============================================================================


def _create_element(
    tree: etree.ElementTree,
    parent_id: str,
    element_tag: str,
    attributes: dict,
    summary_text: str,
) -> str:
    """Generic element creation helper"""
    parent = find_node(tree, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    # Check hierarchy
    valid_hierarchy = {
        "book": ["chapter"],
        "chapter": ["sequence"],
        "sequence": ["beat"],
        "beat": ["paragraph"],
    }

    if (
        parent.tag not in valid_hierarchy
        or element_tag not in valid_hierarchy[parent.tag]
    ):
        raise InvalidHierarchyError(parent.tag, element_tag)

    # Generate unique ID
    existing_ids = get_all_ids(tree)
    new_id = generate_unique_id(existing_ids)
    attributes["id"] = new_id

    # Create element
    element = etree.SubElement(parent, element_tag, **attributes)
    summary = etree.SubElement(element, "summary")
    summary.text = summary_text

    return new_id


@app.tool()
def create_chapter(
    file_path: str, parent_id: str, title: str, summary: str, pov: Optional[str] = None
) -> str:
    """Create a new chapter element"""
    tree = parse_document(file_path)

    attributes = {"title": title}
    if pov:
        attributes["pov"] = pov

    new_id = _create_element(tree, parent_id, "chapter", attributes, summary)

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Created chapter with id {new_id}"


@app.tool()
def create_sequence(
    file_path: str,
    parent_id: str,
    location: str,
    summary: str,
    time: Optional[str] = None,
    pov: Optional[str] = None,
) -> str:
    """Create a new sequence element"""
    tree = parse_document(file_path)

    attributes = {"location": location}
    if time:
        attributes["time"] = time
    if pov:
        attributes["pov"] = pov

    new_id = _create_element(tree, parent_id, "sequence", attributes, summary)

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Created sequence with id {new_id}"


@app.tool()
def create_beat(file_path: str, parent_id: str, summary: str) -> str:
    """Create a new beat element"""
    tree = parse_document(file_path)

    new_id = _create_element(tree, parent_id, "beat", {}, summary)

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Created beat with id {new_id}"


@app.tool()
def create_paragraph(
    file_path: str,
    parent_id: str,
    summary: str,
    text: str,
    mode: str = "narration",
    char: Optional[str] = None,
) -> str:
    """Create a new paragraph element"""
    tree = parse_document(file_path)

    attributes = {"mode": mode}
    if char:
        attributes["char"] = char
    elif mode == "dialogue":
        raise MissingAttributeError("char")

    # Create the paragraph with text content
    parent = find_node(tree, parent_id)
    if parent is None:
        raise NodeNotFoundError(parent_id)

    if parent.tag != "beat":
        raise InvalidParentError(parent.tag, "beat")

    existing_ids = get_all_ids(tree)
    new_id = generate_unique_id(existing_ids)
    attributes["id"] = new_id

    paragraph = etree.SubElement(parent, "paragraph", **attributes)
    summary_elem = etree.SubElement(paragraph, "summary")
    summary_elem.text = summary
    paragraph.text = text

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Created paragraph with id {new_id}"


# ============================================================================
# Node Modification Tools
# ============================================================================


@app.tool()
def edit_node_attributes(file_path: str, node_id: str, attributes: dict) -> str:
    """Modify attributes of an existing node"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Update attributes
    for key, value in attributes.items():
        if key == "id":
            raise InvalidOperationError(
                "edit_node_attributes", "Cannot modify id attribute"
            )

        if value is None or value == "":
            if key in node.attrib:
                del node.attrib[key]
        else:
            node.set(key, value)

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Updated attributes for node {node_id}"


@app.tool()
def remove_node(file_path: str, node_id: str) -> str:
    """Permanently remove a node and all its descendants"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Check if trying to remove root
    if node.tag == "book":
        raise InvalidOperationError("remove_node", "Cannot remove book element")

    # Remove node
    parent = node.getparent()
    parent.remove(node)

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Removed node {node_id} and its descendants"


@app.tool()
def reorder_children(file_path: str, parent_id: str, child_ids: list) -> str:
    """Reorganize the order of child elements"""
    tree = parse_document(file_path)
    parent = find_node(tree, parent_id)

    if parent is None:
        raise NodeNotFoundError(parent_id)

    # Get current children (excluding summary)
    current_children = [child for child in parent if child.tag != "summary"]
    current_ids = [child.get("id") for child in current_children]

    # Validate input
    if set(child_ids) != set(current_ids):
        raise InvalidOperationError(
            "reorder_children", "child_ids must contain all existing child IDs"
        )

    # Create mapping and reorder
    child_map = {child.get("id"): child for child in current_children}

    # Remove all children (except summary)
    for child in current_children:
        parent.remove(child)

    # Add back in new order
    for child_id in child_ids:
        parent.append(child_map[child_id])

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Reordered children of node {parent_id}"


# ============================================================================
# Node Modification Tools
# ============================================================================


@app.tool()
def edit_summary(file_path: str, node_id: str, new_summary: str) -> str:
    """Edit summary text of any element"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    # Find the summary child element
    summary_elem = node.find("summary")
    if summary_elem is None:
        # Create summary if it doesn't exist (shouldn't happen with valid HNPX)
        summary_elem = etree.SubElement(node, "summary")

    # Update the summary text
    summary_elem.text = new_summary

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Updated summary for node {node_id}"


@app.tool()
def edit_paragraph_text(file_path: str, paragraph_id: str, new_text: str) -> str:
    """Edit actual paragraph content"""
    tree = parse_document(file_path)
    paragraph = find_node(tree, paragraph_id)

    if paragraph is None:
        raise NodeNotFoundError(paragraph_id)

    # Verify it's a paragraph element
    if paragraph.tag != "paragraph":
        raise InvalidOperationError(
            "edit_paragraph_text", f"Node {paragraph_id} is not a paragraph"
        )

    # Update the paragraph text content
    paragraph.text = new_text

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Updated text content for paragraph {paragraph_id}"


@app.tool()
def move_node(
    file_path: str, node_id: str, new_parent_id: str, position: Optional[int] = None
) -> str:
    """Move nodes between parents"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)
    new_parent = find_node(tree, new_parent_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    if new_parent is None:
        raise NodeNotFoundError(new_parent_id)

    # Check if trying to move root
    if node.tag == "book":
        raise InvalidOperationError("move_node", "Cannot move book element")

    # Check hierarchy validity
    valid_hierarchy = {
        "book": ["chapter"],
        "chapter": ["sequence"],
        "sequence": ["beat"],
        "beat": ["paragraph"],
    }

    if (
        new_parent.tag not in valid_hierarchy
        or node.tag not in valid_hierarchy[new_parent.tag]
    ):
        raise InvalidHierarchyError(new_parent.tag, node.tag)

    # Check if trying to move a node to its own descendant
    current = new_parent
    while current is not None:
        if current == node:
            raise InvalidOperationError(
                "move_node", "Cannot move a node to its own descendant"
            )
        current = current.getparent()

    # Get old parent
    old_parent = node.getparent()

    # Remove from old parent
    old_parent.remove(node)

    # Add to new parent
    if position is None:
        # Append to the end
        new_parent.append(node)
    else:
        # Insert at specific position
        # Get current children (excluding summary)
        children = [child for child in new_parent if child.tag != "summary"]

        if position < 0 or position > len(children):
            raise InvalidOperationError(
                "move_node", f"Position {position} out of range (0-{len(children)})"
            )

        if position == len(children):
            new_parent.append(node)
        else:
            new_parent.insert(
                position + (1 if new_parent[0].tag == "summary" else 0), node
            )

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Moved node {node_id} to parent {new_parent_id}"


@app.tool()
def remove_node_children(file_path: str, node_id: str) -> str:
    """Remove all children of a node"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    children_count = 0

    # Remove all children except summary
    for child in list(node):
        if child.tag != "summary":
            node.remove(child)
            children_count += 1

    # Validate and save
    schema = load_schema()
    validate_document(tree, schema)
    save_document(tree, file_path)

    return f"Removed {children_count} children from node {node_id}"


# ============================================================================
# Rendering & Export Tools
# ============================================================================


def _render_node_recursive(node: etree.Element, indent: int = 0) -> str:
    """Recursively render node and children as formatted text"""
    lines = []
    indent_str = "  " * indent

    # Get node info
    node_id = node.get("id", "")
    summary = node.findtext("summary", "").strip()

    # Render based on node type
    if node.tag == "book":
        lines.append(f"{indent_str}[{node_id}] Book: {summary}")
    elif node.tag == "chapter":
        title = node.get("title", "")
        pov = node.get("pov", "")
        pov_str = f" (POV: {pov})" if pov else ""
        lines.append(f"{indent_str}[{node_id}] Chapter: {title}{pov_str}")
        lines.append(f"{indent_str}  Summary: {summary}")
    elif node.tag == "sequence":
        location = node.get("location", "")
        time = node.get("time", "")
        pov = node.get("pov", "")
        time_str = f" at {time}" if time else ""
        pov_str = f" (POV: {pov})" if pov else ""
        lines.append(f"{indent_str}[{node_id}] Sequence: {location}{time_str}{pov_str}")
        lines.append(f"{indent_str}  Summary: {summary}")
    elif node.tag == "beat":
        lines.append(f"{indent_str}[{node_id}] Beat: {summary}")
    elif node.tag == "paragraph":
        lines.append(f"{indent_str}[{node_id}] {summary}")
        rendered_text = render_paragraph(node)
        if rendered_text:
            lines.append(f"{indent_str}  {rendered_text}")

    # Recursively render children (excluding summary)
    for child in node:
        if child.tag != "summary":
            lines.append(_render_node_recursive(child, indent + 1))

    return "\n".join(lines)


@app.tool()
def render_node(file_path: str, node_id: str) -> str:
    """Render a node and descendants as formatted text"""
    tree = parse_document(file_path)
    node = find_node(tree, node_id)

    if node is None:
        raise NodeNotFoundError(node_id)

    return _render_node_recursive(node)


@app.tool()
def render_document(file_path: str) -> str:
    """Export entire document to plain text"""
    tree = parse_document(file_path)

    paragraphs = []
    for paragraph in tree.xpath("//paragraph"):
        rendered = render_paragraph(paragraph)
        if rendered:
            paragraphs.append(rendered)

    return "\n\n".join(paragraphs)


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    app.run()
