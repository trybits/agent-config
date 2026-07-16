# Agent Config

这个项目用于管理 AI Coding Agent 的配置文件，包括 skills、MCP server、rules 和 commands。

## 目录结构

```
agent-config/
├── commands/       # 自定义 slash 命令
├── mcp/            # MCP 服务端配置
│   └── mimo-vision/  # 小米 MIMO 视觉分析 MCP 服务
├── rules/          # 编码规则 / 指南
│   ├── backend/      # 后端规则（按语言/框架分子目录）
│   └── frontend/     # 前端规则（按框架分子目录，如 react/）
│       └── react/
├── skills/         # 技能定义
│   ├── agnes-image-api/   # agens的图片生成技能
│   ├── build-permission/  # 构建权限技能
│   ├── drawio/            # DrawIO 图表绘制技能
│   ├── git-stage-commit-push/  # Git 暂存-提交-推送技能
│   ├── prd-writer/        # PRD 需求文档编写技能
│   ├── prototype-design/  # 原型设计技能
│   └── rule-creator/      # 规则创建技能
└── CLAUDE.md       # 本文件 — 项目总览与工作约定
```
