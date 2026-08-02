# doubao-search-mcp

基于火山引擎**豆包联网搜索 API** 的 MCP 服务，提供 `web_search` 工具（网页 / 图片搜索），帮助大模型 / AI Agent 获取更准确、更新鲜的外部信息。

> 本包复刻自火山官方 [`volcengine/mcp-server`](https://github.com/volcengine/mcp-server) 的 `mcp_server_askecho_search_infinity`（MIT 协议），修复了 mcp SDK 2.x 下的导入崩溃问题，并独立发布到 PyPI。

## 功能

提供 `web_search` 工具：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `Query` | str | — | 搜索 query，1~100 个字符（必填） |
| `Count` | int | 10 | 返回条数；web 最多 50，image 最多 5 |
| `SearchType` | str | `web` | 仅支持 `web` 或 `image` |
| `TimeRange` | str | 空 | `OneDay`/`OneWeek`/`OneMonth`/`OneYear` 或日期区间 `YYYY-MM-DD..YYYY-MM-DD` |
| `AuthLevel` | int | 0 | 权威等级过滤；0 默认，1 非常权威 |

## 安装运行

需要 Python 3.12 / 3.13 与 [uv](https://docs.astral.sh/uv/)。

```bash
# 免安装直接运行（首次自动从 PyPI 拉取）
uvx doubao-search-mcp

# 或安装成常驻工具
uv tool install doubao-search-mcp
doubao-search-mcp
```

### 传输方式

默认 stdio；也支持 SSE / streamable-http：

```bash
uvx doubao-search-mcp -t sse
uvx doubao-search-mcp -t streamable-http
```

## 鉴权

**二选一**，通过环境变量提供（两者都不配置会启动失败，日志提示 Authentication missing）：

| 方式 | 环境变量 |
|---|---|
| API Key | `ASK_ECHO_SEARCH_INFINITY_API_KEY` |
| 火山引擎 AK/SK | `VOLCENGINE_ACCESS_KEY` + `VOLCENGINE_SECRET_KEY` |

- 服务开通：https://console.volcengine.com/search-infinity/web-search
- API Key 创建：https://console.volcengine.com/search-infinity/api-key

## 客户端配置

### Claude Code

```bash
claude mcp add doubao-search-mcp \
  -e ASK_ECHO_SEARCH_INFINITY_API_KEY=你的Key \
  -- uvx doubao-search-mcp
```

### 通用 mcp.json / claude_desktop_config.json

```json
{
  "mcpServers": {
    "doubao-search-mcp": {
      "command": "uvx",
      "args": ["doubao-search-mcp"],
      "env": {
        "ASK_ECHO_SEARCH_INFINITY_API_KEY": "你的Key"
      }
    }
  }
}
```

## 为什么锁 `mcp<2`

官方源码依赖 `mcp>=1.9.4` 未锁上限，而 mcp Python SDK 2.x 移除了 `mcp.server.FastMCP` 的导入路径，导致服务启动即崩溃。本包将依赖锁定为 `mcp>=1.9.4,<2`，保证在最新 1.x 上稳定运行；待上游适配 2.x 后再考虑升级。

## 发布新版本

1. **改版本号**：修改 `pyproject.toml` 中的 `version = "x.y.z"`。
2. **构建**：

   ```bash
   uv build
   ```

   产出 `dist/doubao_search_mcp-x.y.z-py3-none-any.whl` 与 `.tar.gz`。
3. **发布**：运行后按提示粘贴 API Token 即可，无需提前设置环境变量：

   ```bash
   twine upload dist/*
   ```

   提示 `Enter your API token:` 时直接粘贴 `pypi-...` token 回车即可（twine 会自动以 `__token__` 作为用户名）。

4. **验证**：

   ```bash
   uvx doubao-search-mcp --help
   ```

> 发布前需在 https://pypi.org/manage/account/token/ 创建 API Token（Scope 选 whole account 或本项目 `doubao-search-mcp`）。同一版本号不能重复上传，改版时务必递增版本号。

## 上游源码 / 同步更新

本包复刻自火山引擎官方源码（MIT 协议），后续同步更新以上游为准：

**上游地址**：https://github.com/volcengine/mcp-server/tree/main/server/mcp_server_askecho_search_infinity

同步上游改动时，注意保留本包的两处自定义：

1. `pyproject.toml` 依赖锁定 `mcp>=1.9.4,<2`（上游未锁上限，装到 mcp 2.x 时 `FastMCP` 导入会崩溃）
2. API 调用超时由上游的 3000s/600s 改为 30s，并清理了死代码

## License

MIT。源码源自 [volcengine/mcp-server](https://github.com/volcengine/mcp-server)。
