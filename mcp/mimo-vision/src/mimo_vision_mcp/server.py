"""MIMO Vision Understanding MCP Server.

Wraps Xiaomi MIMO multimodal API (mimo-v2.5) as MCP tools for Claude Code.
Supports image, audio, and video understanding per the MiMo V2.5 docs.
"""
import base64
import os
from pathlib import Path
from typing import Optional

from openai import OpenAI
from mcp.server import MCPServer

MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
DEFAULT_MIMO_MODEL = "mimo-v2.5"

DEFAULT_SYSTEM = (
    "You are MiMo, an AI assistant developed by Xiaomi. "
    "Analyze the provided media thoroughly and provide detailed, accurate descriptions."
)
DEFAULT_IMAGE_PROMPT = "请详细描述这张图片的内容，包括其中的物体、文字、场景、颜色、布局等所有可见信息。"
DEFAULT_AUDIO_PROMPT = "请详细描述这段音频的内容，包括语音内容、语气、背景声音等所有可感知信息。"
DEFAULT_VIDEO_PROMPT = "请详细描述这段视频的内容，包括画面、动作、场景、文字以及音频等所有可见可听信息。"
DEFAULT_COMPARE_PROMPT = "请对比分析这些内容，指出它们的联系和区别。"

IMAGE_MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}
AUDIO_MIME_MAP = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
}
VIDEO_MIME_MAP = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".wmv": "video/x-ms-wmv",
}

# Base64 编码传入时，所有媒体的编码字符串大小上限均为 50 MB（MiMo V2.5 文档）。
BASE64_MAX_MB = 50
MAX_PARTS = 10


def get_model() -> str:
    return os.environ.get("MIMO_MODEL", DEFAULT_MIMO_MODEL)


def build_client() -> OpenAI:
    key = os.environ.get("MIMO_API_KEY", "")
    if not key:
        raise RuntimeError(
            "MIMO_API_KEY environment variable is not set."
        )
    return OpenAI(api_key=key, base_url=MIMO_BASE_URL)


def media_to_base64_data_uri(
    path_str: str, mime_map: dict[str, str], label: str
) -> tuple[Optional[str], Optional[str]]:
    """Read a local media file into a data URI.

    Returns (data_uri, error); exactly one of the two is not None.
    """
    path = Path(path_str)
    if not path.exists():
        return None, f"Error: {label} file not found: {path_str}"
    if not path.is_file():
        return None, f"Error: Path is not a file: {path_str}"
    size = path.stat().st_size
    if size > BASE64_MAX_MB * 1024 * 1024:
        return None, (
            f"Error: {label} file too large "
            f"({size / 1024 / 1024:.1f} MB); Base64 传入上限为 {BASE64_MAX_MB} MB."
        )
    mime = mime_map.get(path.suffix.lower())
    if not mime:
        return None, (
            f"Error: Unsupported {label} file type '{path.suffix or '(no extension)'}'. "
            f"Supported: {', '.join(sorted(mime_map))}"
        )
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}", None


def validate_video_params(fps: float, media_resolution: str) -> Optional[str]:
    if not (0.1 <= fps <= 10):
        return f"Error: fps must be in range [0.1, 10], got {fps}."
    if media_resolution not in ("default", "max"):
        return f"Error: media_resolution must be 'default' or 'max', got {media_resolution!r}."
    return None


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


def _chat(media_parts: list[dict], prompt: str, max_tokens: int) -> str:
    """Send one completion request with media + text parts, return the text result."""
    try:
        client = build_client()
        resp = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": DEFAULT_SYSTEM},
                {"role": "user", "content": [*media_parts, {"type": "text", "text": prompt}]},
            ],
            max_completion_tokens=max_tokens,
        )
        content = resp.choices[0].message.content
        if content is None:
            return "Error: No content in model response."
        return content + token_info(resp)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


mcp = MCPServer(
    "mimo-vision",
    instructions="MCP server for image/audio/video understanding via Xiaomi MIMO API.",
)


@mcp.tool(
    name="analyze_image",
    description="Analyze a local image file. Supports JPEG, PNG, GIF, WebP, BMP up to 50MB.",
)
def analyze_image(file_path: str, prompt: Optional[str] = None) -> str:
    data_uri, err = media_to_base64_data_uri(file_path, IMAGE_MIME_MAP, "image")
    if err:
        return err
    return _chat(
        [{"type": "image_url", "image_url": {"url": data_uri}}],
        prompt or DEFAULT_IMAGE_PROMPT,
        2048,
    )


