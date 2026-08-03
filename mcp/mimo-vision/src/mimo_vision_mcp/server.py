"""MIMO Vision Understanding MCP Server.

Wraps Xiaomi MIMO multimodal API (mimo-v2.5 / mimo-v2.5-pro) as MCP tools for
Claude Code. Supports image, audio, and video understanding per the MiMo V2.5 docs.

Each analyze_* tool takes ``targets: list[str]`` — every item is a local file path
or a public URL, auto-detected by prefix (http/https/data = remote, passed through
with a HEAD size pre-check; anything else is treated as a local path and sent as
Base64). A single media is a one-element list; local and URL items may be mixed in
one call. ``prompt`` is required — the calling agent always states what to do.

All analyze_* tools return a structured dict aligned with the official response:
{
  "content": str,            # 最终结果（可能为空字符串）
  "finish_reason": str,      # 停止原因（stop/length/tool_calls/content_filter/...）
  "reasoning_content": str,  # 仅 thinking != 'disabled' 时返回：enabled 为占位串"已思考"；enabled_with_reasoning 为完整思考过程
  "role": str,               # 消息角色（assistant）
  "model": str,              # 模型名
  "usage": dict,             # 官方 usage 全量（含 completion/prompt tokens details、web_search_usage）
  "warning": str | None,     # 提示（如 content 为空但可改用 enabled_with_reasoning）
  "error": str | None,       # 错误信息（None 表示成功）
}
Noise fields from the raw response (id, created, object, tool_calls) are dropped.
"""
import base64
import os
import urllib.request
from pathlib import Path
from typing import Literal, Optional

from openai import OpenAI
from mcp.server import MCPServer

MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
DEFAULT_MIMO_MODEL = "mimo-v2.5"

DEFAULT_SYSTEM = (
    "You are MiMo, an AI assistant developed by Xiaomi. "
    "Analyze the provided media thoroughly and provide detailed, accurate descriptions."
)

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

# URL 传入大小上限（官方文档：图片 50MB / 音频 100MB / 视频 300MB）。
IMAGE_URL_MAX_MB = 50
AUDIO_URL_MAX_MB = 100
VIDEO_URL_MAX_MB = 300

DEFAULT_THINKING = "disabled"
THINKING_VALUES = ("disabled", "enabled", "enabled_with_reasoning")

_client: Optional[OpenAI] = None


def get_model() -> str:
    return os.environ.get("MIMO_MODEL", DEFAULT_MIMO_MODEL)


def get_thinking() -> str:
    """Resolve the default thinking mode from MIMO_THINKING env (registered at client config)."""
    return os.environ.get("MIMO_THINKING", DEFAULT_THINKING)


def get_max_completion_tokens() -> Optional[int]:
    """Resolve the default max_completion_tokens from MIMO_MAX_COMPLETION_TOKENS env.

    None 表示不传该参数（使用官方默认）；环境变量缺失或非法（非正整数）时同样返回 None。
    """
    raw = os.environ.get("MIMO_MAX_COMPLETION_TOKENS")
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw.strip())
    except ValueError:
        return None
    return value if value > 0 else None


def build_client() -> OpenAI:
    """Return a cached OpenAI client (created once, reused across calls)."""
    global _client
    if _client is not None:
        return _client
    key = os.environ.get("MIMO_API_KEY", "")
    if not key:
        raise RuntimeError(
            "MIMO_API_KEY environment variable is not set."
        )
    _client = OpenAI(api_key=key, base_url=MIMO_BASE_URL)
    return _client


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


def check_url_size(url: str, max_mb: int) -> Optional[str]:
    """Best-effort HEAD pre-check for URL media; returns error string or None.

    远程大小无法保证可靠获取（HEAD 可能被拒、Content-Length 可能缺失），
    检查失败时静默跳过，交由服务端兜底。
    """
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "mimo-vision-mcp")
        with urllib.request.urlopen(req, timeout=4) as resp:
            length = resp.headers.get("Content-Length")
            if length:
                total = int(length)
                if total > max_mb * 1024 * 1024:
                    return (
                        f"Error: URL media too large ({total / 1024 / 1024:.1f} MB); "
                        f"URL 传入上限为 {max_mb} MB."
                    )
    except Exception:
        pass
    return None


def validate_video_params(fps: float, media_resolution: str) -> Optional[str]:
    if not (0.1 <= fps <= 10):
        return f"Error: fps must be in range [0.1, 10], got {fps}."
    if media_resolution not in ("default", "max"):
        return f"Error: media_resolution must be 'default' or 'max', got {media_resolution!r}."
    return None


def build_sampling_kwargs(
    thinking: str, temperature: Optional[float], top_p: Optional[float]
) -> tuple[Optional[dict], Optional[str]]:
    """Build thinking + sampling kwargs for chat.completions.create.

    thinking 三态：disabled=禁用思维链；enabled / enabled_with_reasoning=启用。
    请求体始终是官方的 disabled/enabled 二值；enabled_with_reasoning 与 enabled 请求相同，
    区别仅在返回层。思考模式下 temperature/top_p 会被模型强制忽略（官方文档），仅 disabled 时传递。
    thinking 是 MiMo 的自定义顶层字段，OpenAI SDK 的 create() 签名没有该参数，
    必须经 extra_body 传入请求体，否则 TypeError。
    """
    if thinking not in THINKING_VALUES:
        return None, f"Error: thinking must be one of {THINKING_VALUES}, got {thinking!r}."
    kwargs: dict = {"extra_body": {"thinking": {"type": "enabled" if thinking != "disabled" else "disabled"}}}
    if thinking == "disabled":
        if temperature is not None:
            if not 0 <= temperature <= 1.5:
                return None, f"Error: temperature must be in range [0, 1.5], got {temperature}."
            kwargs["temperature"] = temperature
        if top_p is not None:
            if not 0.01 <= top_p <= 1.0:
                return None, f"Error: top_p must be in range [0.01, 1.0], got {top_p}."
            kwargs["top_p"] = top_p
    return kwargs, None


def _usage_dict(response) -> dict:
    """Return the full official usage object (all fields), or {} when absent."""
    u = getattr(response, "usage", None)
    if u is None:
        return {}
    dump = getattr(u, "model_dump", None)
    if dump:
        return dump()
    # 兜底：无 model_dump 时手动取主字段
    return {
        "prompt_tokens": getattr(u, "prompt_tokens", 0),
        "completion_tokens": getattr(u, "completion_tokens", 0),
        "total_tokens": getattr(u, "total_tokens", 0),
    }


def _error(message: str) -> dict:
    """Structured error result shared by all tools."""
    return {
        "content": "",
        "finish_reason": None,
        "role": "",
        "model": "",
        "usage": {},
        "warning": None,
        "error": message,
    }


def is_remote_source(target: str) -> bool:
    """True for http(s) URLs and data URIs; anything else is treated as a local path.

    data: 已编码串原样透传（不再 base64 重编码）。
    """
    lower = target.lower()
    return lower.startswith(("http://", "https://", "data:"))


def resolve_media_part(
    target: str,
    part_kind: str,
    mime_map: dict[str, str],
    label: str,
    url_max_mb: int,
    extra: Optional[dict] = None,
) -> tuple[Optional[dict], Optional[str]]:
    """Build a single content part from a local path or a public URL.

    远程（http/https/data）经 check_url_size 预检后直传；本地路径读取后转为
    Base64 data URI。part_kind: "image_url" / "input_audio" / "video_url" 决定
    part 结构；extra 是视频额外字段（fps、media_resolution）。
    返回 (part, None) 或 (None, error)。
    """
    if target.lower().startswith("file://"):
        return None, f"Error: pass a plain local path instead of a file:// URL: {target}"
    if is_remote_source(target):
        err = check_url_size(target, url_max_mb)
        if err:
            return None, err
        url = target
    else:
        data_uri, err = media_to_base64_data_uri(target, mime_map, label)
        if err:
            return None, err
        url = data_uri
    if part_kind == "image_url":
        return {"type": "image_url", "image_url": {"url": url}}, None
    if part_kind == "input_audio":
        return {"type": "input_audio", "input_audio": {"data": url}}, None
    # video_url
    return {"type": "video_url", "video_url": {"url": url}, **(extra or {})}, None


def resolve_media_parts(
    targets: list[str],
    part_kind: str,
    mime_map: dict[str, str],
    label: str,
    url_max_mb: int,
    extra: Optional[dict] = None,
) -> tuple[Optional[list[dict]], Optional[str]]:
    """Build content parts for a list of targets (local paths and/or URLs, mixed OK).

    逐项独立探测，任一失败即返回错误。
    返回 (parts, None) 或 (None, error)。
    """
    parts = []
    for target in targets:
        part, err = resolve_media_part(target, part_kind, mime_map, label, url_max_mb, extra)
        if err:
            return None, err
        parts.append(part)
    return parts, None


def _chat(
    media_parts: list[dict],
    prompt: str,
    max_completion_tokens: Optional[int] = None,
    thinking: Optional[Literal["disabled", "enabled", "enabled_with_reasoning"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
) -> dict:
    """Send one completion request with media + text parts, return a structured dict.

    max_completion_tokens=None 且未配置 MIMO_MAX_COMPLETION_TOKENS 时不传该参数，
    使用官方默认值（mimo-v2.5 为 32768，mimo-v2.5-pro 为 131072），避免人为截断输出。
    thinking=None 时用注册配置默认（MIMO_THINKING）。
    """
    if thinking is None:
        thinking = get_thinking()
    if max_completion_tokens is None:
        max_completion_tokens = get_max_completion_tokens()
    extra, err = build_sampling_kwargs(thinking, temperature, top_p)
    if err:
        return _error(err)
    try:
        client = build_client()
        kwargs = {
            "model": get_model(),
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM},
                {"role": "user", "content": [*media_parts, {"type": "text", "text": prompt}]},
            ],
        }
        if max_completion_tokens is not None:
            kwargs["max_completion_tokens"] = max_completion_tokens
        kwargs.update(extra)
        resp = client.chat.completions.create(**kwargs)
        choices = resp.choices
        if not choices:
            return _error("Empty choices in model response.")
        msg = choices[0].message
        content = (msg.content or "").strip()
        reasoning = (getattr(msg, "reasoning_content", None) or "").strip()
        base = {
            "content": content,
            "finish_reason": getattr(choices[0], "finish_reason", None),
            "role": getattr(msg, "role", "") or "",
            "model": getattr(resp, "model", "") or "",
            "usage": _usage_dict(resp),
            "warning": None,
            "error": None,
        }
        if thinking == "disabled":
            # disabled 模式模型不思考，reasoning_content 字段不返回。
            if not content:
                return {**base, "error": "Model returned empty content."}
            return base
        if thinking == "enabled":
            # 思考已发生但推理内容被丢弃，固定用占位串标注，不兜底。
            result = {**base, "reasoning_content": "已思考"}
            if content:
                return result
            return {
                **result,
                "warning": (
                    "思考模式下模型未在 content 中返回最终结果（content 为空）。"
                    "可改用 thinking='enabled_with_reasoning' 获取思考过程。"
                ),
            }
        # thinking == "enabled_with_reasoning"
        if not content and not reasoning:
            return {**base, "reasoning_content": "", "error": "Model returned empty content (content and reasoning_content are both empty)."}
        return {**base, "reasoning_content": reasoning}
    except Exception as e:
        return _error(f"{type(e).__name__}: {e}")


# 共享上下文：target 探测规则、大小限制、返回结构、采样参数语义。
# 各工具 description 只保留模态独有信息，避免重复。
mcp = MCPServer(
    "mimo-vision",
    instructions=(
        "MCP server for image/audio/video understanding via Xiaomi MIMO API "
        "(mimo-v2.5 / mimo-v2.5-pro). "
        "Every analyze_* tool takes targets: list[str] — each item is a local file "
        "path or a public URL, auto-detected by prefix (http/https/data = remote, "
        "passed through with a best-effort HEAD size check; otherwise treated as a "
        "local path and sent as Base64; file:// is not accepted — use a plain path). "
        "A single media is a one-element list, and local + URL items may be mixed in "
        "one call. prompt is required: state what to do with the media (describe, "
        "transcribe, compare, answer a question, ...). "
        "Size limits: image ≤50MB; audio URL ≤100MB, Base64 ≤50MB; video URL ≤300MB, "
        "Base64 ≤50MB; ≤10 media per call. "
        "All analyze_* tools return a structured dict: {content, finish_reason, role, "
        "model, usage (full official object), warning, error}, plus reasoning_content "
        "when thinking != 'disabled'. content is the final answer; finish_reason is "
        "the stop reason (stop/length/tool_calls/content_filter); reasoning_content is "
        "the literal '已思考' when thinking='enabled' (reasoning requested but not "
        "returned), or the full chain-of-thought when thinking='enabled_with_reasoning'. "
        "Shared sampling params on every analyze_* tool: thinking — default from "
        "MIMO_THINKING env (缺省 'disabled'); 'disabled' 不启用思维链; 'enabled' 启用但只返回最终结果; "
        "'enabled_with_reasoning' 启用并在 reasoning_content 返回思考过程。temperature [0,1.5] 与 "
        "top_p [0.01,1.0] 仅 thinking='disabled' 时生效。max_completion_tokens 正整数，"
        "未传时用注册配置默认（MIMO_MAX_COMPLETION_TOKENS，缺省不传即官方默认）。"
    ),
)


@mcp.tool(
    name="analyze_image",
    description=(
        "Analyze one or more images from local file paths or public URLs. "
        "targets is a list; a single image is a one-element list; local paths and URLs "
        "can be mixed. Supports JPEG/PNG/GIF/WebP/BMP, each ≤50MB, up to 10 images. "
        "Pass a prompt describing what to do, e.g. '请详细描述这张图片' or '请对比这两张图片'. "
        "Shared sampling params are in the server instructions."
    ),
)
def analyze_image(
    targets: list[str],
    prompt: str,
    thinking: Optional[Literal["disabled", "enabled", "enabled_with_reasoning"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_completion_tokens: Optional[int] = None,
) -> dict:
    if not targets:
        return _error("No image targets provided.")
    if len(targets) > MAX_PARTS:
        return _error(f"Maximum {MAX_PARTS} images per request.")
    parts, err = resolve_media_parts(
        targets, "image_url", IMAGE_MIME_MAP, "image", IMAGE_URL_MAX_MB
    )
    if err:
        return _error(err)
    return _chat(
        parts, prompt,
        thinking=thinking, temperature=temperature, top_p=top_p,
        max_completion_tokens=max_completion_tokens,
    )


@mcp.tool(
    name="analyze_audio",
    description=(
        "Analyze one or more audio files from local file paths or public URLs. "
        "targets is a list; a single audio is a one-element list; local paths and URLs "
        "can be mixed. Supports MP3/WAV/FLAC/M4A/OGG; URL ≤100MB, local Base64 ≤50MB; "
        "up to 10 files. Pass a prompt describing what to do, e.g. '请详细描述这段音频' "
        "or '请对比这两段音频'. Shared sampling params are in the server instructions."
    ),
)
def analyze_audio(
    targets: list[str],
    prompt: str,
    thinking: Optional[Literal["disabled", "enabled", "enabled_with_reasoning"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_completion_tokens: Optional[int] = None,
) -> dict:
    if not targets:
        return _error("No audio targets provided.")
    if len(targets) > MAX_PARTS:
        return _error(f"Maximum {MAX_PARTS} audio files per request.")
    parts, err = resolve_media_parts(
        targets, "input_audio", AUDIO_MIME_MAP, "audio", AUDIO_URL_MAX_MB
    )
    if err:
        return _error(err)
    return _chat(
        parts, prompt,
        thinking=thinking, temperature=temperature, top_p=top_p,
        max_completion_tokens=max_completion_tokens,
    )


@mcp.tool(
    name="analyze_video",
    description=(
        "Analyze one or more videos from local file paths or public URLs. "
        "targets is a list; a single video is a one-element list; local paths and URLs "
        "can be mixed. Supports MP4/MOV/AVI/WMV; URL ≤300MB, local Base64 ≤50MB; up to "
        "10 videos. fps in [0.1, 10] (default 2); media_resolution 'default' or 'max' "
        "(default 'default'); both apply to every video in the list. Pass a prompt "
        "describing what to do, e.g. '请详细描述这段视频'. Shared sampling params are in "
        "the server instructions."
    ),
)
def analyze_video(
    targets: list[str],
    prompt: str,
    fps: float = 2.0,
    media_resolution: str = "default",
    thinking: Optional[Literal["disabled", "enabled", "enabled_with_reasoning"]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_completion_tokens: Optional[int] = None,
) -> dict:
    err = validate_video_params(fps, media_resolution)
    if err:
        return _error(err)
    if not targets:
        return _error("No video targets provided.")
    if len(targets) > MAX_PARTS:
        return _error(f"Maximum {MAX_PARTS} videos per request.")
    parts, err = resolve_media_parts(
        targets, "video_url", VIDEO_MIME_MAP, "video", VIDEO_URL_MAX_MB,
        extra={"fps": fps, "media_resolution": media_resolution},
    )
    if err:
        return _error(err)
    return _chat(
        parts, prompt,
        thinking=thinking, temperature=temperature, top_p=top_p,
        max_completion_tokens=max_completion_tokens,
    )


@mcp.tool(
    name="estimate_video_tokens",
    description=(
        "Estimate the input token usage of a video before calling analyze_video, based on the "
        "official MiMo estimate_video_tokens algorithm. fps in [0.1, 10]; media_resolution "
        "'default' or 'max'; mute=True skips the audio token part. Result is an estimate; "
        "actual usage is returned in the API response."
    ),
)
def estimate_video_tokens(
    duration: float,
    width: int,
    height: int,
    fps: float = 2.0,
    media_resolution: str = "default",
    mute: bool = False,
) -> int:
    """Estimate MiMo video input token usage (official algorithm, docs/video-understanding)."""
    if duration <= 0 or width <= 0 or height <= 0:
        raise ValueError("duration, width and height must be positive.")
    if not 0.1 <= fps <= 10:
        raise ValueError("fps must be in range [0.1, 10].")
    if media_resolution not in ("default", "max"):
        raise ValueError("media_resolution must be 'default' or 'max'.")

    import math

    PATCH, MERGE, T_PATCH = 16, 2, 2
    SPATIAL = PATCH * MERGE                         # 32
    PIX_PER_TOKEN = SPATIAL ** 2                    # 1024
    MAX_TOTAL_TOKENS = 131072
    TOTAL_MAX_PIX = MAX_TOTAL_TOKENS * PIX_PER_TOKEN
    MIN_PIX, MAX_PIX = 8192, 8388608
    MAX_FRAMES = 2048
    DEFAULT_MAX_FRAME_TOKEN = 300

    # 1. 抽帧数
    nframes = math.ceil(duration * fps)
    nframes = min(nframes, MAX_FRAMES)
    nframes = max(math.ceil(nframes / T_PATCH) * T_PATCH, T_PATCH)

    # 2. 单帧像素预算
    max_pix = TOTAL_MAX_PIX * T_PATCH // nframes
    if media_resolution != "max":
        max_pix = min(max_pix, DEFAULT_MAX_FRAME_TOKEN * PIX_PER_TOKEN)
    max_pix = max(MIN_PIX, min(max_pix, MAX_PIX))

    # 3. 缩放分辨率
    h, w = height, width
    if min(h, w) < SPATIAL:
        if h < w:
            w = int(w * SPATIAL / h); h = SPATIAL
        else:
            h = int(h * SPATIAL / w); w = SPATIAL
    h_bar = round(h / SPATIAL) * SPATIAL
    w_bar = round(w / SPATIAL) * SPATIAL
    if h_bar * w_bar > max_pix:
        beta = math.sqrt(h * w / max_pix)
        h_bar = math.floor(h / beta / SPATIAL) * SPATIAL
        w_bar = math.floor(w / beta / SPATIAL) * SPATIAL
    elif h_bar * w_bar < MIN_PIX:
        beta = math.sqrt(MIN_PIX / (h * w))
        h_bar = math.ceil(h * beta / SPATIAL) * SPATIAL
        w_bar = math.ceil(w * beta / SPATIAL) * SPATIAL

    # 4. Token 计算
    grids = nframes // T_PATCH                       # 时序网格数
    tokens_per_grid = (h_bar // PATCH) * (w_bar // PATCH) // (MERGE ** 2)
    vision = grids * tokens_per_grid
    timestamps = grids * (5 if fps > 2 else 3)       # 时间戳文本 token
    special = grids * 2 + 2                           # 特殊标记

    # 5. 音频 Token
    audio = 0
    if not mute:
        spec_len = int(duration * 24000) // 240 + 1
        t = (spec_len - 1) // 2 + 1
        t = t // 2 + int(t % 2 != 0)
        audio = math.ceil(t / 4) + 2                 # +2 for audio special tokens

    return vision + timestamps + special + audio
