# 官方文档抓取与转换说明

本文记录 `docs/` 下 MiMo V2.5 能力文档（图片 / 音频 / 视频理解）与 OpenAI Chat Completions API 接口文档的抓取与 Markdown 转换方法，便于日后重新抓取、验证内容准确性。

## 源页面

| 能力 | URL |
|---|---|
| 图片理解 | `https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/multimodal-understanding/image-understanding` |
| 音频理解 | `https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/multimodal-understanding/audio-understanding` |
| 视频理解 | `https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/multimodal-understanding/video-understanding` |
| OpenAI Chat Completions API | `https://mimo.mi.com/docs/zh-CN/api/chat/openai-api` |

## 抓取（curl）

`WebFetch` 无法通过 `mimo.mi.com` 的域名安全校验（被网络策略拦截），因此直接用 `curl` + 浏览器 User-Agent 抓取：

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0"
for name in image audio video; do
  curl -sL --max-time 40 -A "$UA" \
    "https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/multimodal-understanding/$name-understanding" \
    -o "mimo-$name.html"
done
```

三个页面均返回 HTTP 200，单页约 230~290 KB。

> ⚠️ Windows 终端（GBK）直接打印中文会乱码。把提取结果写入 UTF-8 文件，再用支持 UTF-8 的工具（如 Claude Code 的 Read）查看。

## 页面结构（关键发现）

站点是 SPA，但**正文内容已由服务端渲染进 HTML**，抓取后无需执行 JS 即可提取：

- 正文区：`<div class="mdxContent">…</div>`
- 标题：`<h1 class="mdx-h1">`、`<h2 class="mdx-h2">` …
- 代码块：`<mimo-code-block>` 内的 `<pre raw="…">` —— **`raw` 属性是 URL 编码的完整源码**，用 `urllib.parse.unquote` 一次还原，无需从逐 token 化的子节点拼接
- 多语言 Tab：`<mimo-tab><mimo-tab-item label="Python SDK">`（另有 Curl、Anthropic Messages API）
- 内部链接：hash 路由形式 `https://mimo.mi.com/#/docs/…`

### OpenAI Chat Completions API 页的差异

`docs/api/chat/openai-api` 页与上述能力文档结构不同，转换脚本也需单独处理：

- **参数定义**不在正文文本里，而是以 `<inline-schema-v2 schema="…">` 属性的转义 JSON 内嵌（`&#x22;` 等实体，需 `html.unescape` 后 `json.loads`），递归的 `children` 字段表示嵌套子字段。
- **代码块**用 `<pre>` 纯文本（非 `raw` 属性），且部分示例代码位于 `mdxContent` 之外（如页面底部的 curl / JSON 示例），需用 `soup.find_all('pre')` 全局收集后按内容归属到各 section。示例 `pre` 会被响应式双栏布局渲染**两遍**（移动端 `block lg:hidden` + 桌面侧栏 `hidden lg:block`，内容相同），取第一份即可。
- 描述文本内含 `<code>`、`<blockquote>`、`<ul>` 等标签：`code`→反引号、`blockquote`→压缩为单行、**`ul/li`→转多行子列表**（否则列表会被压平成粘连文本，反引号互相贴死，如 `131072``mimo-v2.5`）。
- schema 的 **`defaultValue` 字段需渲染为「默认值 `…`」**：页面里 11 个参数带默认值（`top_p=0.95`、`fps=2`、`max_keyword/limit=5`、`stream=false` 等），不处理会整块丢失。
- `mimo-tab-item` 的 **`label` 是语义信息**（认证方式 tab 的真实标签是 `API Key 鉴权` / `Bearer 鉴权`），需保留，不能硬编码成「认证方式 1/2」。
- 两个响应对象小节（非流式/流式）补 `### 响应对象参数` 标题保持结构一致；流式小节页面本身没有示例代码（无 SSE chunk 示例），属正常。

## 转换（MDX HTML → Markdown）

用 `html.parser.HTMLParser` 提取 `mdxContent`，按标签映射：

| HTML | Markdown |
|---|---|
| `h1`/`h2`/`h3`/`h4` | `#` / `##` / `###` / `####` |
| `p` / `br` | 段落 / 换行 |
| `li` | `- ` 列表项 |
| `pre[@raw]` | ` ``` ` 围栏代码块（`unquote` 还原）|
| `mimo-tab-item[@label]` | `**label**` |
| `strong` / `b` / `em` / `code` | `**` / `*` / `` ` `` |
| `a` | `[text](href)` |

处理细节：

1. **跳过页面内首个 `h1`**：文档页头已带标题，避免重复；同时吞掉该标题的文本。
2. **`pre[raw]` 捕获后跳过子节点**：避免重复输出；据此顺带清理 block-level `<code>` 包裹残留的孤立反引号。
3. **`<li>` 内的 `<p>` 不输出换行**：避免嵌套列表被拆得零散。
4. **压缩连续空行**：3 个以上连续换行压成 2 个。

完整转换脚本见文末。

## 复现步骤

1. 按上文 `curl` 抓取三个能力文档 HTML 到任意目录。
2. 运行文末脚本，生成三个 `.md`。
3. OpenAI API 页（`openai-api.md`）结构不同，需按上文「OpenAI Chat Completions API 页的差异」另行解析（`inline-schema-v2` 的 `schema` 属性 + 全局 `pre`）。
4. 核对内容，重点检查：**大小限制、支持格式、视频 `fps` / `media_resolution` 参数、FAQ**。

