# mimo-vision-mcp

基于小米 MIMO API（mimo-v2.5）的多模态理解 MCP 服务，支持图片、音频、视频三类理解能力。

## 使用

```bash
uvx mimo-vision-mcp
```

需要设置环境变量 `MIMO_API_KEY`。

可选：通过环境变量 `MIMO_MODEL` 或 `--model <名称>` 参数覆盖模型（默认 `mimo-v2.5`）。

## 工具

### 图片理解
- `analyze_image(file_path, prompt?)` - 分析本地图片（JPEG/PNG/GIF/WebP/BMP，≤50MB）
- `analyze_image_url(url, prompt?)` - 分析公网 URL 图片（≤50MB）
- `analyze_multiple_images(file_paths, prompt?)` - 分析多张本地图片（最多 10 张）
- `analyze_multiple_images_url(urls, prompt?)` - 分析多张 URL 图片（最多 10 张）

### 音频理解
- `analyze_audio(file_path, prompt?)` - 分析本地音频（MP3/WAV/FLAC/M4A/OGG，Base64 ≤50MB）
- `analyze_audio_url(url, prompt?)` - 分析公网 URL 音频（≤100MB）

### 视频理解
- `analyze_video(file_path, prompt?, fps?, media_resolution?)` - 分析本地视频（MP4/MOV/AVI/WMV，Base64 ≤50MB）
- `analyze_video_url(url, prompt?, fps?, media_resolution?)` - 分析公网 URL 视频（≤300MB）

视频参数：
- `fps`：抽帧率，默认 2，范围 [0.1, 10]，越高时序细节越精细、Token 越多
- `media_resolution`：`"default"`（平衡效果与效率）或 `"max"`（提升小物体/细节识别）

## 媒体限制

| 模态 | 支持格式 | URL 大小 | Base64 大小 | 多输入 |
|---|---|---|---|---|
| 图片 | JPEG / PNG / GIF / WebP / BMP | ≤50MB | ≤50MB | 最多 10 张 |
| 音频 | MP3 / WAV / FLAC / M4A / OGG | ≤100MB | ≤50MB | 多个 |
| 视频 | MP4 / MOV / AVI / WMV | ≤300MB | ≤50MB | 多个 |

注：Base64 传入时单个文件不超过 50MB；音频/视频不支持 files API 本地文件上传，仅支持 URL 或 Base64 编码传入（本地文件由本服务自动转 Base64）。

## 相关文档

`docs/` 目录存放了 MiMo V2.5 官方能力文档的离线快照与抓取方法：

- [图片理解](docs/image-understanding.md)
- [音频理解](docs/audio-understanding.md)
- [视频理解](docs/video-understanding.md)
- [官方文档抓取与转换说明](docs/capture-and-conversion.md)

官方在线文档：<https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/multimodal-understanding/image-understanding>

## License

MIT
