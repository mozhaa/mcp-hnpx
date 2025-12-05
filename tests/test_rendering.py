"""
Tests for rendering and export tools.
"""

import pytest
from lxml import etree

from src.mcp_hnpx.tools.rendering import (
    render_node,
    render_document,
    render_to_markdown,
)
from src.mcp_hnpx.errors import (
    FileNotFoundError,
    NotHNPXError,
    NodeNotFoundError,
)


class TestRenderNode:
    def test_render_book_node(self, sample_hnpx_file):
        """Test rendering a book node."""
        result = render_node(str(sample_hnpx_file), "b3k9m7")

        assert "[b3k9m7] Book:" in result
        assert "Boogiepop legend" in result
        assert "[c8p2q5] Chapter:" in result
        assert "Boogiepop" in result
        assert "(POV: suema)" in result

    def test_render_chapter_node(self, sample_hnpx_file):
        """Test rendering a chapter node."""
        result = render_node(str(sample_hnpx_file), "c8p2q5")

        assert "[c8p2q5] Chapter:" in result
        assert "Boogiepop" in result
        assert "(POV: suema)" in result
        assert "Summary: Students discuss the Boogiepop legend" in result
        assert "[s4r7t9] Sequence:" in result
        assert "School cafeteria at lunch" in result

    def test_render_sequence_node(self, sample_hnpx_file):
        """Test rendering a sequence node."""
        result = render_node(str(sample_hnpx_file), "s4r7t9")

        assert "[s4r7t9] Sequence:" in result
        assert "School cafeteria at lunch" in result
        assert "(POV: suema)" in result
        assert "Summary: Lunch conversation" in result
        assert "[b1v6x3] Beat:" in result

    def test_render_beat_node(self, sample_hnpx_file):
        """Test rendering a beat node."""
        result = render_node(str(sample_hnpx_file), "b1v6x3")

        assert "[b1v6x3] Beat:" in result
        assert "Introduction to the Boogiepop rumor" in result
        assert "[p9m5k2]" in result
        assert "The narrator introduces the Boogiepop rumor" in result

    def test_render_paragraph_node(self, sample_hnpx_file):
        """Test rendering a paragraph node."""
        result = render_node(str(sample_hnpx_file), "p9m5k2")

        assert "[p9m5k2]" in result
        assert "The narrator introduces the Boogiepop rumor" in result
        assert "Recently, a strange rumor" in result

    def test_render_dialogue_paragraph(self, temp_dir):
        """Test rendering a dialogue paragraph."""
        # Create document with dialogue paragraph
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter, "sequence", id="ghi789", loc="Test Location"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        beat = etree.SubElement(sequence, "beat", id="jkl012")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "Test beat"

        paragraph = etree.SubElement(
            beat, "paragraph", id="mno345", mode="dialogue", char="speaker"
        )
        paragraph_summary = etree.SubElement(paragraph, "summary")
        paragraph_summary.text = "Dialogue summary"
        paragraph.text = "Hello world!"

        file_path = temp_dir / "dialogue_render.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = render_node(str(file_path), "mno345")

        assert "[mno345]" in result
        assert "Dialogue summary" in result
        assert "speaker: Hello world!" in result

    def test_render_internal_paragraph(self, temp_dir):
        """Test rendering an internal monologue paragraph."""
        # Create document with internal paragraph
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter, "sequence", id="ghi789", loc="Test Location"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        beat = etree.SubElement(sequence, "beat", id="jkl012")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "Test beat"

        paragraph = etree.SubElement(
            beat, "paragraph", id="mno345", mode="internal", char="thinker"
        )
        paragraph_summary = etree.SubElement(paragraph, "summary")
        paragraph_summary.text = "Internal summary"
        paragraph.text = "This is my internal thought."

        file_path = temp_dir / "internal_render.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = render_node(str(file_path), "mno345")

        assert "[mno345]" in result
        assert "Internal summary" in result
        assert "*This is my internal thought.*" in result

    def test_render_dialogue_with_quotes(self, temp_dir):
        """Test rendering dialogue paragraph that already has quotes."""
        # Create document with dialogue paragraph that has quotes
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter, "sequence", id="ghi789", loc="Test Location"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        beat = etree.SubElement(sequence, "beat", id="jkl012")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "Test beat"

        paragraph = etree.SubElement(
            beat, "paragraph", id="mno345", mode="dialogue", char="speaker"
        )
        paragraph_summary = etree.SubElement(paragraph, "summary")
        paragraph_summary.text = "Dialogue summary"
        paragraph.text = '"Already quoted text"'

        file_path = temp_dir / "quoted_dialogue.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = render_node(str(file_path), "mno345")

        assert "[mno345]" in result
        assert 'speaker: "Already quoted text"' in result

    def test_render_node_indentation(self, sample_hnpx_file):
        """Test that rendered output has proper indentation."""
        result = render_node(str(sample_hnpx_file), "b3k9m7")

        lines = result.split("\n")

        # Check that nested elements are indented
        book_line = next(line for line in lines if "[b3k9m7] Book:" in line)
        chapter_line = next(line for line in lines if "[c8p2q5] Chapter:" in line)
        sequence_line = next(line for line in lines if "[s4r7t9] Sequence:" in line)

        # Chapter should be indented more than book
        assert chapter_line.startswith("  ") and not book_line.startswith("  ")
        # Sequence should be indented more than chapter
        assert sequence_line.startswith("    ") and chapter_line.startswith("  ")

    def test_render_nonexistent_node(self, sample_hnpx_file):
        """Test rendering non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc_info:
            render_node(str(sample_hnpx_file), "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_render_nonexistent_file(self):
        """Test rendering node from non-existent file."""
        with pytest.raises(FileNotFoundError):
            render_node("nonexistent.xml", "any_id")

    def test_render_invalid_xml(self, invalid_xml_file):
        """Test rendering node from invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            render_node(str(invalid_xml_file), "any_id")

    def test_render_non_hnpx_document(self, non_hnpx_file):
        """Test rendering node from non-HNPX document."""
        with pytest.raises(NotHNPXError):
            render_node(str(non_hnpx_file), "any_id")


