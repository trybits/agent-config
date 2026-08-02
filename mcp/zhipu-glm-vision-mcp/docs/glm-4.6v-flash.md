# GLM-4.6V-Flash 官方文档快照

> 来源：https://docs.bigmodel.cn/cn/guide/models/text/glm-4.6v-flash （离线快照，抓取于 2026-08-02）

GLM-4.6V-Flash 是 GLM-4.6V 的免费版本，支持开启或关闭思考模式。训练时上下文窗口提升到 128K Tokens，视觉理解精度达到同参数规模 SOTA，并首次在模型架构中将 Function Calling 能力原生融入视觉模型。

## 能力支持

| 能力 | 说明 |
|---|---|
| 深度思考 | 支持开启或关闭思考模式，可灵活开关深层推理分析 |
| 视觉理解 | 支持图片、视频、文件多模态输入 |
| 流式输出 | 支持实时流式响应 |
| Function Calling | 原生多模态工具调用（「图像即参数，结果即上下文」） |
| 上下文缓存 | 智能缓存机制，优化长对话性能 |

## 推荐场景

- **图片理解**：通用 OCR、复杂表格解析、抗干扰识别（透视/模糊/光照不均/红章/水印）、商品属性识别、图像内容分析、瑕疵缺陷检测、Image2Prompt、物体检测与计数
- **视频理解**：视频内容标签、关键帧提取、事件时间轴构建、智能分镜与脚本生成、视频问答、视频巡检
- **文档/复杂图表问答**：抗干扰识别（红章/水印/褶皱）、版式还原与重构（结构化 JSON/Markdown/HTML）、跨页逻辑理解、文档智能问答、多文档关联分析

## API 调用

### 端点

```
POST https://open.bigmodel.cn/api/paas/v4/chat/completions
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

OpenAI 兼容，可用 `openai` SDK：`OpenAI(api_key=..., base_url="https://open.bigmodel.cn/api/paas/v4")`。

### 思考模式

请求顶层参数：

```json
"thinking": { "type": "enabled" }   // 或 "disabled"
```

开启后流式响应中 `choices[0].delta.reasoning_content` 为推理内容，`choices[0].delta.content` 为最终回答。

### 请求格式（content 多模态部分）

图片（`image_url`，支持 URL 或 Base64 data URI）：

```json
{
  "type": "image_url",
  "image_url": { "url": "https://.../xxx.png" }
}
```

```json
{
  "type": "image_url",
  "image_url": { "url": "data:image/png;base64,<base64>" }
}
```

视频（`video_url`）：

```json
{
  "type": "video_url",
  "video_url": { "url": "https://.../xxx.mov" }
}
```

文件（`file_url`，txt/pdf 等）：

```json
{
  "type": "file_url",
  "file_url": { "url": "https://.../demo1.pdf" }
}
```

文本（每个 user content 至少一条）：

```json
{
  "type": "text",
  "text": "描述一下这张图片"
}
```

### 完整示例（Python）

```python
from zhipuai import ZhipuAI  # 或 openai SDK

client = ZhipuAI(api_key="YOUR_API_KEY")
response = client.chat.completions.create(
    model="glm-4.6v-flash",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "https://cdn.bigmodel.cn/static/logo/register.png"},
                },
                {"type": "text", "text": "What are the pics talk about?"},
            ],
        }
    ],
    thinking={"type": "enabled"},
)
print(response.choices[0].message)
```

Base64 本地图片传入：

```python
import base64
with open("your/path/xxx.png", "rb") as f:
    img_base = base64.b64encode(f.read()).decode("utf-8")
# 将 img_base 填入 image_url.url 即可
```

## 已知限制（已核验）

- **图片、视频、文件三者互斥**：不支持在单个请求中同时传入 `file_url`、`image_url` 和 `video_url`。
- 视频输入最多 10 个；单图/单视频最多读取 16384 Token。
- 图片/视频/文件均支持 Base64 data URI 或公网 URL 传入。
- 输出模态为纯文本。
