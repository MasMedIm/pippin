#!/usr/bin/env python3
"""
Simple MCP Server using FastMCP that returns your name
"""
from mcp.server.fastmcp import FastMCP
from typing import Optional

# Initialize the FastMCP server
mcp = FastMCP("Name Server")

# Store the user's name (you can modify this)
USER_NAME = "Ahsan Fuzail"  # Change this to your actual name

@mcp.tool()
def get_my_name() -> str:
    """Returns the user's name"""
    return f"Your name is: {USER_NAME}"

@mcp.tool()
def get_my_name_all_caps() -> str:
    """Returns the user's name in all caps"""
    return f"Your name is: {USER_NAME.upper()}"

if __name__ == "__main__":
    # Run the server
    mcp.run(transport='stdio')