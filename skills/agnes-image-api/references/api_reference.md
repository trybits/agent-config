# Agnes AI Image API — Full Reference

## Connection Details

| Field | Value |
|---|---|
| Base URL | `https://apihub.agnes-ai.com` |
| Image Endpoint | `POST https://apihub.agnes-ai.com/v1/images/generations` |
| Auth | `Authorization: Bearer <API_KEY>` |
| Content-Type | `application/json` |
| Protocol | OpenAI-compatible |

## Image Model

### agnes-image-2.1-flash — Text-to-Image AND Image-to-Image

A single model handles both text-to-image generation and image-to-image editing. Updated by Sapiens AI, it offers improved performance for high-information-density images compared to previous versions.

- **Text-to-Image:** Generates high-quality images from natural language prompts
- **Image-to-Image:** Transforms, edits, or restyles existing images based on natural language instructions
- **Strengths:** Complex scenes, detailed compositions, text/UI mockups, photorealistic output, composition preservation
- **Input format (I2I):** Image URL or base64 data URI
- **Latency:** Fast (flash tier)

## Request Parameters

| Type | Parameter | Required | Description |
|---|---|---|---|
| string | `model` | Yes | Model name. Use `agnes-image-2.1-flash` |
| string | `prompt` | Yes | Instruction for generating or editing the image |
| string | `size` | Yes | Output image size, e.g. `1024x768` |
| string[] | `extra_body.image` | Required for I2I | Array of input images. Supports public URLs or Data URI Base64 |
| boolean | `return_base64` | No | Set to `true` when Text-to-Image should return Base64 output (top-level parameter) |
| object | `extra_body` | No | Container for advanced parameters (`image`, `response_format`) |
| string | `extra_body.response_format` | No | Output format: `url` or `b64_json` (must be inside `extra_body`, NOT top level) |

### Critical parameter placement rules

- **`response_format`** must go INSIDE `extra_body`, never at the top level — top-level placement causes a 400 error.
- **`return_base64`** is a top-level parameter for Text-to-Image Base64 output.
- **`image`** array goes inside `extra_body` for Image-to-Image.
- Image-to-Image does NOT require `tags: ["img2img"]` — just provide the `image` array.

> **⚠️ Official doc inconsistency on `image` placement:** The "Important Notes" (`重要说明`) and "Remarks" (`备注`) sections of the official doc state that `image` should be placed in the "top-level `image` array" (`顶层 image 数组`). However, **all 5 official code examples and the "Common Errors" (`常见错误与排查`) correct examples place `image` inside `extra_body.image`**. The examples are authoritative (they are executable code), so this skill places `image` inside `extra_body.image`. If a request with `extra_body.image` ever fails, try the top-level `image` array as a fallback — but the examples strongly indicate `extra_body.image` is correct.

## cURL Examples

### 1. Text-to-Image with URL output

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
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

Result URL is at: `data[0].url`

### 2. Text-to-Image with Base64 output

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "A clean product photo of a glass cube on a white studio background, soft shadows, high detail",
    "size": "1024x768",
    "return_base64": true
  }'
```

Result Base64 data is at: `data[0].b64_json`

### 3. Image-to-Image with URL input and URL output

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "Transform the scene into a rain-soaked cyberpunk night with neon reflections while preserving the original composition",
    "size": "1024x768",
    "extra_body": {
      "image": ["https://example.com/input-image.png"],
      "response_format": "url"
    }
  }'
```

### 4. Image-to-Image with URL input and Base64 output

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "Make the object orange while preserving the original composition",
    "size": "1024x768",
    "extra_body": {
      "image": ["https://example.com/input-image.png"],
      "response_format": "b64_json"
    }
  }'
```

### 5. Image-to-Image with Data URI Base64 input

Data URI format: `data:image/png;base64,BASE64_HERE`

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "Make the object matte black while preserving the original composition",
    "size": "1024x768",
    "extra_body": {
      "image": ["data:image/png;base64,BASE64_HERE"],
      "response_format": "b64_json"
    }
  }'
```

## Response Format

### URL Output

When `extra_body.response_format` is set to `"url"`:

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

The generated image URL is typically accessible for a limited time. Download and save locally if needed for long-term use.

### Base64 Output

When `return_base64: true` (T2I) or `extra_body.response_format: "b64_json"` (I2I):

```json
{
  "created": 1780000000,
  "data": [
    {
      "url": null,
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA...",
      "revised_prompt": null
    }
  ]
}
```

## Python — Full Examples

### Text-to-Image (URL output)

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl",
    base_url="https://apihub.agnes-ai.com/v1",
)

response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="一只可爱的柯基犬在海边奔跑，夕阳金色光线，写实摄影风格",
    size="1024x768",
    extra_body={"extra_body": {"response_format": "url"}},
)

