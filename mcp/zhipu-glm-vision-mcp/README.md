# zhipu-glm-vision-mcp

基于智谱 GLM-4.6V-Flash（免费多模态视觉模型）的多模态理解 MCP 服务，支持图片、视频、文件三类理解能力，并支持思考模式（thinking）开关。

GLM-4.6V-Flash 上下文窗口 128K，在视觉理解精度上达到同参数规模 SOTA，原生支持多模态 Function Calling。本服务通过智谱 OpenAI 兼容接口接入，遵循 **MCP v2 协议**（`mcp>=2.0.0` + `MCPServer`）。

## 使用

```bash
uvx zhipu-glm-vision-mcp
```

需要设置环境变量 `ZHIPU_API_KEY`（在 [智谱开放平台](https://open.bigmodel.cn) 免费获取）。

可选环境变量：

| 变量 | 说明 | 默认 |
|---|---|---|
| `ZHIPU_API_KEY` | 智谱 API Key（必需） | - |
| `GLM_MODEL` | 模型名称 | `glm-4.6v-flash` |
| `GLM_THINKING` | 思考模式默认，取值与工具 `thinking` 参数一致（`disabled` / `enabled` / `enabled_with_reasoning`；兼容布尔写法 `true`/`false`） | `disabled` |

CLI 参数：`--model <名称>` 覆盖模型、`--transport/-t stdio|streamable-http|sse`（默认 stdio）、`--thinking` / `--no-thinking` / `--reasoning` 设置思考默认（分别对应 `enabled` / `disabled` / `enabled_with_reasoning`）。

## 工具

每个工具均接受**列表参数**（传 1 个即单条分析，传多个即在同一上下文内对比/关联分析），并支持 `thinking` 思考开关与 `prompt` 自定义提问。

> 本地 Base64 传入**仅图片支持**（官方契约）；视频/文件仅支持公网 URL 传入（`file_url` 官方明确不支持 Base64）。因此视频/文件只提供 `*_url` 工具。

### 图片理解
- `analyze_image(file_paths: list, prompt?, thinking?)` - 分析 1..50 个本地图片路径（JPEG/PNG，每张 Base64 ≤5MB、≤6000×6000）
- `analyze_image_url(urls: list, prompt?, thinking?)` - 分析 1..50 个公网图片 URL（JPEG/PNG）

### 视频理解
- `analyze_video_url(urls: list, prompt?, thinking?)` - 分析 1..N 个公网视频 URL（MP4/MKV/MOV，每个 ≤200MB，数量不设上限）

### 文件/文档理解
- `analyze_file_url(urls: list, prompt?, thinking?)` - 分析 1..50 个公网文件 URL（PDF/TXT/Word/DOCX/JSONL/XLSX/PPTX），支持多文档跨文档对比

### 可选参数

每个工具都接受以下**可选参数**：

| 参数 | 类型 | 说明 | 默认 |
|---|---|---|---|
| `prompt` | string | 自定义提问，覆盖默认提示词 | 按模态的默认中文提示词（描述/分析/总结） |
| `thinking` | string | 三态思考模式，见下 | 回落 `GLM_THINKING` 环境变量，再默认 `disabled` |

**必选参数**：
- `file_paths`：本地图片路径列表，用于 `analyze_image`
- `urls`：公网 URL 列表，用于 `analyze_image_url` / `analyze_video_url` / `analyze_file_url`

**`thinking` 三态**：

| 取值 | 行为 |
|---|---|
| `"disabled"` | 关闭思考，只返回最终答案 |
| `"enabled"` | 开启思考，不返回思考链 |
| `"enabled_with_reasoning"` | 开启思考，并返回思考链（`【思考过程】…\n【回答】…`） |

**优先级**：单次调用 `thinking` 参数 > `GLM_THINKING` 环境变量（可用 CLI `--reasoning`/`--thinking`/`--no-thinking` 或启动前设置）> 默认 `disabled`。

开启思考后模型会先进行深度推理再作答，理解更细致但响应更慢；免费 flash 版默认关闭以换取更快响应。

**示例**：

```text
analyze_image(file_paths=["a.png", "b.png"], prompt="这两张图有什么区别？", thinking="enabled_with_reasoning")
analyze_file_url(urls=["https://.../report.pdf"], thinking="enabled")
analyze_video_url(urls=["https://.../clip.mp4"])
```

## 媒体限制

对齐官方契约（`docs/model-api-raw.md`）：

- **模态互斥**：图片、视频、文件三者互斥，单次请求只能分析一种模态（GLM-4.6V 限制），因此拆分为独立工具。
- **传入方式**：图片支持公网 URL 或本地 Base64 data URI；视频/文件**仅支持公网 URL**（`file_url` 官方明确不支持 Base64，`video_url` 官方仅描述 URL）。
- **数量上限**：图片最多 50 张；文件最多 50 个；视频官方未限制数量，不设上限。
- **大小上限**：图片单张 ≤5MB 且像素 ≤6000×6000；视频单个 ≤200MB。
- **格式**：图片 JPEG/PNG；视频 MP4/MKV/MOV；文件 PDF/TXT/Word/DOCX/JSONL/XLSX/PPTX。
- 输出模态为纯文本；上下文窗口 128K。

## 客户端注册

Claude Code：

```bash
claude mcp add zhipu-glm-vision-mcp \
  -e ZHIPU_API_KEY=你的Key \
  -- uvx zhipu-glm-vision-mcp
```

`.mcp.json` / `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "zhipu-glm-vision-mcp": {
      "command": "uvx",
      "args": ["zhipu-glm-vision-mcp"],
      "env": {
        "ZHIPU_API_KEY": "你的Key"
      }
    }
  }
}
```

## 发布新版本

1. 修改 `pyproject.toml` 中的 `version`（必须严格递增）
2. `uv build`，生成 `dist/*.whl` 与 `dist/*.tar.gz`
3. `twine upload dist/*`，按提示粘贴 PyPI API Token（用户名填 `__token__`）
4. 验证：`uvx zhipu-glm-vision-mcp --help`

## 相关文档

`docs/` 目录存放了 GLM-4.6V-Flash 相关文档：

- [GLM-4.6V-Flash API 参考快照](docs/glm-4.6v-flash.md) - 精简 API 契约（端点 / 请求格式 / 已知限制）
- [GLM-4.6V-Flash 原始官方文档](docs/glm-4.6v-flash-raw.md) - 官方完整能力文档原样存档

## License

MIT
