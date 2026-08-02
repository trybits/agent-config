"""MCP server that wraps Zhipu GLM-4.6V-Flash multimodal API for visual understanding."""
import argparse
import os
from importlib.metadata import PackageNotFoundError, version

from .server import mcp

try:
    __version__ = version("zhipu-glm-vision-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"


def main():
    """Entry point for zhipu-glm-vision-mcp."""
    parser = argparse.ArgumentParser(
        description="MCP server for GLM-4.6V-Flash multimodal understanding via Zhipu API"
    )
    parser.add_argument(
        "--model", default=None,
        help="GLM model name (default: $GLM_MODEL env or glm-4.6v-flash)"
    )
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="Transport protocol to use (stdio, streamable-http or sse)",
    )
    parser.add_argument(
        "--thinking", default=None, action="store_true",
        help="Enable thinking mode by default (default: $GLM_THINKING env, off)",
    )
    parser.add_argument(
        "--no-thinking", default=None, action="store_true",
        help="Disable thinking mode by default (overrides $GLM_THINKING env)",
    )
    parser.add_argument(
        "--reasoning", default=None, action="store_true",
        help="Enable thinking and return the reasoning chain by default "
        "(sets $GLM_THINKING=enabled_with_reasoning)",
    )
    args = parser.parse_args()
    if args.model:
        os.environ["GLM_MODEL"] = args.model
    if args.reasoning:
        os.environ["GLM_THINKING"] = "enabled_with_reasoning"
    elif args.thinking:
        os.environ["GLM_THINKING"] = "enabled"
    elif args.no_thinking:
        os.environ["GLM_THINKING"] = "disabled"
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
