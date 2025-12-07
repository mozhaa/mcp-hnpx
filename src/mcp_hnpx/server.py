import fastmcp
from . import tools

app = fastmcp.FastMCP("hnpx-server", version="1.0.0")

# Document Management Tools
app.tool()(tools.create_document)

# Navigation & Discovery Tools
app.tool()(tools.get_empty)
app.tool()(tools.get_node)

# Node Inspection Tools
app.tool()(tools.get_subtree)
app.tool()(tools.get_children)
app.tool()(tools.get_path)

# Node Creation Tools
app.tool()(tools.create_chapter)
app.tool()(tools.create_sequence)
app.tool()(tools.create_beat)
app.tool()(tools.create_paragraph)

# Node Modification Tools
app.tool()(tools.edit_node_attributes)
app.tool()(tools.remove_nodes)
app.tool()(tools.reorder_children)
app.tool()(tools.edit_summary)
app.tool()(tools.edit_paragraph_text)
app.tool()(tools.move_nodes)
app.tool()(tools.remove_node_children)

# Rendering & Export Tools
app.tool()(tools.render_node)
app.tool()(tools.render_document)


if __name__ == "__main__":
    app.run()
