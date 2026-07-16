#!/usr/bin/env python3
"""
Agnes Image API — CLI tool for text-to-image and image-to-image generation.

Both workflows use the single model `agnes-image-2.1-flash`.

Usage:
    # Text-to-image (URL output, printed to stdout)
    python agnes_image.py --prompt "一只猫在海边散步"

    # Text-to-image with custom size, saved to file
    python agnes_image.py --prompt "A futuristic city" --size 1024x768 -o city.png

    # Image-to-image editing (URL input)
    python agnes_image.py --prompt "把背景改成雪景，保留主体不变" \
        --image https://example.com/photo.jpg -o edited.png

    # Image-to-image from local file (auto-converted to data URI)
    python agnes_image.py --prompt "改成水彩风格" --image ./photo.jpg -o watercolor.png

NOTE on parameter placement (per official doc):
  - `response_format` MUST live inside the `extra_body` object, NOT at the top
    level of the request body. Top-level placement causes a 400 error.
  - For Text-to-Image Base64 output, prefer the top-level `return_base64: true`.
  - For Image-to-Image, the `image` array lives inside `extra_body`.
  - Image-to-Image does NOT require `tags: ["img2img"]`.
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

# Try to use openai SDK, fall back to raw HTTP
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


API_KEY = "sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl"
BASE_URL = "https://apihub.agnes-ai.com/v1"
ENDPOINT = f"{BASE_URL}/images/generations"
MODEL = "agnes-image-2.1-flash"


def generate_via_sdk(prompt, size, image_inputs, want_base64, timeout):
    """Use OpenAI SDK.

    The Agnes API literally expects a JSON key named `extra_body` containing
    `image` and/or `response_format`. The OpenAI SDK merges its own
    `extra_body=` kwarg into the request body, so we nest it once more:
    extra_body={"extra_body": {...}} -> body becomes {"extra_body": {...}}.
    """
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=timeout)

    inner = {}
    if image_inputs:
        inner["image"] = image_inputs
        # Image-to-Image: response_format goes inside extra_body
        inner["response_format"] = "b64_json" if want_base64 else "url"
    else:
        # Text-to-Image Base64: prefer top-level return_base64 per the doc
        if want_base64:
            inner["return_base64"] = True
        else:
            inner["response_format"] = "url"

    response = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=size,
        extra_body={"extra_body": inner},
    )
    return response


def generate_via_http(prompt, size, image_inputs, want_base64, timeout):
    """Use raw urllib HTTP request (fallback when openai SDK is not installed)."""
    inner = {}
    if image_inputs:
        inner["image"] = image_inputs
        inner["response_format"] = "b64_json" if want_base64 else "url"
    else:
        if want_base64:
            inner["return_base64"] = True
        else:
            inner["response_format"] = "url"

    body = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "extra_body": inner,
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    class DataItem:
        def __init__(self, d):
            self.url = d.get("url")
            self.b64_json = d.get("b64_json")

    class Response:
        def __init__(self, d):
            self.data = [DataItem(item) for item in d.get("data", [])]

    return Response(result)


def file_to_data_uri(filepath):
    """Convert a local image file to a base64 data URI."""
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = Path(filepath).suffix.lower().lstrip(".")
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    mime = mime_map.get(ext, "image/png")
    return f"data:{mime};base64,{b64}"


def download_url(url, output_path):
    """Download an image from a URL to a local file."""
    urllib.request.urlretrieve(url, output_path)
    print(f"Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Agnes Image API — Generate or edit images via Agnes AI (agnes-image-2.1-flash)"
    )
    parser.add_argument(
        "--prompt", required=True,
        help="Image description (text-to-image) or editing instruction (image-to-image)"
    )
    parser.add_argument(
        "--size", default="1024x768",
        help="Image size (default: 1024x768)"
    )
    parser.add_argument(
        "--image", action="append", dest="image_inputs", default=[],
        help="Input image URL or local file path for image-to-image (can repeat)"
    )
    parser.add_argument(
        "--format", choices=["url", "b64_json"], default=None,
        help="Output format. Default: url (or b64_json when -o is given for reliable local save)"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file path to save the generated image"
    )
    parser.add_argument(
        "--timeout", type=int, default=180,
        help="Request timeout in seconds (default: 180; doc recommends 60–360)"
    )

    args = parser.parse_args()

    # Process image inputs — convert local files to data URIs
    image_inputs = []
    for img in args.image_inputs:
        if img.startswith("http://") or img.startswith("https://") or img.startswith("data:"):
            image_inputs.append(img)
        elif os.path.isfile(img):
            print(f"Converting local file to data URI: {img}")
            image_inputs.append(file_to_data_uri(img))
        else:
            print(f"Error: image path not found or invalid: {img}", file=sys.stderr)
            sys.exit(1)

    # Decide output format
    want_base64 = False
    if args.format == "b64_json":
        want_base64 = True
    elif args.format is None and args.output:
        # Auto-use b64_json when saving locally for reliability
        want_base64 = True

    # Generate
    print(f"Model: {MODEL}")
    print(f"Prompt: {args.prompt}")
    print(f"Size: {args.size}")
    print(f"Mode: {'image-to-image' if image_inputs else 'text-to-image'}")
    print(f"Output format: {'b64_json' if want_base64 else 'url'}")
    print("Generating...")

    try:
        if HAS_OPENAI:
            response = generate_via_sdk(
                args.prompt, args.size, image_inputs, want_base64, args.timeout
            )
        else:
            response = generate_via_http(
                args.prompt, args.size, image_inputs, want_base64, args.timeout
            )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    for i, item in enumerate(response.data):
        if item.url:
            print(f"[{i+1}] URL: {item.url}")
            if args.output and i == 0:
                download_url(item.url, args.output)
        elif item.b64_json:
            if args.output:
                output_path = args.output
            else:
                output_path = f"agnes_image_output_{i+1}.png"
            image_bytes = base64.b64decode(item.b64_json)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            print(f"[{i+1}] Saved to: {output_path} ({len(image_bytes):,} bytes)")
            if i > 0 and args.output:
                break  # Only save first for named output


if __name__ == "__main__":
    main()