class TestRenderDocument:
    def test_render_complete_document(self, sample_hnpx_file):
        """Test rendering complete document to plain text."""
        result = render_document(str(sample_hnpx_file))

        # Should contain paragraph text
        assert "Recently, a strange rumor" in result
        assert "It's something about the mysterious Boogiepop" in result

        # Should be formatted as continuous text
        assert isinstance(result, str)
        assert len(result) > 0

        # Should not contain XML tags or IDs
        assert "<paragraph>" not in result
        assert "[p9m5k2]" not in result
        assert "<summary>" not in result

    def test_render_document_with_dialogue(self, temp_dir):
        """Test rendering document with dialogue paragraphs."""
        # Create document with mixed paragraph types
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test book"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Test chapter"

        sequence = etree.SubElement(
            chapter, "sequence", id="ghi789", loc="Test Location"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Test sequence"

        beat = etree.SubElement(sequence, "beat", id="jkl012")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "Test beat"

        # Add different paragraph types
        para1 = etree.SubElement(beat, "paragraph", id="p001", mode="narration")
        para1_summary = etree.SubElement(para1, "summary")
        para1_summary.text = "Narration summary"
        para1.text = "This is narration text."

        para2 = etree.SubElement(
            beat, "paragraph", id="p002", mode="dialogue", char="speaker"
        )
        para2_summary = etree.SubElement(para2, "summary")
        para2_summary.text = "Dialogue summary"
        para2.text = "This is dialogue text."

        para3 = etree.SubElement(
            beat, "paragraph", id="p003", mode="internal", char="thinker"
        )
        para3_summary = etree.SubElement(para3, "summary")
        para3_summary.text = "Internal summary"
        para3.text = "This is internal thought."

        file_path = temp_dir / "mixed_paragraphs.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = render_document(str(file_path))

        assert "This is narration text." in result
        assert 'speaker: "This is dialogue text."' in result
        assert "*This is internal thought.*" in result

        # Should be separated by double newlines
        assert "\n\n" in result

    def test_render_empty_document(self, minimal_hnpx_file):
        """Test rendering document with no paragraphs."""
        result = render_document(str(minimal_hnpx_file))

        # Should return empty string since no paragraphs
        assert result == ""

    def test_render_document_unicode_content(self, temp_dir):
        """Test rendering document with Unicode content."""
        # Create document with Unicode text
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "测试书"

        chapter = etree.SubElement(root, "chapter", id="def456", title="Capítulo Uno")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Un capítulo"

        sequence = etree.SubElement(chapter, "sequence", id="ghi789", loc="場所")
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "シーンの説明"

        beat = etree.SubElement(sequence, "beat", id="jkl012")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "Beat summary"

        paragraph = etree.SubElement(
            beat, "paragraph", id="mno345", mode="dialogue", char="角色"
        )
        paragraph_summary = etree.SubElement(paragraph, "summary")
        paragraph_summary.text = "対話の要約"
        paragraph.text = "¡Hola! こんにちは 你好"

        file_path = temp_dir / "unicode_document.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = render_document(str(file_path))

        assert '角色: "¡Hola! こんにちは 你好"' in result

    def test_render_nonexistent_file(self):
        """Test rendering non-existent file."""
        with pytest.raises(FileNotFoundError):
            render_document("nonexistent.xml")

    def test_render_invalid_xml(self, invalid_xml_file):
        """Test rendering invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            render_document(str(invalid_xml_file))

    def test_render_non_hnpx_document(self, non_hnpx_file):
        """Test rendering non-HNPX document."""
        with pytest.raises(NotHNPXError):
            render_document(str(non_hnpx_file))


class TestRenderToMarkdown:
    def test_render_to_markdown_complete(self, sample_hnpx_file):
        """Test rendering complete document to markdown."""
        result = render_to_markdown(str(sample_hnpx_file))

        # Should have markdown headers
        assert "# " in result  # Book title as H1
        assert "## " in result  # Chapter title as H2
        assert "### " in result  # Sequence as H3
        assert "#### " in result  # Beat as H4

        # Should contain content
        assert "Boogiepop legend" in result
        assert "Students discuss the Boogiepop legend" in result
        assert "School cafeteria" in result
        assert "Introduction to the Boogiepop rumor" in result

        # Should have book ID
        assert "*Book ID: b3k9m7*" in result

        # Should have POV information
        assert "*POV: suema*" in result

    def test_render_to_markdown_structure(self, temp_dir):
        """Test markdown structure with multiple chapters."""
        # Create document with multiple chapters
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test Book Title"

        # First chapter
        chapter1 = etree.SubElement(
            root, "chapter", id="ch001", title="First Chapter", pov="char1"
        )
        chapter1_summary = etree.SubElement(chapter1, "summary")
        chapter1_summary.text = "First chapter summary"

        seq1 = etree.SubElement(chapter1, "sequence", id="seq001", loc="Location 1")
        seq1_summary = etree.SubElement(seq1, "summary")
        seq1_summary.text = "First sequence summary"

        beat1 = etree.SubElement(seq1, "beat", id="beat001")
        beat1_summary = etree.SubElement(beat1, "summary")
        beat1_summary.text = "First beat summary"

        para1 = etree.SubElement(beat1, "paragraph", id="para001")
        para1_summary = etree.SubElement(para1, "summary")
        para1_summary.text = "First paragraph summary"
        para1.text = "First paragraph text."

        # Second chapter
        chapter2 = etree.SubElement(
            root, "chapter", id="ch002", title="Second Chapter", pov="char2"
        )
        chapter2_summary = etree.SubElement(chapter2, "summary")
        chapter2_summary.text = "Second chapter summary"

        seq2 = etree.SubElement(
            chapter2, "sequence", id="seq002", loc="Location 2", time="evening"
        )
        seq2_summary = etree.SubElement(seq2, "summary")
        seq2_summary.text = "Second sequence summary"

        beat2 = etree.SubElement(seq2, "beat", id="beat002")
        beat2_summary = etree.SubElement(beat2, "summary")
        beat2_summary.text = "Second beat summary"

        para2 = etree.SubElement(beat2, "paragraph", id="para002")
        para2_summary = etree.SubElement(para2, "summary")
        para2_summary.text = "Second paragraph summary"
        para2.text = "Second paragraph text."

        file_path = temp_dir / "markdown_structure.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = render_to_markdown(str(file_path))

        # Check structure
        result.split("\n")

        # Should have book title
        assert "# Test Book Title" in result
        assert "*Book ID: abc123*" in result

        # Should have both chapters
        assert "## First Chapter" in result
        assert "## Second Chapter" in result

        # Should have POV info
        assert "*POV: char1*" in result
        assert "*POV: char2*" in result

        # Should have sequences with time
        assert "### **Location 1**" in result
        assert "### **Location 2** (evening)" in result

        # Should have beats and paragraphs
        assert "#### First beat summary" in result
        assert "First paragraph text." in result
        assert "#### Second beat summary" in result
        assert "Second paragraph text." in result

    def test_render_to_markdown_with_different_povs(self, temp_dir):
        """Test markdown rendering with different POV levels."""
        # Create document with POV inheritance
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test Book"

        chapter = etree.SubElement(
            root, "chapter", id="ch001", title="Test Chapter", pov="chapter_pov"
        )
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Chapter summary"

        # Sequence with different POV
        seq1 = etree.SubElement(chapter, "sequence", id="seq001", loc="Location 1")
        seq1_summary = etree.SubElement(seq1, "summary")
        seq1_summary.text = "Sequence 1 summary"

        # Sequence with same POV
        seq2 = etree.SubElement(
            chapter, "sequence", id="seq002", loc="Location 2", pov="sequence_pov"
        )
        seq2_summary = etree.SubElement(seq2, "summary")
        seq2_summary.text = "Sequence 2 summary"

        file_path = temp_dir / "pov_markdown.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = render_to_markdown(str(file_path))

        # Chapter should have POV
        assert "*POV: chapter_pov*" in result

        # First sequence should not show POV (inherits from chapter)
        seq1_line = next(line for line in result.split("\n") if "Location 1" in line)
        assert "[POV:" not in seq1_line

        # Second sequence should show POV (different from chapter)
        seq2_line = next(line for line in result.split("\n") if "Location 2" in line)
        assert "[POV: sequence_pov]" in seq2_line

    def test_render_to_markdown_unicode(self, temp_dir):
        """Test markdown rendering with Unicode content."""
        # Create document with Unicode content
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "测试书籍"

        chapter = etree.SubElement(root, "chapter", id="ch001", title="第一章")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "第一章摘要"

        sequence = etree.SubElement(chapter, "sequence", id="seq001", loc="学校")
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "场景摘要"

        beat = etree.SubElement(sequence, "beat", id="beat001")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "节拍摘要"

        paragraph = etree.SubElement(beat, "paragraph", id="para001")
        paragraph_summary = etree.SubElement(paragraph, "summary")
        paragraph_summary.text = "段落摘要"
        paragraph.text = "这是中文段落内容。"

        file_path = temp_dir / "unicode_markdown.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        result = render_to_markdown(str(file_path))

        assert "# 测试书籍" in result
        assert "## 第一章" in result
        assert "### **学校**" in result
        assert "这是中文段落内容。" in result

    def test_render_to_markdown_minimal(self, minimal_hnpx_file):
        """Test markdown rendering of minimal document."""
        result = render_to_markdown(str(minimal_hnpx_file))

        # Should have book title and ID
        assert "# New book" in result
        assert "*Book ID:" in result

        # Should not have chapters
        assert "## " not in result

    def test_render_to_markdown_nonexistent_file(self):
        """Test markdown rendering of non-existent file."""
        with pytest.raises(FileNotFoundError):
            render_to_markdown("nonexistent.xml")

    def test_render_to_markdown_invalid_xml(self, invalid_xml_file):
        """Test markdown rendering of invalid XML."""
        with pytest.raises(Exception):  # Should raise InvalidXMLError or similar
            render_to_markdown(str(invalid_xml_file))

    def test_render_to_markdown_non_hnpx_document(self, non_hnpx_file):
        """Test markdown rendering of non-HNPX document."""
        with pytest.raises(NotHNPXError):
            render_to_markdown(str(non_hnpx_file))


class TestRenderingIntegration:
    def test_rendering_consistency(self, temp_dir):
        """Test that different rendering methods are consistent."""
        # Create test document
        root = etree.Element("book", id="abc123")
        summary = etree.SubElement(root, "summary")
        summary.text = "Test Book"

        chapter = etree.SubElement(root, "chapter", id="ch001", title="Test Chapter")
        chapter_summary = etree.SubElement(chapter, "summary")
        chapter_summary.text = "Chapter summary"

        sequence = etree.SubElement(
            chapter, "sequence", id="seq001", loc="Test Location"
        )
        sequence_summary = etree.SubElement(sequence, "summary")
        sequence_summary.text = "Sequence summary"

        beat = etree.SubElement(sequence, "beat", id="beat001")
        beat_summary = etree.SubElement(beat, "summary")
        beat_summary.text = "Beat summary"

        paragraph = etree.SubElement(
            beat, "paragraph", id="para001", mode="dialogue", char="speaker"
        )
        paragraph_summary = etree.SubElement(paragraph, "summary")
        paragraph_summary.text = "Paragraph summary"
        paragraph.text = "Hello world!"

        file_path = temp_dir / "consistency_test.xml"
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        # Test different rendering methods
        node_render = render_node(str(file_path), "para001")
        doc_render = render_document(str(file_path))
        markdown_render = render_to_markdown(str(file_path))

        # All should contain the dialogue text
        assert "Hello world!" in node_render
        assert 'speaker: "Hello world!"' in doc_render
        assert "Hello world!" in markdown_render

        # Node render should have summary
        assert "Paragraph summary" in node_render

        # Document render should not have XML tags
        assert "<paragraph>" not in doc_render

        # Markdown render should have proper structure
        assert "# Test Book" in markdown_render
        assert "## Test Chapter" in markdown_render
