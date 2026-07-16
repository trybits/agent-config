# mimo-vision-mcp

MCP server for visual understanding via Xiaomi MIMO multimodal API.

## Usage

```bash
uvx mimo-vision-mcp
```

Requires MIMO_API_KEY environment variable.

## Tools

- `analyze_image(file_path, prompt?)` - Analyze a local image
- `analyze_image_url(url, prompt?)` - Analyze an image from URL
- `analyze_multiple_images(file_paths, prompt?)` - Analyze multiple images

## License

MIT