print(response.data[0].url)
```

### Text-to-Image (Base64, save to file)

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl",
    base_url="https://apihub.agnes-ai.com/v1",
)

response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="现代简约风格客厅设计，自然光充足，北欧风格，建筑渲染",
    size="1024x768",
    extra_body={"return_base64": True},
)

image_bytes = base64.b64decode(response.data[0].b64_json)
with open("generated_image.png", "wb") as f:
    f.write(image_bytes)
print("Saved to generated_image.png")
```

### Image-to-Image (URL input)

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl",
    base_url="https://apihub.agnes-ai.com/v1",
)

# First, generate a base image
gen = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="城市天际线，白天，清晰",
    size="1024x768",
    extra_body={"extra_body": {"response_format": "url"}},
)
original_url = gen.data[0].url

# Then edit it
edited = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="保留城市天际线不变，把白天改成夜晚，霓虹灯亮起，赛博朋克风格",
    size="1024x768",
    extra_body={
        "extra_body": {
            "image": [original_url],
            "response_format": "url",
        }
    },
)

print(f"Original: {original_url}")
print(f"Edited:   {edited.data[0].url}")
```

### Image-to-Image (local file base64 input)

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl",
    base_url="https://apihub.agnes-ai.com/v1",
)

def file_to_data_uri(filepath):
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = filepath.rsplit(".", 1)[-1].lower()
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
    mime = mime_map.get(ext, "image/png")
    return f"data:{mime};base64,{b64}"

data_uri = file_to_data_uri("my_photo.jpg")

response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="把照片改成梵高星空风格的油画，保留人物轮廓",
    size="1024x768",
    extra_body={
        "extra_body": {
            "image": [data_uri],
            "response_format": "b64_json",
        }
    },
)

print(response.data[0].b64_json[:50] + "...")
```

## Prompt Structure Reference

### Recommended format

```
[Subject] + [Scene/Environment] + [Style] + [Lighting] + [Composition] + [Quality requirements]
```

### Prompt examples by category

**Photorealistic:**
- "一位老人在日式庭院中修剪盆栽，晨光穿过竹帘，宁静安详，4K摄影"
- "A barista pouring latte art in a cozy coffee shop, morning light through large windows, shallow depth of field, commercial photography"

**Artistic / Stylized:**
- "龙在云端翱翔，中国传统水墨画风格，留白构图，意境深远"
- "A girl reading under a giant oak tree, Studio Ghibli animation style, soft pastel colors, magical atmosphere"

**Product / Concept:**
- "极简风格无线耳机产品渲染图，白色背景，柔光箱打光，3D渲染，商业摄影级别"
- "A sleek smartwatch on a marble surface, product photography, dramatic side lighting, 8K detail shot"

**Image Editing:**
- "保留人物不变，把办公室背景换成热带海滩，自然光线"
- "Keep the product exactly as is, change the background to pure white, studio lighting"

## Pricing and Limits

| Aspect | Detail |
|---|---|
| Cost | 0 / image (free) per current Chinese official doc; earlier English doc listed $0.003/image — verify on official page if billing matters |
| Rate limit | RPM only (requests per minute) |
| Account needed | Yes (free registration to get API key) |
| Usage cap | No hard cap beyond RPM |

When hitting RPM limits (HTTP 429), add a delay and retry.

## Other Agnes Models

| Model | Endpoint | Purpose |
|---|---|---|
| `agnes-2.0-flash` | `/v1/chat/completions` | Text chat, Agent tasks, tool calling |
| `agnes-image-2.1-flash` | `/v1/images/generations` | Text-to-image AND image-to-image |
| `agnes-video-v2.0` | `/v1/videos` (async) | Video generation (requires `num_frames` = 8n+1) |

All models share the same API key and base URL.

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 200 | Success | Parse `data[0].url` or `data[0].b64_json` |
| 400 | Bad request | Check parameter placement — `response_format` must be in `extra_body`, not top level |
| 401 | Unauthorized | Verify API key in `Authorization` header |
| 429 | Rate limited | Wait and retry with exponential backoff |
| 500 | Server error | Retry after a short delay |

### Common error patterns

1. **`response_format` at top level causes 400**: Move it inside `extra_body` — `"extra_body": {"response_format": "url"}`.
2. **Sending `tags: ["img2img"]`**: Not needed. Just provide `image` array in `extra_body`.
3. **Missing `image` for image-to-image**: Use `extra_body={"extra_body": {"image": [...]}}` in Python SDK, or `"extra_body": {"image": [...]}` in raw JSON.
4. **Invalid image URL**: Ensure URLs are publicly accessible HTTPS (no authentication required to fetch). Use Data URI Base64 for private images.
5. **Timeout on complex images**: Set client timeout to 60–360 seconds depending on prompt complexity and image size.
6. **Chinese prompts work natively** — no translation needed.
