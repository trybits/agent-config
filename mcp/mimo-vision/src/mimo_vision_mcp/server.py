"""MIMO Vision Understanding MCP Server.

Wraps Xiaomi MIMO multimodal API as MCP tools for Codex.
"""
import base64
import os
from pathlib import Path
from typing import Optional

from openai import OpenAI
from mcp.server.fastmcp import FastMCP

MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5"
DEFAULT_PROMPT = "请详细描述这张图片的内容，包括其中的物体、文字、场景、颜色、布局等所有可见信息。"

MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def get_mime(path: Path) -> str:
    return MIME_MAP.get(path.suffix.lower(), "image/png")


def build_client() -> OpenAI:
    key = os.environ.get("MIMO_API_KEY", "")
    if not key:
        raise RuntimeError(
            "MIMO_API_KEY environment variable is not set."
        )
    return OpenAI(api_key=key, base_url=MIMO_BASE_URL)


def token_info(response) -> str:
    if hasattr(response, "usage") and response.usage:
        u = response.usage
        return (
            f"\n\n---\n"
            f"Model: {response.model} | "
            f"Prompt tokens: {u.prompt_tokens} | "
            f"Completion tokens: {u.completion_tokens} | "
            f"Total tokens: {u.total_tokens}"
        )
    return ""


mcp = FastMCP(
    "mimo-vision",
    instructions="MCP server for visual understanding via Xiaomi MIMO API.",
)


@mcp.tool(
    name="analyze_image",
    description="Analyze a local image file. Supports JPEG, PNG, GIF, WebP, BMP up to 50MB.",
)
def analyze_image(file_path: str, prompt: Optional[str] = None) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"Error: File not found: {file_path}"
    if not path.is_file():
        return f"Error: Path is not a file: {file_path}"
    size = path.stat().st_size
    if size > 50 * 1024 * 1024:
        return f"Error: File too large ({size / 1024 / 1024:.1f} MB)."
    try:
        mime = get_mime(path)
        data = base64.b64encode(path.read_bytes()).decode("utf-8")
        url = f"data:{mime};base64,{data}"
        client = build_client()
        resp = client.chat.completions.create(
            model=MIMO_MODEL,
            messages=[
                {"role": "system", "content": "You are MiMo. Analyze images thoroughly and provide detailed, accurate descriptions."},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": url}},
                    {"type": "text", "text": prompt or DEFAULT_PROMPT},
                ]},
            ],
            max_completion_tokens=2048,
        )
        content = resp.choices[0].message.content
        if content is None:
            return "Error: No content in model response."
        return content + token_info(resp)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="analyze_image_url",
    description="Analyze an image from a public URL.",
)
def analyze_image_url(url: str, prompt: Optional[str] = None) -> str:
    try:
        client = build_client()
        resp = client.chat.completions.create(
            model=MIMO_MODEL,
            messages=[
                {"role": "system", "content": "You are MiMo. Analyze images thoroughly and provide detailed, accurate descriptions."},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": url}},
                    {"type": "text", "text": prompt or DEFAULT_PROMPT},
                ]},
            ],
            max_completion_tokens=2048,
        )
        content = resp.choices[0].message.content
        if content is None:
            return "Error: No content in model response."
        return content + token_info(resp)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="analyze_multiple_images",
    description="Analyze multiple local images together. Max 10 images.",
)
def analyze_multiple_images(
    file_paths: list[str],
    prompt: str = "请对比分析这些图片的内容、联系和区别。",
) -> str:
    if not file_paths:
        return "Error: No file paths provided."
    if len(file_paths) > 10:
        return "Error: Maximum 10 images per request."
    try:
        parts = []
        for fp in file_paths:
            p = Path(fp)
            if not p.exists():
                return f"Error: File not found: {fp}"
            mime = get_mime(p)
            data = base64.b64encode(p.read_bytes()).decode("utf-8")
            parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}})
        parts.append({"type": "text", "text": prompt})
        client = build_client()
        resp = client.chat.completions.create(
            model=MIMO_MODEL,
            messages=[
                {"role": "system", "content": "You are MiMo. Analyze images thoroughly."},
                {"role": "user", "content": parts},
            ],
            max_completion_tokens=4096,
        )
        content = resp.choices[0].message.content
        if content is None:
            return "Error: No content in model response."
        return content
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
