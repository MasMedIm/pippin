import subprocess
import json
from typing import Dict, Any, Optional

class MCPClient:
    def __init__(self, server_path: str = "opentrons_mcp.py"):
        self.server_path = server_path
    
    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Call an MCP tool and return the result"""
        try:
            # Prepare the MCP call
            mcp_input = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }
            
            # Execute MCP server
            process = subprocess.run(
                ["python", self.server_path],
                input=json.dumps(mcp_input),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if process.returncode != 0:
                return f"MCP Error: {process.stderr}"
            
            # Parse response
            response = json.loads(process.stdout)
            if "error" in response:
                return f"Tool Error: {response['error']}"
            
            return response.get("result", {}).get("content", [{}])[0].get("text", "No result")
            
        except Exception as e:
            return f"Error calling MCP tool: {str(e)}"