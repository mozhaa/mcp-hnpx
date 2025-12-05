"""
Core utilities for working with HNPX documents.
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from lxml import etree
from xmlschema import XMLSchema


class HNPXDocument:
    """Represents an HNPX document with parsing and manipulation capabilities."""

    def __init__(self, file_path: str):
        """Initialize HNPX document from file path."""
        self.file_path = Path(file_path)
        self.tree = None
        self.root = None
        self.schema = None
        self._id_cache = {}
        self._load_document()
        self._load_schema()
        self._build_id_cache()

    def _load_document(self):
        """Load and parse the HNPX document."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"HNPX file not found: {self.file_path}")

        try:
            parser = etree.XMLParser(remove_blank_text=True)
            self.tree = etree.parse(str(self.file_path), parser)
            self.root = self.tree.getroot()
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML in HNPX file: {e}")

    def _load_schema(self):
        """Load the HNPX XSD schema for validation."""
        schema_path = Path(__file__).parent.parent.parent / "docs" / "HNPX.xml"
        if schema_path.exists():
            try:
                self.schema = XMLSchema(str(schema_path))
            except Exception as e:
                print(f"Warning: Could not load HNPX schema: {e}")
                self.schema = None
        else:
            print(f"Warning: HNPX schema not found at {schema_path}")
            self.schema = None

    def _build_id_cache(self):
        """Build a cache of all element IDs for fast lookup."""
        self._id_cache = {}
        for element in self.root.xpath("//*[@id]"):
            element_id = element.get("id")
            if element_id:
                self._id_cache[element_id] = element

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the document against the HNPX schema."""
        if not self.schema:
            return True, ["Schema not available for validation"]

        try:
            is_valid = self.schema.is_valid(self.tree)
            errors = []
            if not is_valid:
                errors = [str(error) for error in self.schema.iter_errors(self.tree)]
            return is_valid, errors
        except Exception as e:
            return False, [f"Validation error: {e}"]

    def get_element_by_id(self, element_id: str) -> Optional[etree._Element]:
        """Get an element by its ID attribute."""
        return self._id_cache.get(element_id)

    def get_parent(self, element: etree._Element) -> Optional[etree._Element]:
        """Get the parent of an element."""
        return element.getparent()

    def get_children(self, element: etree._Element) -> List[etree._Element]:
        """Get all child elements of an element, excluding summary tags."""
        return [child for child in element if child.tag != "summary"]

    def get_siblings(self, element: etree._Element) -> List[etree._Element]:
        """Get all siblings of an element (excluding the element itself)."""
        parent = self.get_parent(element)
        if parent is None:
            return []
        return [child for child in parent if child != element]

    def get_element_summary(self, element: etree._Element) -> Optional[str]:
        """Get the summary text of an element."""
        summary_elem = element.find("summary")
        if summary_elem is not None and summary_elem.text:
            return summary_elem.text.strip()
        return None

    def get_element_attributes(self, element: etree._Element) -> Dict[str, str]:
        """Get all attributes of an element."""
        return dict(element.attrib)

    def get_element_text(self, element: etree._Element) -> str:
        """Get the text content of an element (excluding summary)."""
        # For paragraph elements, get text after summary
        if element.tag == "paragraph":
            summary = element.find("summary")
            if summary is not None:
                # Get text after the summary element
                text_parts = []
                for child in element.itertext():
                    if child != summary.text and child.strip():
                        text_parts.append(child.strip())
                return " ".join(text_parts)
        return element.text or ""

    def is_container_element(self, element: etree._Element) -> bool:
        """Check if an element is a container (book, chapter, sequence, beat)."""
        return element.tag in ["book", "chapter", "sequence", "beat"]

    def needs_children(self, element: etree._Element) -> bool:
        """Check if a container element needs children populated."""
        if not self.is_container_element(element):
            return False

        # Check if it has only a summary and no other children
        all_children = list(element)  # Get all children including summary
        non_summary_children = self.get_children(
            element
        )  # Get children excluding summary

        # If it has only a summary and no other children
        if len(all_children) == 1 and all_children[0].tag == "summary":
            return True

        # Check if it has the minimum required children
        required_counts = {
            "book": 2,  # summary + at least 1 chapter
            "chapter": 2,  # summary + at least 1 sequence
            "sequence": 2,  # summary + at least 1 beat
            "beat": 2,  # summary + at least 1 paragraph
        }

        return len(non_summary_children) < required_counts.get(element.tag, 1)

    def find_empty_containers(self, limit: int = 10) -> List[etree._Element]:
        """Find container elements that need children populated."""
        empty_containers = []
        for element in self.root.xpath("//book | //chapter | //sequence | //beat"):
            if self.needs_children(element):
                empty_containers.append(element)
                if len(empty_containers) >= limit:
                    break
        return empty_containers

    def search_elements(
        self,
        tag: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
        text_contains: Optional[str] = None,
        summary_contains: Optional[str] = None,
    ) -> List[etree._Element]:
        """Search for elements matching criteria."""
        xpath_query = "//*"
        if tag:
            xpath_query = f"//{tag}"

        elements = self.root.xpath(xpath_query)
        results = []

        for element in elements:
            # Check attributes
            if attributes:
                match = True
                for attr_name, attr_value in attributes.items():
                    if element.get(attr_name) != attr_value:
                        match = False
                        break
                if not match:
                    continue

            # Check text content
            if text_contains:
                element_text = self.get_element_text(element)
                if text_contains.lower() not in element_text.lower():
                    continue

            # Check summary content
            if summary_contains:
                summary = self.get_element_summary(element)
                if not summary or summary_contains.lower() not in summary.lower():
                    continue

            results.append(element)

        return results

    def remove_element(self, element_id: str) -> bool:
        """Remove an element by ID."""
        element = self.get_element_by_id(element_id)
        if element is None:
            return False

        parent = self.get_parent(element)
        if parent is None:
            return False  # Cannot remove root element

        parent.remove(element)
        self._build_id_cache()  # Rebuild cache after removal
        return True

    def set_element_children(
        self, element_id: str, new_children: List[etree._Element]
    ) -> bool:
        """Replace all children of an element with new children (excluding summary)."""
        element = self.get_element_by_id(element_id)
        if element is None:
            return False

        # Keep the summary element if it exists
        summary = element.find("summary")

        # Clear all existing children
        element.clear()

        # Restore summary if it existed
        if summary is not None:
            element.append(summary)

        # Add new children (excluding any summary elements in the new children)
        for child in new_children:
            if child.tag != "summary":
                element.append(child)

        self._build_id_cache()  # Rebuild cache after modification
        return True

    def append_children(
        self, element_id: str, new_children: List[etree._Element]
    ) -> bool:
        """Append new children to an element (excluding summary)."""
        element = self.get_element_by_id(element_id)
        if element is None:
            return False

        for child in new_children:
            if child.tag != "summary":
                element.append(child)

        self._build_id_cache()  # Rebuild cache after modification
        return True

    def edit_element_attributes(
        self, element_id: str, new_attributes: Dict[str, str]
    ) -> bool:
        """Edit element attributes."""
        element = self.get_element_by_id(element_id)
        if element is None:
            return False

        # Update attributes
        for attr_name, attr_value in new_attributes.items():
            element.set(attr_name, attr_value)

        return True

    def save(self, file_path: Optional[str] = None) -> bool:
        """Save the document to file."""
        save_path = file_path or str(self.file_path)
        try:
            self.tree.write(
                save_path, encoding="utf-8", xml_declaration=True, pretty_print=True
            )
            return True
        except Exception as e:
            print(f"Error saving document: {e}")
            return False

    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the document."""
        stats = {
            "total_elements": len(self.root.xpath("//*")),
            "element_counts": {},
            "total_paragraphs": len(self.root.xpath("//paragraph")),
            "total_words": 0,
            "max_depth": 0,
            "pov_characters": set(),
            "narrative_modes": {"narration": 0, "dialogue": 0, "internal": 0},
        }

        # Count elements by type
        for tag in ["book", "chapter", "sequence", "beat", "paragraph"]:
            stats["element_counts"][tag] = len(self.root.xpath(f"//{tag}"))

        # Count words and narrative modes
        for paragraph in self.root.xpath("//paragraph"):
            text = self.get_element_text(paragraph)
            stats["total_words"] += len(text.split())

            mode = paragraph.get("mode", "narration")
            if mode in stats["narrative_modes"]:
                stats["narrative_modes"][mode] += 1

            char = paragraph.get("char")
            if char:
                stats["pov_characters"].add(char)

        # Get POV from chapters and sequences
        for element in self.root.xpath("//chapter | //sequence"):
            pov = element.get("pov")
            if pov:
                stats["pov_characters"].add(pov)

        stats["pov_characters"] = list(stats["pov_characters"])

        # Calculate max depth
        def get_depth(element, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            for child in element:
                if child.tag in ["chapter", "sequence", "beat", "paragraph"]:
                    get_depth(child, current_depth + 1)

        max_depth = 0
        get_depth(self.root)
        stats["max_depth"] = max_depth

        return stats

    def get_node_path(self, element_id: str) -> List[str]:
        """Get the full path from root to the specified element."""
        element = self.get_element_by_id(element_id)
        if element is None:
            return []

        path = []
        current = element

        while current is not None:
            path.insert(0, f"{current.tag}[{current.get('id')}]")
            current = current.getparent()

        return path

    def render_node_with_ids(
        self, element_id: str, include_summaries: bool = True
    ) -> str:
        """Render a node and its children as markdown with ID prefixes."""
        element = self.get_element_by_id(element_id)
        if element is None:
            return f"Element '{element_id}' not found"

        lines = []

        def render_element(elem, level=0):
            elem_id = elem.get("id", "")
            prefix = "  " * level

            if elem.tag == "book":
                title = self.get_element_summary(elem) or "Untitled Book"
                lines.append(f"{prefix}# [{elem_id}] {title}")

            elif elem.tag == "chapter":
                title = elem.get("title", "Untitled Chapter")
                lines.append(f"{prefix}## [{elem_id}] {title}")
                if include_summaries:
                    summary = self.get_element_summary(elem)
                    if summary:
                        lines.append(f"{prefix}*{summary}*")

            elif elem.tag == "sequence":
                loc = elem.get("loc", "Unknown Location")
                lines.append(f"{prefix}### [{elem_id}] {loc}")
                if include_summaries:
                    summary = self.get_element_summary(elem)
                    if summary:
                        lines.append(f"{prefix}*{summary}*")

            elif elem.tag == "beat":
                summary = self.get_element_summary(elem)
                if summary:
                    lines.append(f"{prefix}**[{elem_id}] {summary}**")

            elif elem.tag == "paragraph":
                text = self.get_element_text(elem)
                mode = elem.get("mode", "narration")
                char = elem.get("char")

                if not text and include_summaries:
                    summary = self.get_element_summary(elem)
                    lines.append(f"{prefix}[{elem_id}] *{summary} (summary only)*")
                elif text:
                    if mode == "dialogue":
                        lines.append(f"{prefix}[{elem_id}] > **{char}**: {text}")
                    elif mode == "internal":
                        lines.append(f"{prefix}[{elem_id}] *{char} (thoughts): {text}*")
                    else:
                        lines.append(f"{prefix}[{elem_id}] {text}")

            # Render children
            for child in self.get_children(elem):
                render_element(child, level + 1)

        render_element(element)
        return "\n".join(lines)

    def validate_attributes(
        self, element_tag: str, attributes: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """Validate attributes against HNPX schema rules."""
        valid_attrs = {
            "book": [],
            "chapter": ["title", "pov"],
            "sequence": ["loc", "time", "pov"],
            "beat": [],
            "paragraph": ["mode", "char"],
        }

        enum_values = {"mode": ["narration", "dialogue", "internal"]}

        errors = []

        # Check if attributes are valid for this element type
        for attr_name, attr_value in attributes.items():
            if attr_name not in valid_attrs.get(element_tag, []):
                errors.append(
                    f"Invalid attribute '{attr_name}' for element '{element_tag}'"
                )
                continue

            # Validate enum values
            if attr_name in enum_values and attr_value not in enum_values[attr_name]:
                errors.append(
                    f"Invalid {attr_name} '{attr_value}'. Must be one of: {', '.join(enum_values[attr_name])}"
                )

        return len(errors) == 0, errors

    def create_child_element(
        self, parent_id: str, child_tag: str, summary: str, **attributes
    ) -> Optional[str]:
        """Create a new child element and return its ID."""
        parent = self.get_element_by_id(parent_id)
        if parent is None:
            return None

        # Validate parent-child relationship
        valid_children = {
            "book": ["chapter"],
            "chapter": ["sequence"],
            "sequence": ["beat"],
            "beat": ["paragraph"],
        }

        if (
            parent.tag not in valid_children
            or child_tag not in valid_children[parent.tag]
        ):
            return None

        # Validate attributes
        is_valid, errors = self.validate_attributes(child_tag, attributes)
        if not is_valid:
            return None

        # Create new element
        new_element = create_element(child_tag, summary, **attributes)
        parent.append(new_element)

        # Rebuild cache and save
        self._build_id_cache()
        self.save()

        return new_element.get("id")

    def reorder_children(self, parent_id: str, child_ids: List[str]) -> bool:
        """Reorder children of an element based on provided ID list."""
        parent = self.get_element_by_id(parent_id)
        if parent is None:
            return False

        # Get current children (excluding summary)
        current_children = self.get_children(parent)

        # Create a mapping of ID to element
        child_map = {child.get("id"): child for child in current_children}

        # Validate all child IDs exist
        for child_id in child_ids:
            if child_id not in child_map:
                return False

        # Clear existing children (keep summary)
        summary = parent.find("summary")
        parent.clear()
        if summary is not None:
            parent.append(summary)

        # Add children in new order
        for child_id in child_ids:
            parent.append(child_map[child_id])

        # Save changes
        self.save()
        return True


def generate_id() -> str:
    """Generate a random 6-character ID for HNPX elements."""
    import random
    import string

    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def create_element(tag: str, summary: str = "", **attributes) -> etree._Element:
    """Create a new HNPX element with the given parameters."""
    # Always generate a random ID
    element_id = generate_id()

    element = etree.Element(tag, id=element_id, **attributes)
    summary_elem = etree.SubElement(element, "summary")
    summary_elem.text = summary
    return element
