---
name: build-permission
description: 管理构建命令的权限。当用户主动要求修复构建错误时，临时放开权限；当用户说不要构建时，检查并补充禁止构建的权限规则。不主动触发，不主动询问。
disable-model-invocation: true
---


# 构建权限管理

## 核心原则

**仅当用户主动提出时才执行对应操作。** 不自行触发、不主动询问用户是否需要修复构建。用户说"修复构建"就执行 A 流程，用户说"不要构建"就执行 B 流程，其他情况不干预。

## 前置步骤：检测项目构建环境

执行 A 或 B 流程前，先了解项目用什么工具。

### P1. 检测包管理器

读取项目根目录的锁文件：

| 锁文件 | 包管理器 |
|--------|----------|
| `pnpm-lock.yaml` | `pnpm` |
| `package-lock.json` | `npm` |
| `yarn.lock` | `yarn` |
| `bun.lock` / `bun.lockb` | `bun` |

多个锁文件按上表优先级取第一个。无锁文件默认为 `pnpm`。

### P2. 检测构建脚本

读取 `package.json` 的 `scripts`，关注：`build`、`compile`、`typecheck`、`type-check`、`lint`。

如果 `scripts.build`（或其他构建脚本）包含 `tsc`，或者根目录有 `tsconfig.json`，说明项目用了 TypeScript 类型检查。

> **为什么关心 tsc：** 很多项目把类型检查作为构建的一步（如 `tsc -b && vite build`）。修复时可能需要单独跑 `tsc` 来快速迭代类型错误，不必等整个构建流程。

### P3. 生成权限规则

根据检测结果动态生成 `Bash(...)` 权限阻止模式：

**包管理器构建命令：**
```
<pnpm|npm|yarn|bun> build
<pnpm|npm|yarn|bun> build *
```

**类型检查命令（如果项目用了 TypeScript）：**
```
tsc
tsc *
npx tsc
npx tsc *
```

**构建工具命令（从 scripts 中提取的构建工具）**：
从 `scripts.build` 的命令行中提取关键工具名（例如 `vite build` → `vite build`, `next build` → `next build`）并生成对应的 `npx` 规则。提取原则：只取命令行的第一个 token（工具名）+ 一个关键子命令参数（如有）。

### 无 package.json 的项目

（如 Python、Rust、Go 纯后端项目）询问用户需要拦截哪些构建命令。

---

## 流程 A：用户要求修复构建错误

用户说"构建报错"、"build 失败"、"修复构建"、"修一下构建"时：

### A1. 检查并临时放开 settings.json 权限

Read `.claude/settings.json`，看 `permissions.deny` 中是否有匹配 P3 生成规则的条目。

**移除规则时，只删除与构建相关的条目，保留 `deny` 数组中已有的其他规则不变。** 记下移除的具体条目，A5 恢复时只加回这些条目。无需再次询问用户——用户主动提出修复即视为已授权。

### A2. 运行构建抓错误

```bash
cd <项目根目录> && <构建命令> 2>&1
```

构建命令优先级：
1. `package.json` 中 `scripts.build` 的值（最贴合项目实际）
2. 若 `scripts.build` 不含 `tsc` 但项目有 `tsconfig.json`，优先跑 `tsc --noEmit`（类型检查比完整构建快，适合迭代修复）
3. 无 `package.json` 则询问用户

timeout 至少 120000ms。

### A3. 分析错误

提取：**文件路径**、**行号**、**错误码**、**错误描述**。

#### 常见：TS2352 类型断言语义错误

不兼容类型直接断言时触发（如 `window as Record<string, unknown>`），源类型缺少索引签名。

```typescript
// ❌
(window as Record<string, unknown>)[key]

// ✅
(window as unknown as Record<string, unknown>)[key]
```

### A4. 修复 + 验证

一次修完所有错误，再跑构建验证。若仍失败回到 A3。

### A5. 恢复权限

在 `deny` 数组中加回 A1 时移除的构建相关条目。**保留数组中已有的其他规则不变。**

---

## 流程 B：用户说"不要构建"

用户说"不要构建"、"禁止构建"、"别跑构建"、"烦死了每次都要确认"等或明确表示不想运行构建时：

### B1. 按前置步骤生成规则

参考 P1-P3 检测结果，生成适用的构建相关权限规则列表。

### B2. 补充到 settings.json

看 `.claude/settings.json` 的 `permissions.deny` 中是否已有对应的规则。将缺失的条目追加到 `deny` 数组中。**仅添加缺失的条目，不要删除或覆盖已有的其他规则。**

### B3. 告知用户结果

告诉用户已添加到 settings.json，今后构建命令会被拦截。
