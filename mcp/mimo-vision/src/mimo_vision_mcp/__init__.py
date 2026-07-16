"""MCP server that wraps Xiaomi MIMO multimodal API for visual understanding."""
import argparse
import asyncio

from .server import mcp

__version__ = "0.1.0"


def main():
    """Entry point for mimo-vision-mcp."""
    parser = argparse.ArgumentParser(
        description="MCP server for visual understanding via Xiaomi MIMO multimodal API"
    )
    parser.add_argument(
        "--model", type=str, default="mimo-v2.5",
        help="MIMO model name (default: mimo-v2.5)"
    )
    args = parser.parse_args()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
