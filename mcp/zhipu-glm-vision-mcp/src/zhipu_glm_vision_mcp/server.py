"""GLM-4.6V-Flash Vision Understanding MCP Server.

Wraps Zhipu GLM-4.6V-Flash multimodal API as MCP tools for Claude Code.
Supports image, video, and file understanding with optional thinking mode.

Tool design notes:
- One tool per modality (image / video / file) because the API forbids mixing
  modalities in a single request ("不支持同时理解文件、视频和图像").
- Local Base64 data URI is supported ONLY for images (official contract);
  video and file are URL-only (file_url explicitly "不支持Base64编码"). Hence
  the local-path tools exist for image only; video/file use *_url tools.
- Each tool accepts a list of 1..N items (local paths or public URLs), so a
  single media item and a multi-item comparison are both covered by one tool.
- Limits align with official docs (model-api-raw.md): image ≤5MB/≤50 items,
  file ≤50 items, video size ≤200MB each with unbounded count.
- `thinking` is a tri-state parameter: "disabled" / "enabled" /
  "enabled_with_reasoning" (thinking + return the reasoning chain).
"""
import base64
import os
from pathlib import Path
from typing import Literal, Optional

from openai import OpenAI
from mcp.server import MCPServer

ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
DEFAULT_GLM_MODEL = "glm-4.6v-flash"

DEFAULT_SYSTEM = (
    "You are GLM-4.6V, a multimodal AI assistant developed by Zhipu AI. "
    "Analyze the provided media thoroughly and provide detailed, accurate answers."
)
DEFAULT_IMAGE_PROMPT = (
    "请详细分析提供的图片内容，包括其中的物体、文字、场景、颜色、布局等所有可见信息。"
    "若有多张图片，请分别描述并指出它们的联系与区别。"
)
DEFAULT_VIDEO_PROMPT = (
    "请详细分析提供的视频内容，包括画面、动作、场景、文字以及音频等所有可见可听信息。"
    "若有多个视频，请分别描述并指出它们的联系与区别。"
)
DEFAULT_FILE_PROMPT = (
    "请详细阅读并分析提供的文件内容，包括关键信息、结构和要点。"
    "若有多个文件，请分别总结并指出它们的联系与区别。"
)

THINKING_DISABLED = "disabled"
THINKING_ENABLED = "enabled"
THINKING_REASONING = "enabled_with_reasoning"
THINKING_MODES = (THINKING_DISABLED, THINKING_ENABLED, THINKING_REASONING)

# MIME 列表严格对齐官方契约（docs/model-api-raw.md）：
# - 图片 jpg/png/jpeg；视频 mp4/mkv/mov；文件 pdf/txt/word/jsonl/xlsx/pptx。
# - 视频/文件仅支持 URL 传入（官方明确 file_url 不支持 Base64），本地路径版
#   已移除，video/file 的 MIME map 仅保留官方列表供文档/校验参考。
IMAGE_MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
VIDEO_MIME_MAP = {
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
}
FILE_MIME_MAP = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".jsonl": "application/jsonl",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

# 官方限制（docs/model-api-raw.md + 官方对话补全 API 参考）：
# - 图片：Base64 单张 ≤5MB 且像素 ≤6000×6000，最多 50 张。
# - 视频：仅 URL 传入，单个 ≤200MB；官方未限制数量上限，故不设数量检查。
# - 文件：仅 URL 传入，最多 50 个。
IMAGE_MAX_MB = 5
IMAGE_MAX_PARTS = 50
FILE_MAX_PARTS = 50
MAX_OUTPUT_TOKENS = 4096


def get_model() -> str:
    return os.environ.get("GLM_MODEL", DEFAULT_GLM_MODEL)


def get_thinking_mode() -> str:
    """Read the default thinking mode from the GLM_THINKING env var.

    Accepts the tri-state values ("disabled"/"enabled"/"enabled_with_reasoning")
    and, for backward compatibility, boolean-like values ("true"/"1"/"yes"/"on").
    """
    val = os.environ.get("GLM_THINKING", "").strip().lower()
    if val in THINKING_MODES:
        return val
    if val in ("1", "true", "yes", "on"):
        return THINKING_ENABLED
    return THINKING_DISABLED


