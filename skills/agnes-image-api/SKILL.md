---
name: agnes-image-api
description: Generate and edit images via the Agnes AI Image API. Covers text-to-image generation and image-to-image editing, both using the single model agnes-image-2.1-flash. Trigger when the user asks to create images from text, edit or transform existing images, generate AI art, posters, or concept visuals. The Agnes API is OpenAI-compatible and currently free (0 per image) with RPM limits. Provides API key, endpoint details, prompt-writing guidance, and Python/curl examples.
agent_created: true
---

# Agnes Image API

Generate and edit images via the Agnes AI image model — OpenAI-compatible, currently free (0 / image).

## Overview

Agnes AI provides a single image model through an OpenAI-compatible API that supports both text-to-image and image-to-image workflows:

| Model | Purpose | Key Use |
|---|---|---|
| `agnes-image-2.1-flash` | Text-to-Image AND Image-to-Image | Generate images from text prompts; edit/transform existing images |

Both workflows share the same model name, base URL, and API key. Pricing is **0 / image (free)** per the current official doc — earlier docs listed $0.003/image, so verify on the official page if billing matters. RPM (requests per minute) limits still apply.

## Quick Start

The pre-configured credentials are:

- **Base URL:** `https://apihub.agnes-ai.com`
- **API Endpoint:** `POST https://apihub.agnes-ai.com/v1/images/generations`
- **API Key:** `sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl`
- **Auth header:** `Authorization: Bearer <API_KEY>`
- **Content-Type:** `application/json`

### Fastest path — cURL (Text-to-Image, URL output)

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "A luminous floating city above a misty canyon at sunrise, cinematic realism",
    "size": "1024x768",
    "extra_body": {
      "response_format": "url"
    }
  }'
```

### Fastest path — Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl",
    base_url="https://apihub.agnes-ai.com/v1",
)

resp = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="一只可爱的小猫在绿茵足球场上踢足球，阳光明媚，动感瞬间，高清摄影风格",
    size="1024x768",
    extra_body={"extra_body": {"response_format": "url"}},
)
print(resp.data[0].url)
```

## Text-to-Image Generation

Use `agnes-image-2.1-flash` to create images from natural language descriptions.

**Required parameters:**
- `model`: `"agnes-image-2.1-flash"`
- `prompt`: Natural language description (Chinese or English)
- `size`: Image dimensions, e.g. `"1024x768"`

**Optional parameters:**
- `return_base64`: `true` — return the result as Base64 data instead of URL
- `extra_body.response_format`: `"url"` or `"b64_json"` — output format (must be inside `extra_body`, NOT at top level)

> **CRITICAL:** Do NOT place `response_format` at the top level of the request body — this causes a 400 error. Always nest it inside `extra_body`. For Text-to-Image Base64 output, prefer the top-level `return_base64: true` parameter.

**Python example — URL output:**

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl",
    base_url="https://apihub.agnes-ai.com/v1",
)

response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="一座未来主义城市在日落时分，飞行汽车穿梭于摩天大楼之间，赛博朋克风格",
    size="1024x768",
    extra_body={"extra_body": {"response_format": "url"}},
)

image_url = response.data[0].url
print(f"Generated image: {image_url}")
```

**Python example — Base64 output (using `return_base64`):**

```python
response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="一座未来主义城市在日落时分",
    size="1024x768",
    extra_body={"return_base64": True},
)

import base64
image_data = base64.b64decode(response.data[0].b64_json)
with open("output.png", "wb") as f:
    f.write(image_data)
```

## Image-to-Image Editing

Use `agnes-image-2.1-flash` (same model) to edit or transform existing images. Provide the input image URL(s) inside `extra_body.image`.

> **Note:** Image-to-Image does NOT require sending `tags: ["img2img"]`. The presence of the `image` array inside `extra_body` is sufficient.

> **⚠️ Official doc inconsistency:** The "Important Notes" and "Remarks" sections of the official doc say to put `image` in the "top-level `image` array", but **all 5 official examples and the "Common Errors" correct examples place `image` inside `extra_body.image`**. Follow the examples — place `image` inside `extra_body`. The scripts in this skill follow the examples.

**Required parameters:**
- `model`: `"agnes-image-2.1-flash"`
- `prompt`: Description of desired edits
- `size`: Image dimensions, e.g. `"1024x768"`
- `extra_body.image`: List of image URLs or base64 data URIs (inside `extra_body`)

**Optional parameters:**
- `extra_body.response_format`: `"url"` (default) or `"b64_json"` — must be inside `extra_body`

**Python example — URL input, URL output:**

```python
response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="保留小猫踢足球的动作和足球不变，把场景改成傍晚的专业足球场，看台有观众，球场灯光亮起，电影感",
    size="1024x768",
    extra_body={
        "extra_body": {
            "image": ["https://example.com/original.jpg"],
            "response_format": "url",
        }
    },
)
print(response.data[0].url)
```

**Python example — Base64 input:**

```python
import base64

