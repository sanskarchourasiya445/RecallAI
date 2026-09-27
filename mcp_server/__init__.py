"""
RecallAI MCP Server Package.
Implements Model Context Protocol (MCP) tool exposure for external clients.
"""

from mcp_server.server import handle_json_rpc_message, run_stdio_server

__all__ = ["handle_json_rpc_message", "run_stdio_server"]
