import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hnpx-tools", description="perform some basic actions on HNPX documents"
    )
    subparsers = parser.add_subparsers(title="actions")

    render_parser = subparsers.add_parser(
        "render", description="render an HNPX document into some format"
    )
    render_parser.add_argument("file", type=str, help="path to HNPX document")
    render_parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="plain",
        choices=["plain", "plain_with_ids", "fb2"],
        help="output format",
    )
    render_parser.add_argument(
        "--no-section-marks",
        action="store_true",
        help="don't mark chapter/sequence beginnings",
    )
    render_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="interactive mode for fillint the blanks in FB2 metadata",
    )
    render_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="path to output file (default: stdout)",
    )
    render_parser.set_defaults(func=render)

    list_tools_parser = subparsers.add_parser(
        "list-tools", description="list available MCP tools"
    )
    list_tools_parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["minimal", "medium", "markdown"],
        default="minimal",
        help="output format",
    )
    list_tools_parser.set_defaults(func=list_tools)

    return parser.parse_args()


def render(args: argparse.Namespace) -> None:
    def render_fb2() -> str:
        from lxml import etree

        from .hnpx import parse_document

        tree = parse_document(args.file)
        root = tree.getroot()

        fb2 = etree.Element(
            "FictionBook", xmlns="http://www.gribuser.ru/xml/fictionbook/2.0"
        )

        description = etree.SubElement(fb2, "description")
        title_info = etree.SubElement(description, "title-info")
        book_title = etree.SubElement(title_info, "book-title")
        book_title.text = input("Title: ") if args.interactive else "Untitled"
        body = etree.SubElement(fb2, "body")

        for chapter in root:
            if chapter.tag == "summary":
                continue
            section = etree.SubElement(body, "section")
            title = etree.SubElement(section, "title")
            p = etree.SubElement(title, "p")
            p.text = chapter.get("title")
            is_first_sequence = True
            for sequence in chapter:
                if sequence.tag == "summary":
                    continue
                if not is_first_sequence:
                    sep_p = etree.SubElement(section, "p")
                    sep_p.text = "***"
                is_first_sequence = False
                for beat in sequence:
                    if beat.tag == "summary":
                        continue
                    for paragraph in beat:
                        if paragraph.tag == "summary":
                            continue
                        fb2_p = etree.SubElement(section, "p")
                        fb2_p.text = (paragraph.text or "").strip()

        return etree.tostring(fb2, encoding="unicode", pretty_print=True)

    def render_plain() -> str:
        from .tools import get_root_id, render_node

        root_id = get_root_id(args.file)
        return render_node(
            args.file,
            root_id,
            args.format == "plain_with_ids",
            not args.no_section_marks,
        )

    if args.format == "fb2":
        result = render_fb2()
    else:
        result = render_plain()

    if args.output:
        with open(args.output, "w+", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)


def list_tools(args: argparse.Namespace) -> None:
    import asyncio

    from hnpx_sdk.server import app

    async def f() -> None:
        tools = await app.get_tools()
        if args.format == "markdown":
            print("# Available MCP Tools\n")
            print("### Navigation:")
            for name, tool in tools.items():
                print(f"- [{name}](#{name})")
            print()
            for name, tool in tools.items():
                print(f"## `{name}`")
                print(f"{tool.description}")
                print()
        else:
            for name, tool in tools.items():
                if args.format == "minimal":
                    print(name)
                elif args.format == "medium":
                    print(f"- {name}: {tool.description}")
                    print()

    asyncio.run(f())


def main() -> None:
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