with open("local_image.png", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")
data_uri = f"data:image/png;base64,{image_b64}"

response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="把背景换成冬季雪景",
    size="1024x768",
    extra_body={
        "extra_body": {
            "image": [data_uri],
            "response_format": "b64_json",
        }
    },
)
```

**Editing prompt pattern:** Clearly state what to KEEP and what to CHANGE:
- "保留[主体/动作/元素]不变，把[要改的部分]改成[目标效果]"
- "Keep [subject] unchanged, change [element] to [target]"

## Response Format

**URL output (`extra_body.response_format: "url"`):**
```json
{
  "created": 1780000000,
  "data": [
    {
      "url": "https://storage.googleapis.com/agnes-aigc/xxx.png",
      "b64_json": null,
      "revised_prompt": null
    }
  ]
}
```

**Base64 output (`return_base64: true` or `extra_body.response_format: "b64_json"`):**
```json
{
  "created": 1780000000,
  "data": [
    {
      "url": null,
      "b64_json": "iVBORw0KGgoAAAANS...",
      "revised_prompt": null
    }
  ]
}
```

Access the result via `data[0].url` or `data[0].b64_json`.

## Prompt Writing Guide

### Recommended prompt structure

```
[Subject] + [Scene/Environment] + [Style] + [Lighting] + [Composition] + [Quality requirements]
```

**Examples:**
- "一只橘猫趴在窗台上，午后阳光透过百叶窗洒在它身上，温暖治愈，胶片摄影风格"
- "A luminous floating city above a misty canyon at sunrise, cinematic realism, wide-angle composition, rich architectural details, soft golden light, high visual density"

### Best practices for text-to-image

- Be specific about the **subject** (type, color, pose, expression)
- Describe the **scene** (indoor/outdoor, time of day, weather)
- Mention **lighting** (golden hour, studio lighting, neon, soft morning light)
- Specify the **style** (photography, oil painting, watercolor, 3D render, anime, etc.)
- Include **quality keywords**: "HD photography style", "cinematic", "8K", "highly detailed"
- Add **composition** details: wide-angle, close-up, bird's eye view

### Best practices for image-to-image

- **Always specify what to keep** and **what to change**
- Use the original image URL from a prior text-to-image call
- Try multiple variations with different style keywords on the same base image
- Input images can be URLs or data URI base64 strings
- Recommended structure: `[Modification requirement] + [New style/scene] + [Elements to add/remove] + [Elements to preserve]`

### For high-information-density images

Agnes Image 2.1 Flash is optimized for complex, detail-rich images. When the target image contains complex details (text, charts, UI mockups, diagrams), use longer, more detailed prompts that explicitly list every element, its position, and the visual hierarchy.

## Common Errors and Troubleshooting

| Error | Cause | Solution |
|---|---|---|
| `response_format` at top level causes 400 | `response_format` placed at top level of request body | Move it inside `extra_body`: `"extra_body": {"response_format": "url"}` |
| Sending `tags: ["img2img"]` | Image-to-Image doesn't require tags | Remove the `tags` field; just provide `image` array in `extra_body` |
| Input image URL not accessible | The URL provided is private or expired | Use a publicly accessible HTTPS URL or base64 data URI |
| Request timeout | Image generation takes longer than client timeout | Set client timeout to 60–360 seconds depending on complexity |
| Missing `image` in image-to-image | Forgot to include `extra_body.image` | Always include the `image` array inside `extra_body` for image-to-image |
| 429 / request rejected | RPM limit reached | Add delay/retry or reduce request frequency |
| Image-to-image result poor | Prompt only describes changes, not what to preserve | Use the "keep X, change Y" pattern explicitly |

## Pricing

| Price | Type |
|---|---|
| 0 / image (free) | Generated images |

> **Note:** The current Chinese official doc lists the price as `0 / 张` (free). An earlier English version of the doc listed `$0.003 / image`. Verify on the official page (https://agnes-ai.com/doc/agnes-image-21-flash) if billing matters.

- **Rate limit:** RPM only (requests per minute)
- **Account needed:** Yes (free registration to get API key)
- The generated image URL is accessible for a limited time — download locally if long-term access is needed.

## Available Models Reference

For the full list of available models beyond images, refer to `references/api_reference.md`. Other Agnes models include:
- `agnes-2.0-flash` — Text/Chat/Agent model
- `agnes-video-v2.0` — Video generation (requires 8n+1 frames, async task polling)

## Scripts

- `scripts/agnes_image.py` — Standalone Python script for calling the image API without importing the skill. Run with: `python scripts/agnes_image.py --prompt "your description"`.
- `scripts/generate_image.py` — Quick one-shot: `python scripts/generate_image.py "a cat on a beach at sunset"`. Saves the result to the current directory.
