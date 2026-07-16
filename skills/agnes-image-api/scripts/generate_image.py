#!/usr/bin/env python3
"""
Quick one-shot text-to-image generation using Agnes Image API.

Uses the single model `agnes-image-2.1-flash`. Saves the result locally.

Usage:
    python generate_image.py "a cat on a beach at sunset"
    python generate_image.py "未来城市夜景" --size 1024x768 -o city.png

NOTE: `response_format` MUST be inside `extra_body`, not at the top level
of the request body (top-level placement causes a 400 error). For Text-to-Image
Base64 output, the doc recommends the top-level `return_base64: true`.
"""

import base64
import sys
import os

API_KEY = "sk-naWVi6wS1H33gqWjLoDQb0WYEN7TXweCXb79syHY9noFXPkl"
BASE_URL = "https://apihub.agnes-ai.com/v1"
MODEL = "agnes-image-2.1-flash"


def generate(prompt, size="1024x768", output=None):
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai package required. Install with: pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    print(f"Generating: {prompt}")
    response = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=size,
        # return_base64 is a top-level param for T2I Base64 output (per official doc).
        # It must NOT be confused with response_format, which goes inside extra_body.
        extra_body={"extra_body": {"return_base64": True}},
    )

    image_bytes = base64.b64decode(response.data[0].b64_json)

    if not output:
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in prompt)[:50]
        output = f"agnes_{safe_name}.png"

    with open(output, "wb") as f:
        f.write(image_bytes)

    file_size = os.path.getsize(output)
    print(f"Saved: {output} ({file_size:,} bytes)")
    return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Quick text-to-image generation with Agnes AI")
    parser.add_argument("prompt", help="Image description")
    parser.add_argument("--size", default="1024x768", help="Image size (default: 1024x768)")
    parser.add_argument("-o", "--output", default=None, help="Output filename")

    args = parser.parse_args()
    generate(args.prompt, args.size, args.output)