def build_client() -> OpenAI:
    key = os.environ.get("ZHIPU_API_KEY", "")
    if not key:
        raise RuntimeError(
            "ZHIPU_API_KEY environment variable is not set. "
            "Get a free key at https://open.bigmodel.cn."
        )
    return OpenAI(api_key=key, base_url=ZHIPU_BASE_URL)


def media_to_base64_data_uri(
    path_str: str, mime_map: dict[str, str], label: str, max_mb: int
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
    if size > max_mb * 1024 * 1024:
        return None, (
            f"Error: {label} file too large "
            f"({size / 1024 / 1024:.1f} MB); Base64 传入上限为 {max_mb} MB."
        )
    mime = mime_map.get(path.suffix.lower())
    if not mime:
        return None, (
            f"Error: Unsupported {label} file type '{path.suffix or '(no extension)'}'. "
            f"Supported: {', '.join(sorted(mime_map))}"
        )
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}", None


def media_parts_from_paths(
    paths: list[str], mime_map: dict[str, str], label: str, part_type: str,
    max_parts: int, max_mb: int,
) -> tuple[list[dict], Optional[str]]:
    """Build API media parts from local file paths.

    Returns (parts, error); exactly one of the two is not None.
    """
    if not paths:
        return [], f"Error: No {label} paths provided."
    if len(paths) > max_parts:
        return [], f"Error: Maximum {max_parts} {label}s per request."
    parts = []
    for p in paths:
        data_uri, err = media_to_base64_data_uri(p, mime_map, label, max_mb)
        if err:
            return [], err
        parts.append({"type": part_type, part_type: {"url": data_uri}})
    return parts, None


def media_parts_from_urls(
    urls: list[str], label: str, part_type: str, max_parts: Optional[int]
) -> tuple[list[dict], Optional[str]]:
    """Build API media parts from public URLs.

    `max_parts` limits the item count; pass None to skip the count check
    (e.g. video, whose count is unbounded per official docs).

    Returns (parts, error); exactly one of the two is not None.
    """
    if not urls:
        return [], f"Error: No {label} URLs provided."
    if max_parts is not None and len(urls) > max_parts:
        return [], f"Error: Maximum {max_parts} {label}s per request."
    return [{"type": part_type, part_type: {"url": u}} for u in urls], None


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


def resolve_thinking_mode(thinking: Optional[str]) -> str:
    """Resolve the tri-state thinking mode from the per-call value or env default."""
    if thinking is not None:
        return thinking
    return get_thinking_mode()


def _reasoning_to_text(val) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return "".join(
            str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in val
        )
    return str(val)


def _get_reasoning_content(message) -> str:
    """Extract reasoning_content from an OpenAI-SDK-parsed message with fallbacks."""
    try:
        val = getattr(message, "reasoning_content", None)
        if val:
            return _reasoning_to_text(val)
    except Exception:
        pass
    try:
        extra = getattr(message, "model_extra", None) or {}
        val = extra.get("reasoning_content")
        if val:
            return _reasoning_to_text(val)
    except Exception:
        pass
    try:
        val = message.model_dump().get("reasoning_content")
        if val:
            return _reasoning_to_text(val)
    except Exception:
        pass
    return ""


def _chat(
    media_parts: list[dict],
    prompt: str,
    max_tokens: int,
    thinking: Optional[str] = None,
) -> str:
    """Send one completion request with media + text parts, return the text result.

    `thinking` is tri-state: "disabled" / "enabled" / "enabled_with_reasoning".
    """
    mode = resolve_thinking_mode(thinking)
    if mode not in THINKING_MODES:
        return (
            f"Error: thinking must be one of {THINKING_MODES}, got {thinking!r}."
        )
    try:
        client = build_client()
        resp = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": DEFAULT_SYSTEM},
                {"role": "user", "content": [*media_parts, {"type": "text", "text": prompt}]},
            ],
            max_tokens=max_tokens,
            extra_body={
                "thinking": {
                    "type": "enabled" if mode != THINKING_DISABLED else "disabled"
                }
            },
        )
        message = resp.choices[0].message
        content = message.content
        if content is None:
            return "Error: No content in model response."
        out = ""
        if mode == THINKING_REASONING:
            reasoning = _get_reasoning_content(message)
            if reasoning:
                out += f"【思考过程】\n{reasoning}\n\n"
        out += content
        return out + token_info(resp)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


