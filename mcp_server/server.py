"""
Lightweight Model Context Protocol (MCP) Server for RecallAI.
Conforms to MCP JSON-RPC 2.0 protocol specifications over stdio or direct message invocation.
Exposes RecallAI's controlled meeting action tools:
- create_task, list_tasks
- create_calendar_event, list_calendar_events
- draft_email, send_email
"""

import sys
import json
from typing import Dict, Any, Optional

from core.actions.tool_registry import DEFAULT_TOOL_REGISTRY, ToolRegistry
from core.actions.models import ToolResult

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "recallai-meeting-assistant"
SERVER_VERSION = "1.0.0"


def handle_json_rpc_message(
    message: Dict[str, Any],
    registry: ToolRegistry = DEFAULT_TOOL_REGISTRY,
) -> Optional[Dict[str, Any]]:
    """
    Process an incoming MCP JSON-RPC message and generate appropriate response.
    Supports:
    - initialize
    - tools/list
    - tools/call
    - ping
    """
    msg_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {})

    # Notification / Handshake without response
    if method == "notifications/initialized":
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    # Initialize handshake
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
                },
            },
        }

    # Tool listing
    if method == "tools/list":
        tools_list = registry.list_tools()
        # Format according to MCP schema: name, description, inputSchema
        formatted_tools = [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            }
            for t in tools_list
        ]
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": formatted_tools},
        }

    # Tool invocation
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        result: ToolResult = registry.execute_tool(tool_name, arguments)

        content_item = {
            "type": "text",
            "text": json.dumps(result.to_dict(), indent=2),
        }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [content_item],
                "isError": not result.success,
            },
        }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {
            "code": -32601,
            "message": f"Method '{method}' not found.",
        },
    }


def run_stdio_server(registry: ToolRegistry = DEFAULT_TOOL_REGISTRY):
    """Run interactive MCP server reading JSON-RPC lines from stdin and writing to stdout."""
    for line in sys.stdin:
        line_clean = line.strip()
        if not line_clean:
            continue
        try:
            req = json.loads(line_clean)
            resp = handle_json_rpc_message(req, registry=registry)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