@mcp.tool(
    name="analyze_image_url",
    description="Analyze an image from a public URL. Supports JPEG, PNG, GIF, WebP, BMP up to 50MB.",
)
def analyze_image_url(url: str, prompt: Optional[str] = None) -> str:
    return _chat(
        [{"type": "image_url", "image_url": {"url": url}}],
        prompt or DEFAULT_IMAGE_PROMPT,
        2048,
    )


@mcp.tool(
    name="analyze_multiple_images",
    description="Analyze multiple local image files together. Max 10 images.",
)
def analyze_multiple_images(file_paths: list[str], prompt: str = DEFAULT_COMPARE_PROMPT) -> str:
    if not file_paths:
        return "Error: No file paths provided."
    if len(file_paths) > MAX_PARTS:
        return f"Error: Maximum {MAX_PARTS} images per request."
    parts = []
    for fp in file_paths:
        data_uri, err = media_to_base64_data_uri(fp, IMAGE_MIME_MAP, "image")
        if err:
            return err
        parts.append({"type": "image_url", "image_url": {"url": data_uri}})
    return _chat(parts, prompt, 4096)


@mcp.tool(
    name="analyze_multiple_images_url",
    description="Analyze multiple images from public URLs together. Max 10 images.",
)
def analyze_multiple_images_url(urls: list[str], prompt: str = DEFAULT_COMPARE_PROMPT) -> str:
    if not urls:
        return "Error: No image URLs provided."
    if len(urls) > MAX_PARTS:
        return f"Error: Maximum {MAX_PARTS} images per request."
    parts = [{"type": "image_url", "image_url": {"url": u}} for u in urls]
    return _chat(parts, prompt, 4096)


@mcp.tool(
    name="analyze_audio",
    description="Analyze a local audio file. Supports MP3, WAV, FLAC, M4A, OGG (Base64 up to 50MB).",
)
def analyze_audio(file_path: str, prompt: Optional[str] = None) -> str:
    data_uri, err = media_to_base64_data_uri(file_path, AUDIO_MIME_MAP, "audio")
    if err:
        return err
    return _chat(
        [{"type": "input_audio", "input_audio": {"data": data_uri}}],
        prompt or DEFAULT_AUDIO_PROMPT,
        2048,
    )


@mcp.tool(
    name="analyze_audio_url",
    description="Analyze audio from a public URL. Supports MP3, WAV, FLAC, M4A, OGG up to 100MB.",
)
def analyze_audio_url(url: str, prompt: Optional[str] = None) -> str:
    return _chat(
        [{"type": "input_audio", "input_audio": {"data": url}}],
        prompt or DEFAULT_AUDIO_PROMPT,
        2048,
    )


@mcp.tool(
    name="analyze_video",
    description=(
        "Analyze a local video file. Supports MP4, MOV, AVI, WMV (Base64 up to 50MB). "
        "fps in [0.1, 10], media_resolution 'default' or 'max'."
    ),
)
def analyze_video(
    file_path: str,
    prompt: Optional[str] = None,
    fps: float = 2.0,
    media_resolution: str = "default",
) -> str:
    err = validate_video_params(fps, media_resolution)
    if err:
        return err
    data_uri, err = media_to_base64_data_uri(file_path, VIDEO_MIME_MAP, "video")
    if err:
        return err
    return _chat(
        [{"type": "video_url", "video_url": {"url": data_uri}, "fps": fps, "media_resolution": media_resolution}],
        prompt or DEFAULT_VIDEO_PROMPT,
        4096,
    )


@mcp.tool(
    name="analyze_video_url",
    description=(
        "Analyze a video from a public URL. Supports MP4, MOV, AVI, WMV up to 300MB. "
        "fps in [0.1, 10], media_resolution 'default' or 'max'."
    ),
)
def analyze_video_url(
    url: str,
    prompt: Optional[str] = None,
    fps: float = 2.0,
    media_resolution: str = "default",
) -> str:
    err = validate_video_params(fps, media_resolution)
    if err:
        return err
    return _chat(
        [{"type": "video_url", "video_url": {"url": url}, "fps": fps, "media_resolution": media_resolution}],
        prompt or DEFAULT_VIDEO_PROMPT,
        4096,
    )