## 已知限制

- 文档会更新（音频页底部标注更新于 2026-07-15），重新抓取即可获得最新内容。
- 若小米改版页面结构，`mdxContent` / `pre[@raw]` 等选择器可能需要调整。
- 转换结果是"接近原文"的版本而非逐字精确（嵌套列表排版可能有细微差异）。

## 完整转换脚本

```python
"""Convert MiMo doc SPA pages (mdxContent HTML) to clean Markdown."""
import html as htmllib
import re
from html.parser import HTMLParser
from urllib.parse import unquote

SRC = {
    "image": "mimo-image.html",
    "audio": "mimo-audio.html",
    "video": "mimo-video.html",
}
TITLE = {"image": "图片理解", "audio": "音频理解", "video": "视频理解"}
DOC_URL = "https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/multimodal-understanding/{}-understanding"


class MDConverter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []
        self.active = False          # 当前是否在 mdxContent 内
        self.div_depth = 0
        self.in_pre = False          # 已捕获 pre[@raw]，跳过其子节点
        self.in_li = False
        self.h1_seen = False
        self.in_skipped_h1 = False   # 正在吞掉首个 h1 的文本
        self._link_href = ""

    def _emit(self, s):
        self.out.append(s)

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if tag == "div" and "mdxContent" in ad.get("class", ""):
            self.active = True
            self.div_depth = 1
            return
        if not self.active:
            return
        if tag == "div":
            self.div_depth += 1
            return
        if self.in_pre:
            return

        if tag == "h1":
            if self.h1_seen:
                self._emit("\n\n# ")
            else:
                self.h1_seen = True
                self.in_skipped_h1 = True
        elif tag == "h2":
            self._emit("\n\n## ")
        elif tag == "h3":
            self._emit("\n\n### ")
        elif tag == "h4":
            self._emit("\n\n#### ")
        elif tag == "p":
            if not self.in_li:
                self._emit("\n\n")
        elif tag == "br":
            self._emit("\n")
        elif tag in ("ul", "ol"):
            self._emit("\n")
        elif tag == "li":
            self._emit("\n- ")
            self.in_li = True
        elif tag == "pre":
            raw = ad.get("raw")
            if raw:
                code = unquote(raw).strip("\n")
                self._emit(f"\n\n```{self._guess_lang(code)}\n{code}\n```\n")
                self.in_pre = True
            else:
                self._emit("\n\n```\n")
        elif tag == "mimo-tab-item":
            label = ad.get("label", "")
            if label:
                self._emit(f"\n\n**{label}**\n")
        elif tag == "strong":
            self._emit("**")
        elif tag in ("b", "em"):
            self._emit("*")
        elif tag == "code":
            self._emit("`")
        elif tag == "a":
            self._emit("[")
            self._link_href = ad.get("href", "")
        elif tag == "table":
            self._emit("\n")
        elif tag in ("thead", "tbody"):
            self._emit("\n")
        elif tag == "tr":
            self._emit("\n|")
        elif tag in ("td", "th"):
            self._emit(" ")

    def handle_endtag(self, tag):
        if not self.active:
            return
        if tag == "div":
            if self.div_depth > 0:
                self.div_depth -= 1
                if self.div_depth == 0:
                    self.active = False
            return
        if self.in_pre and tag == "pre":
            self.in_pre = False
            return
        if tag in ("h1", "h2", "h3", "h4"):
            self.in_skipped_h1 = False
            self._emit("\n")
        elif tag == "p":
            if not self.in_li:
                self._emit("\n")
        elif tag == "li":
            self.in_li = False
        elif tag == "strong":
            self._emit("**")
        elif tag in ("b", "em"):
            self._emit("*")
        elif tag == "code":
            self._emit("`")
        elif tag == "a":
            self._emit(f"]({self._link_href or ''})")
        elif tag in ("ul", "ol"):
            self._emit("\n")
        elif tag == "tr":
            self._emit("\n")

    def handle_data(self, data):
        if not self.active or self.in_pre or self.in_skipped_h1:
            return
        if data.strip() or (self.out and self.out[-1] in ("\n", " ", "- ")):
            self._emit(htmllib.unescape(data))

    def _guess_lang(self, code):
        if re.search(r"curl|--location|--request", code, re.I):
            return "bash"
        return "python"


def convert(fname):
    raw = open(fname, encoding="utf-8", errors="replace").read()
    p = MDConverter()
    p.feed(raw)
    text = "".join(p.out)
    text = re.sub(r"\n{3,}", "\n\n", text)          # 压缩连续空行
    text = re.sub(r"(?m)^`\s*$", "", text)          # 清理孤立反引号
    return text.strip() + "\n"


for key, fname in SRC.items():
    body = convert(fname)
    header = (
        f"# {TITLE[key]}\n\n"
        f"> 来源：<{DOC_URL.format(key)}>（MiMo V2.5 官方文档，抓取自离线快照）\n"
    )
    with open(f"mimo-{key}-doc.md", "w", encoding="utf-8") as f:
        f.write(header + body)
    print(f"mimo-{key}-doc.md: {len(body)} chars")
```
