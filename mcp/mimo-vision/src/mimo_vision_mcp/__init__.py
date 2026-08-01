"""MCP server that wraps Xiaomi MIMO multimodal API for visual understanding."""
import argparse
import os
from importlib.metadata import PackageNotFoundError, version

from .server import mcp

try:
    __version__ = version("mimo-vision-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"


def main():
    """Entry point for mimo-vision-mcp."""
    parser = argparse.ArgumentParser(
        description="MCP server for visual understanding via Xiaomi MIMO multimodal API"
    )
    parser.add_argument(
        "--model", default=None,
        help="MIMO model name (default: $MIMO_MODEL env or mimo-v2.5)"
    )
    args = parser.parse_args()
    if args.model:
        os.environ["MIMO_MODEL"] = args.model
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
