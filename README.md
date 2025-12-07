# HNPX SDK

A collection of tools for **HNPX** - a hierarchical XML-based format for planning and writing fiction. This project introduces the HNPX format and provides tools for creating, editing, and managing HNPX documents.

## Origin

**LLMs can't write a book.** Well, technically they can write _a_ book: they'll generate thousands of words that follow narrative conventions. **But they can't write _your_ book**, the specific story only you have in mind. That gap between "AI can write fiction" and "AI can't write the fiction I want" is the core of the workflow, described below.

Ask an LLM to write a whole chapter, and it'll **speedrun through the plot in about 300 words.** Try going paragraph by paragraph, and you'll find the AI **doesn't know when to stop one scene and start the next.**

This led to experimenting with **hierarchy:** first generating a detailed chapter plan with sections, then asking the LLM to write each section individually based on that plan. This approach improved structure and word count: the chapter speedrun problem was less severe, and scene boundaries were clearer. This hierarchical method required automation, which I implemented through simple Python scripts. However, a fully automated process without guidance led the LLM to **write nonsense, not at all what I wanted.** The text became filled with errors, and the problem was even more pronounced when writing in Russian, where general LLMs produce noticeably poorer text quality.

**The solution evolved into HNPX,** a narrative planning format that structures the writing process from book-level overview down to atomic paragraphs. It allows for **step-by-step expansion,** maintaining context and control at each level while keeping human guidance central to the process.

To bring HNPX to life, I considered building a custom UI or VS Code extension, but that would have been too difficult: creating a whole AI agent system from scratch. Instead, I realized **Roo Code** already provided the perfect foundation. Its flexible mode system meant I could build an **MCP server** and create **custom modes** to use it, creating exactly the workflow HNPX required. HNPX structures the writing process so that **LLMs write under human guidance at each step,** transforming them from autonomous storytellers into responsive collaborators.

> **TL;DR:** HNPX defines a structured writing workflow where LLMs write under human direction at each level, turning AI from an autonomous storyteller into a guided collaborator.

## What is HNPX?

HNPX (Hierarchical Narrative Planning XML) is a structured XML format designed for planning and writing fiction. It organizes narrative content into a strict hierarchy from book-level overview down to individual paragraphs, enabling a step-by-step expansion approach that maintains context and control throughout the writing process.

The format supports both high-level planning (summaries without full text) and complete documentation (full prose ready for rendering), making it flexible for writers at any stage of their creative process.

See [this document](tests/resources/mixed.xml) as a reference.

## Features

-   **MCP Server**: Model Context Protocol server for AI agent integration
-   **CLI Tools**: Command-line interface for some tasks
-   **Roo Code Integration**: Custom modes for collaborative fiction writing
    -   **HNPX Editor Mode**: Interactive mode for creating and editing hierarchical narrative documents
    -   **Bible Writer Mode**: Specialized mode for creating fiction reference documents

## MCP Tools

The HNPX SDK provides a comprehensive set of **MCP** (Model Context Protocol) tools that enable AI agents to fully manipulate HNPX documents, from creating new documents to editing individual paragraphs and restructuring the narrative hierarchy. See [docs/mcp-tools.md](docs/mcp-tools.md) for complete documentation.

## Installation

Install the HNPX SDK:

```bash
pip install -e .
# or via uv
uv pip install -e .
```

#### Roo Code Modes Setup

To use the custom Roo Code modes for HNPX editing, place [.roomodes](.roomodes) into your project root:
