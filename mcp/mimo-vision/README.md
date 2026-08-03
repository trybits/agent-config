# mimo-vision-mcp

基于小米 MIMO API（mimo-v2.5 / mimo-v2.5-pro）的多模态理解 MCP 服务，支持图片、音频、视频三类理解能力。


## 使用

```bash
uvx mimo-vision-mcp
```

### 注册配置

在 MCP 客户端的 server 配置（如 `.mcp.json`）中注册 `mimo-vision-mcp`。每个配置项有两种等价写法：`args`（命令行参数 `--xxx`）或 `env`（环境变量 `MIMO_XXX`），**二选一即可**；都填时 `--xxx` 优先。

| 配置 | 必填/可选 | 默认值 | 说明 |
|---|---|---|---|
| `env.MIMO_API_KEY` | **必填** | — | API 密钥，缺失启动报错 |
| `env.MIMO_MODEL` 或 `--model <名称>` | 可选 | `mimo-v2.5` | 模型名（`mimo-v2.5` / `mimo-v2.5-pro`） |
| `env.MIMO_THINKING` 或 `--thinking <值>` | 可选 | `disabled` | 默认思维模式（`disabled` / `enabled` / `enabled_with_reasoning`） |
| `env.MIMO_MAX_COMPLETION_TOKENS` 或 `--max-completion-tokens <正整数>` | 可选 | 不传（官方默认：`mimo-v2.5` 32768 / `mimo-v2.5-pro` 131072） | 输出 token 上限 |

**写法 A：全部用命令行参数（`args`）**

```json
{
  "mcpServers": {
    "mimo-vision": {
      "command": "uvx",
      "args": ["mimo-vision-mcp", "--model", "mimo-v2.5-pro", "--thinking", "enabled"],
      "env": { "MIMO_API_KEY": "sk-xxx" }
    }
  }
}
```

**写法 B：全部用环境变量（`env`）**

```json
{
  "mcpServers": {
    "mimo-vision": {
      "command": "uvx",
      "args": ["mimo-vision-mcp"],
      "env": {
        "MIMO_API_KEY": "sk-xxx",
        "MIMO_MODEL": "mimo-v2.5-pro",
        "MIMO_THINKING": "enabled_with_reasoning",
        "MIMO_MAX_COMPLETION_TOKENS": "8192"
      }
    }
  }
}
```

> 两种写法等价，选一种风格即可。仅 `MIMO_API_KEY` 必填，其余可选（不配用默认值）。

**参数优先级**（对 `thinking` / `max_completion_tokens`）：

```
工具调用显式传参  >  --xxx 命令行参数  >  $MIMO_XXX 环境变量  >  内置默认值
```

## 工具

所有 `analyze_*` 工具统一接受 `targets` 列表：每项为本地文件路径或公网 URL（按前缀自动识别，见下），单张媒体传单元素列表（`["a.png"]`），本地与 URL 可混合；`prompt` **必填**，由调用方指定要模型做什么（描述、转写、对比、问答均可）。

### 图片理解
- `analyze_image(targets, prompt, thinking?, temperature?, top_p?, max_completion_tokens?)` - 分析一张或多张图片（JPEG/PNG/GIF/WebP/BMP，单张 ≤50MB，最多 10 张）

### 音频理解
- `analyze_audio(targets, prompt, thinking?, temperature?, top_p?, max_completion_tokens?)` - 分析一段或多段音频（MP3/WAV/FLAC/M4A/OGG，URL ≤100MB、Base64 ≤50MB，最多 10 段）

### 视频理解
- `analyze_video(targets, prompt, fps?, media_resolution?, thinking?, temperature?, top_p?, max_completion_tokens?)` - 分析一个或多个视频（MP4/MOV/AVI/WMV，URL ≤300MB、Base64 ≤50MB，最多 10 个）
- `estimate_video_tokens(duration, width, height, fps?, media_resolution?, mute?)` - 按官方算法估算视频输入 Token 数（估算仅供参考，实际用量以 API 响应为准）

视频参数：
- `fps`：抽帧率，默认 2，范围 [0.1, 10]，越高时序细节越精细、Token 越多；作用于列表内全部视频
- `media_resolution`：`"default"`（平衡效果与效率）或 `"max"`（提升小物体/细节识别）

