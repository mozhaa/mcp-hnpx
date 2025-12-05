"""
Pytest configuration and fixtures for HNPX tests.
"""

import os
import tempfile
from pathlib import Path

import pytest
from lxml import etree

from src.mcp_hnpx.hnpx_utils import create_minimal_hnpx_document


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file path."""
    return temp_dir / "test.hnpx"


@pytest.fixture
def sample_hnpx_document():
    """Create a sample HNPX document for testing."""
    root = etree.Element("book", id="b3k9m7")
    summary = etree.SubElement(root, "summary")
    summary.text = (
        "A story about high school students and the mysterious Boogiepop legend."
    )

    chapter = etree.SubElement(
        root, "chapter", id="c8p2q5", title="Boogiepop", pov="suema"
    )
    chapter_summary = etree.SubElement(chapter, "summary")
    chapter_summary.text = "Students discuss the Boogiepop legend, and one claims to see the mysterious figure on the school roof."

    sequence = etree.SubElement(
        chapter,
        "sequence",
        id="s4r7t9",
        loc="School cafeteria",
        time="lunch",
        pov="suema",
    )
    sequence_summary = etree.SubElement(sequence, "summary")
    sequence_summary.text = (
        "Lunch conversation about the Boogiepop legend and rumors about Kirima Nagi."
    )

    beat = etree.SubElement(sequence, "beat", id="b1v6x3")
    beat_summary = etree.SubElement(beat, "summary")
    beat_summary.text = "Introduction to the Boogiepop rumor."

    paragraph = etree.SubElement(beat, "paragraph", id="p9m5k2", mode="narration")
    paragraph_summary = etree.SubElement(paragraph, "summary")
    paragraph_summary.text = (
        "The narrator introduces the Boogiepop rumor spreading among students."
    )
    paragraph.text = "Recently, a strange rumor, or rather, a bit of a ghost story, has been spreading among the girls of the second year classes."

    return root


@pytest.fixture
def sample_hnpx_file(temp_dir, sample_hnpx_document):
    """Create a sample HNPX file for testing."""
    file_path = temp_dir / "sample.hnpx"

    xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml_str += etree.tostring(
        sample_hnpx_document, encoding="utf-8", pretty_print=True
    ).decode("utf-8")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

    return file_path


@pytest.fixture
def minimal_hnpx_document():
    """Create a minimal HNPX document."""
    return create_minimal_hnpx_document()


@pytest.fixture
def minimal_hnpx_file(temp_dir, minimal_hnpx_document):
    """Create a minimal HNPX file for testing."""
    file_path = temp_dir / "minimal.hnpx"

    xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml_str += etree.tostring(
        minimal_hnpx_document, encoding="utf-8", pretty_print=True
    ).decode("utf-8")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

    return file_path


@pytest.fixture
def example_hnpx_file():
    """Path to the example HNPX file."""
    return Path(__file__).parent / "resources" / "example.xml"


@pytest.fixture
def existing_ids():
    """Sample set of existing IDs for testing ID generation."""
    return {"a1b2c3", "d4e5f6", "g7h8i9"}


@pytest.fixture
def valid_node_data():
    """Valid data for creating different node types."""
    return {
        "chapter": {
            "title": "Test Chapter",
            "summary": "A test chapter summary",
            "pov": "test_char",
        },
        "sequence": {
            "location": "Test Location",
            "summary": "A test sequence summary",
            "time": "morning",
            "pov": "test_char",
        },
        "beat": {"summary": "A test beat summary"},
        "paragraph": {
            "summary": "A test paragraph summary",
            "text": "This is test paragraph content.",
            "mode": "narration",
            "char": "test_char",
        },
    }


@pytest.fixture
def invalid_xml_file(temp_dir):
    """Create an invalid XML file for testing error handling."""
    file_path = temp_dir / "invalid.xml"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("<invalid><xml></invalid>")
    return file_path


@pytest.fixture
def non_hnpx_file(temp_dir):
    """Create a valid XML file that's not HNPX for testing error handling."""
    file_path = temp_dir / "non_hnpx.xml"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(
            '<?xml version="1.0" encoding="utf-8"?>\n<root><item>Not HNPX</item></root>'
        )
    return file_path


@pytest.fixture
def mock_file_operations(monkeypatch):
    """Mock file operations for testing."""
    mock_files = {}

    def mock_open(file_path, mode="r", encoding="utf-8"):
        if "w" in mode:

            class MockWriter:
                def __init__(self):
                    self.content = ""

                def write(self, data):
                    self.content = data

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    mock_files[file_path] = self.content

            return MockWriter()
        else:

            class MockReader:
                def __init__(self, path):
                    self.path = path

                def read(self):
                    return mock_files.get(self.path, "")

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return MockReader(file_path)

    def mock_exists(path):
        return path in mock_files or os.path.exists(path)

    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("os.path.exists", mock_exists)

    return mock_files