mcp = MCPServer(
    "zhipu-glm-vision-mcp",
    instructions="MCP server for image/video/file understanding via Zhipu GLM-4.6V-Flash API.",
)

THINKING_HINT = (
    "thinking: 'disabled' (no thinking), 'enabled' (thinking, no chain), "
    "'enabled_with_reasoning' (thinking + return the reasoning chain). "
    "Default: $GLM_THINKING env, else 'disabled'."
)

Thinking = Optional[Literal["disabled", "enabled", "enabled_with_reasoning"]]


@mcp.tool(
    name="analyze_image",
    description=(
        "Analyze one or more local image files in a single request. Pass a list of 1..50 file "
        "paths (a single image is a list of one); multiple images are analyzed together for "
        "comparison. Supports JPEG, PNG (each Base64 up to 5MB, ≤6000x6000). "
        + THINKING_HINT
    ),
)
def analyze_image(
    file_paths: list[str],
    prompt: Optional[str] = None,
    thinking: Thinking = None,
) -> str:
    parts, err = media_parts_from_paths(
        file_paths, IMAGE_MIME_MAP, "image", "image_url", IMAGE_MAX_PARTS, IMAGE_MAX_MB
    )
    if err:
        return err
    return _chat(parts, prompt or DEFAULT_IMAGE_PROMPT, MAX_OUTPUT_TOKENS, thinking)


@mcp.tool(
    name="analyze_image_url",
    description=(
        "Analyze one or more images from public URLs in a single request. Pass a list of 1..50 "
        "URLs (a single image is a list of one); multiple images are analyzed together for "
        "comparison. Supports JPEG, PNG. "
        + THINKING_HINT
    ),
)
def analyze_image_url(
    urls: list[str],
    prompt: Optional[str] = None,
    thinking: Thinking = None,
) -> str:
    parts, err = media_parts_from_urls(urls, "image", "image_url", IMAGE_MAX_PARTS)
    if err:
        return err
    return _chat(parts, prompt or DEFAULT_IMAGE_PROMPT, MAX_OUTPUT_TOKENS, thinking)


@mcp.tool(
    name="analyze_video_url",
    description=(
        "Analyze one or more videos from public URLs in a single request. Pass a list of 1..N "
        "URLs (a single video is a list of one); count is not capped (official API limits video "
        "size to ≤200MB each but not the count). Supports MP4, MKV, MOV. Video supports URL "
        "input only (no local Base64). "
        + THINKING_HINT
    ),
)
def analyze_video_url(
    urls: list[str],
    prompt: Optional[str] = None,
    thinking: Thinking = None,
) -> str:
    parts, err = media_parts_from_urls(urls, "video", "video_url", None)
    if err:
        return err
    return _chat(parts, prompt or DEFAULT_VIDEO_PROMPT, MAX_OUTPUT_TOKENS, thinking)


@mcp.tool(
    name="analyze_file_url",
    description=(
        "Analyze one or more files from public URLs in a single request. Pass a list of 1..50 "
        "URLs (a single file is a list of one); multiple files are analyzed together for "
        "cross-document comparison. Supports PDF, TXT, Word, JSONL, XLSX, PPTX. File supports "
        "URL input only (official API does not accept Base64 for files). "
        + THINKING_HINT
    ),
)
def analyze_file_url(
    urls: list[str],
    prompt: Optional[str] = None,
    thinking: Thinking = None,
) -> str:
    parts, err = media_parts_from_urls(urls, "file", "file_url", FILE_MAX_PARTS)
    if err:
        return err
    return _chat(parts, prompt or DEFAULT_FILE_PROMPT, MAX_OUTPUT_TOKENS, thinking)
