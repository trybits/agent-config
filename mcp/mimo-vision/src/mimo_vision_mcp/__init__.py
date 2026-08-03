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
    parser.add_argument(
        "--thinking", default=None,
        choices=["disabled", "enabled", "enabled_with_reasoning"],
        help="Default thinking mode (default: $MIMO_THINKING env or disabled)"
    )
    parser.add_argument(
        "--max-completion-tokens", default=None, type=int,
        help="Default max_completion_tokens (default: $MIMO_MAX_COMPLETION_TOKENS env or official default)"
    )
    args = parser.parse_args()
    if args.model:
        os.environ["MIMO_MODEL"] = args.model
    if args.thinking:
        os.environ["MIMO_THINKING"] = args.thinking
    if args.max_completion_tokens:
        os.environ["MIMO_MAX_COMPLETION_TOKENS"] = str(args.max_completion_tokens)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
