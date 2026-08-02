"""Doubao Search MCP — 基于火山引擎豆包联网搜索 API 的 MCP 服务。

提供 web_search 工具（网页/图片搜索），鉴权支持 API Key 或火山引擎 AK/SK。
"""
from importlib.metadata import PackageNotFoundError, version

from .server import main

try:
    __version__ = version("doubao-search-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"
