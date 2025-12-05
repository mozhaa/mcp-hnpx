"""
MCP HNPX Server - A Model Context Protocol server for HNPX document processing.
"""

__version__ = "1.0.0"
__all__ = ["HNPXMCP", "run_server"]

from .server import HNPXMCP, run_server
