"""
Tests for HNPX document validation.
"""

from unittest.mock import patch

import pytest

from src.mcp_hnpx.validation import validate_hnpx_with_schema, validate_hnpx_basic
from src.mcp_hnpx.errors import FileNotFoundError


class TestValidateHNPXWithSchema:
    def test_validate_valid_document(self, sample_hnpx_file):
        """Test validating a valid HNPX document with schema."""
        # Since we don't have an actual schema file, this will likely fail
        # but we can test the error handling
        errors = validate_hnpx_with_schema(str(sample_hnpx_file))
        # Should return errors because schema file doesn't exist
        assert isinstance(errors, list)
        assert len(errors) > 0
        assert "Schema file not found" in errors[0]

    def test_validate_nonexistent_file(self):
        """Test validating a non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_hnpx_with_schema("nonexistent.xml")

    def test_validate_invalid_xml(self, invalid_xml_file):
        """Test validating an invalid XML file."""
        errors = validate_hnpx_with_schema(str(invalid_xml_file))
        assert isinstance(errors, list)
        assert len(errors) > 0

    @patch("src.mcp_hnpx.validation.etree.parse")
    @patch("src.mcp_hnpx.validation.os.path.exists")
    def test_validate_with_mock_schema(self, mock_exists, mock_parse, sample_hnpx_file):
        """Test validation with mocked schema."""
        # Mock schema file exists
        mock_exists.return_value = True

        # Mock schema validation to pass
        mock_xml_schema = mock_parse.return_value.XMLSchema.return_value
        mock_xml_schema.validate.return_value = True
        mock_xml_schema.error_log = []

        errors = validate_hnpx_with_schema(str(sample_hnpx_file))
        assert errors == []

    @patch("src.mcp_hnpx.validation.etree.parse")
    @patch("src.mcp_hnpx.validation.os.path.exists")
    def test_validate_with_schema_errors(
        self, mock_exists, mock_parse, sample_hnpx_file
    ):
        """Test validation with schema errors."""
        # Mock schema file exists
        mock_exists.return_value = True

        # Mock schema validation to fail
        mock_xml_schema = mock_parse.return_value.XMLSchema.return_value
        mock_xml_schema.validate.return_value = False

        # Mock error log
        mock_error = mock_parse.return_value.error_log.__iter__.return_value.__next__.return_value
        mock_error.line = 5
        mock_error.message = "Element 'invalid': This element is not expected"
        mock_xml_schema.error_log = [mock_error]

        errors = validate_hnpx_with_schema(str(sample_hnpx_file))
        assert len(errors) == 1
        assert "Line 5" in errors[0]
        assert "This element is not expected" in errors[0]


class TestValidateHNPXBasic:
    def test_validate_valid_document(self, sample_hnpx_file):
        """Test basic validation of a valid HNPX document."""
        errors = validate_hnpx_basic(str(sample_hnpx_file))
        assert errors == []

    def test_validate_minimal_document(self, minimal_hnpx_file):
        """Test basic validation of a minimal HNPX document."""
        errors = validate_hnpx_basic(str(minimal_hnpx_file))
        assert errors == []

    def test_validate_example_document(self, example_hnpx_file):
        """Test basic validation of the example HNPX document."""
        errors = validate_hnpx_basic(str(example_hnpx_file))
        assert errors == []

    def test_validate_nonexistent_file(self):
        """Test basic validation of a non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_hnpx_basic("nonexistent.xml")

    def test_validate_invalid_xml(self, invalid_xml_file):
        """Test basic validation of an invalid XML file."""
        errors = validate_hnpx_basic(str(invalid_xml_file))
        assert isinstance(errors, list)
        assert len(errors) > 0

    def test_validate_non_hnpx_document(self, non_hnpx_file):
        """Test basic validation of a non-HNPX XML document."""
        errors = validate_hnpx_basic(str(non_hnpx_file))
        assert isinstance(errors, list)
        assert len(errors) > 0
        assert any("Root element must be 'book'" in error for error in errors)

    def test_create_invalid_documents_for_testing(self, temp_dir):
        """Test various invalid HNPX documents."""
        # Test missing book ID
        file_path = temp_dir / "no_id.xml"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="utf-8"?>\n<book><summary>Test</summary></book>'
            )

        errors = validate_hnpx_basic(str(file_path))
        assert any("Book element must have 'id' attribute" in error for error in errors)

        # Test invalid book ID format
        file_path = temp_dir / "invalid_id.xml"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="utf-8"?>\n<book id="INVALID"><summary>Test</summary></book>'
            )

        errors = validate_hnpx_basic(str(file_path))
        assert any(
            "Book ID must be exactly 6 lowercase letters/digits" in error
            for error in errors
        )

        # Test missing book summary
        file_path = temp_dir / "no_summary.xml"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n<book id="abc123"></book>')

        errors = validate_hnpx_basic(str(file_path))
        assert any("Book must have a non-empty summary" in error for error in errors)

        # Test empty book summary
        file_path = temp_dir / "empty_summary.xml"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="utf-8"?>\n<book id="abc123"><summary></summary></book>'
            )

        errors = validate_hnpx_basic(str(file_path))
        assert any("Book must have a non-empty summary" in error for error in errors)

    def test_validate_duplicate_ids(self, temp_dir):
        """Test validation with duplicate IDs."""
        file_path = temp_dir / "duplicate_ids.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <summary>Test book</summary>
  <chapter id="def456">
    <summary>Test chapter</summary>
    <sequence id="def456">
      <summary>Test sequence</summary>
    </sequence>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        assert any("Duplicate ID: def456" in error for error in errors)

    def test_validate_invalid_hierarchy(self, temp_dir):
        """Test validation with invalid hierarchy."""
        file_path = temp_dir / "invalid_hierarchy.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <summary>Test book</summary>
  <chapter id="def456">
    <summary>Test chapter</summary>
    <beat id="ghi789">
      <summary>Invalid beat under chapter</summary>
    </beat>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        assert any("chapter cannot contain beat" in error for error in errors)

    def test_validate_missing_chapter_title(self, temp_dir):
        """Test validation with missing chapter title."""
        file_path = temp_dir / "no_title.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <summary>Test book</summary>
  <chapter id="def456">
    <summary>Test chapter</summary>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        assert any("Chapter missing title attribute" in error for error in errors)

    def test_validate_missing_sequence_location(self, temp_dir):
        """Test validation with missing sequence location."""
        file_path = temp_dir / "no_loc.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <summary>Test book</summary>
  <chapter id="def456" title="Test Chapter">
    <summary>Test chapter</summary>
    <sequence id="ghi789">
      <summary>Test sequence</summary>
    </sequence>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        assert any("Sequence missing loc attribute" in error for error in errors)

    def test_validate_dialogue_without_char(self, temp_dir):
        """Test validation with dialogue paragraph missing character."""
        file_path = temp_dir / "no_char.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <summary>Test book</summary>
  <chapter id="def456" title="Test Chapter">
    <summary>Test chapter</summary>
    <sequence id="ghi789" loc="Test Location">
      <summary>Test sequence</summary>
      <beat id="jkl012">
        <summary>Test beat</summary>
        <paragraph id="mno345" mode="dialogue">
          <summary>Test paragraph</summary>
          "Hello world!"
        </paragraph>
      </beat>
    </sequence>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        assert any(
            "Dialogue paragraph missing char attribute" in error for error in errors
        )

    def test_validate_empty_paragraph_text(self, temp_dir):
        """Test validation with empty paragraph text."""
        file_path = temp_dir / "empty_text.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <summary>Test book</summary>
  <chapter id="def456" title="Test Chapter">
    <summary>Test chapter</summary>
    <sequence id="ghi789" loc="Test Location">
      <summary>Test sequence</summary>
      <beat id="jkl012">
        <summary>Test beat</summary>
        <paragraph id="mno345">
          <summary>Test paragraph</summary>
        </paragraph>
      </beat>
    </sequence>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        assert any("Paragraph has empty text content" in error for error in errors)

    def test_validate_missing_summaries(self, temp_dir):
        """Test validation with missing summaries."""
        file_path = temp_dir / "missing_summaries.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <chapter id="def456" title="Test Chapter">
    <sequence id="ghi789" loc="Test Location">
      <beat id="jkl012">
        <paragraph id="mno345">
          Test text
        </paragraph>
      </beat>
    </sequence>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        # Should have multiple missing summary errors
        summary_errors = [error for error in errors if "missing summary" in error]
        assert len(summary_errors) >= 4  # book, chapter, sequence, beat, paragraph

    def test_validate_complex_document(self, temp_dir):
        """Test validation of a complex but valid document."""
        file_path = temp_dir / "complex.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <summary>A complex test book with multiple chapters and nested elements</summary>
  
  <chapter id="def456" title="First Chapter" pov="main_char">
    <summary>The first chapter of our story</summary>
    
    <sequence id="ghi789" loc="Forest" time="morning">
      <summary>A morning scene in the forest</summary>
      
      <beat id="jkl012">
        <summary>Entering the forest</summary>
        
        <paragraph id="mno345" mode="narration">
          <summary>Description of the forest entrance</summary>
          The forest loomed ahead, dark and mysterious.
        </paragraph>
        
        <paragraph id="pqr678" mode="internal" char="main_char">
          <summary>Character's thoughts about the forest</summary>
          I wonder what dangers await me in these woods.
        </paragraph>
      </beat>
      
      <beat id="stu901">
        <summary>First encounter</summary>
        
        <paragraph id="vwx234" mode="dialogue" char="mysterious_voice">
          <summary>A mysterious voice speaks</summary>
          "Turn back now, while you still can."
        </paragraph>
      </beat>
    </sequence>
  </chapter>
  
  <chapter id="yza567" title="Second Chapter" pov="main_char">
    <summary>The second chapter continues the adventure</summary>
    
    <sequence id="bcd890" loc="Village" time="afternoon">
      <summary>Arrival at the village</summary>
      
      <beat id="efg123">
        <summary>Meeting the villagers</summary>
        
        <paragraph id="hij456" mode="narration">
          <summary>Description of the village</summary>
          The village was small but bustling with activity.
        </paragraph>
      </beat>
    </sequence>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        assert errors == []

    def test_validate_with_unicode_content(self, temp_dir):
        """Test validation with Unicode content."""
        file_path = temp_dir / "unicode.xml"
        content = """<?xml version="1.0" encoding="utf-8"?>
<book id="abc123">
  <summary>测试书 with émojis 🚀 and ñ special chars</summary>
  <chapter id="def456" title="Capítulo Uno" pov="主角">
    <summary>Un capítulo con contenido especial</summary>
    <sequence id="ghi789" loc="場所" time="朝">
      <summary>シーンの説明</summary>
      <beat id="jkl012">
        <summary>Beat summary</summary>
        <paragraph id="mno345" mode="dialogue" char="角色">
          <summary>Character dialogue</summary>
          "¡Hola! こんにちは 你好"
        </paragraph>
      </beat>
    </sequence>
  </chapter>
</book>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        errors = validate_hnpx_basic(str(file_path))
        assert errors == []