采样参数（所有分析工具通用）：
- `thinking`：不传时用注册配置默认（`MIMO_THINKING` 环境变量，缺省 `"disabled"`）。`"disabled"` 不启用思维链；`"enabled"` 启用思维链但返回中丢弃思考过程（若模型未在 `content` 返回结果，会给出提示，不兜底）；`"enabled_with_reasoning"` 启用思维链，并在返回的 `reasoning_content` 字段给出思考过程
- `temperature`：范围 [0, 1.5]，仅 `thinking="disabled"` 时生效
- `top_p`：范围 [0.01, 1.0]，仅 `thinking="disabled"` 时生效
- `max_completion_tokens`：可选正整数，限制输出 token 上限；不传时用注册配置默认（`MIMO_MAX_COMPLETION_TOKENS`，缺省不传，即官方默认：`mimo-v2.5` 为 32768、`mimo-v2.5-pro` 为 131072）

### 返回结构

所有 `analyze_*` 工具返回结构化 dict，字段对齐官方响应，屏蔽 `id`/`created`/`object`/`tool_calls` 等噪音字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `content` | string | 最终结果（可能为空字符串） |
| `finish_reason` | string \| null | 停止原因（`stop` / `length` / `tool_calls` / `content_filter`…） |
| `reasoning_content` | string | 仅 `thinking != "disabled"` 时返回：`"enabled"` 为占位串 `"已思考"`；`"enabled_with_reasoning"` 为完整思考过程 |
| `role` | string | 消息角色（`assistant`） |
| `model` | string | 模型名 |
| `usage` | object | 官方 `usage` 全量返回（含 `completion_tokens_details` / `prompt_tokens_details` / `web_search_usage` 等） |
| `warning` | string \| null | 提示（如 content 为空但可改用 `enabled_with_reasoning`） |
| `error` | string \| null | 错误信息（`null` 表示成功） |

示例（`thinking="enabled_with_reasoning"`）：

```json
{
  "content": "视频画面是一只毛茸茸的白色小猫...",
  "finish_reason": "stop",
  "reasoning_content": "1. 分析视频主体...\n2. 描述场景...",
  "role": "assistant",
  "model": "mimo-v2.5",
  "usage": {
    "completion_tokens": 849,
    "prompt_tokens": 1260,
    "total_tokens": 2109,
    "completion_tokens_details": {"reasoning_tokens": 719},
    "prompt_tokens_details": {"video_tokens": 1144, "cached_tokens": 1256, "audio_tokens": 19},
    "web_search_usage": {"tool_usage": 2, "page_usage": 8}
  },
  "warning": null,
  "error": null
}
```

## 媒体限制

`targets` 每项可为本地路径（自动读文件转 Base64）或公网 URL（HEAD 预检大小后直传），两者可混合。

| 模态 | 支持格式 | URL 大小 | Base64 大小 | 多输入 |
|---|---|---|---|---|
| 图片 | JPEG / PNG / GIF / WebP / BMP | ≤50MB | ≤50MB | 最多 10 张 |
| 音频 | MP3 / WAV / FLAC / M4A / OGG | ≤100MB | ≤50MB | 最多 10 个 |
| 视频 | MP4 / MOV / AVI / WMV | ≤300MB | ≤50MB | 最多 10 个 |

注：Base64 传入时单个文件不超过 50MB；音频/视频不支持 files API 本地文件上传，仅支持 URL 或 Base64 编码传入（本地文件由本服务自动转 Base64）。`file://` 前缀不接受，请直接传本地路径。

## 相关文档

`docs/` 目录存放了 MiMo V2.5 官方能力文档的离线快照与抓取方法：

- [图片理解](docs/capabilities/image-understanding.md)
- [音频理解](docs/capabilities/audio-understanding.md)
- [视频理解](docs/capabilities/video-understanding.md)
- [OpenAI Chat Completions API（兼容接口）](docs/api/openai-api.md)
- [官方文档抓取与转换说明](docs/capture-and-conversion.md)

官方在线文档：<https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/multimodal-understanding/image-understanding>

## License

MIT
