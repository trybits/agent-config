---
name: rule-creator
description: >-
  创建规范并保存为规则文件。当用户想要定规范、立规矩、统一风格/方式时触发。
disable-model-invocation: true
---

# Rule Creator

创建规范并保存为规则文件。本 skill 帮你把需要长期遵守的约定格式化为结构化的规则文件，后续在适用范围内自动生效。

先确定写的是**项目规则**还是**用户规则**，走不同的流程。

---

## 项目规则

适用范围局限于当前项目，保存到 `.claude/rules/`。

### 1. 澄清意图

- **规范范围？** 代码风格？组件模式？架构约定？命名规范？工作流？
- **适用范围？** 全局适用（不加 `paths`）还是仅特定目录/文件类型（加 `paths` 限定）？
- **是否已有做法？** 翻代码看看实际怎么写的。
- **参考依据？** 文档、最佳实践、团队讨论记录。

### 2. 调研现有代码

- 查看项目源码目录下的实现，了解实际模式
- 查看 `.claude/rules/` 已有规则，确保不冲突、互补
- 查看配置文件了解技术栈（`package.json`、`tsconfig.json` 等）
- 涉及外部库/框架时查阅官方文档确认最佳实践
- 查看 `~/.claude/rules/` 下的用户规则，避免冲突

### 3. 撰写规则

**文件名**：描述性 kebab-case，如 `component-patterns.md`。可按子目录组织，如 `frontend/component-patterns.md`

**内容要求：**
- imperative 语气：直接写"做什么"，不写"建议做什么"
- 一个文件一个主题，精简聚焦
- 只写标准做法供参照执行，不需要示例和解释

**决定是否加 `paths`：**
- 不加 → 每次会话自动加载，全局适用
- 加 `paths` → 只在操作匹配文件时加载，节省上下文

```markdown
---
paths:
  - "src/**/*.{ts,tsx}"
  - "lib/**/*.ts"
---
```

路径规则在 Claude **读取匹配文件时触发**。glob 模式：`**/*.ts`（所有 ts）、`src/**/*`（src 下全部）、`src/**/*.{ts,tsx}`（多扩展名）。

**保存位置**：`.claude/rules/`

### 4. 向用户说明并验证

说明为什么这样定规范（考虑的因素、依据），可附好/坏示例帮助理解。

确认：
- 与已有规则无矛盾
- `paths` 范围准确（不宽不窄）
- 告知文件路径、覆盖内容、适用范围

### 跨项目共享

公司级规范可用符号链接共享到多个项目：
```bash
ln -s ~/company-standards/frontend.md .claude/rules/frontend.md
```
> Windows 需管理员身份或开发者模式。不可行时手动复制。

---

## 用户规则

适用范围为**用户所有项目**，保存到 `~/.claude/rules/`。

### 1. 澄清意图

- **什么偏好？** 编码习惯、编辑器设置、个人工作流
- **确认归属**：是个人习惯而非项目约定？

### 2. 撰写规则

- 用户规则总是全局适用，**不加 `paths`**
- 格式与项目规则一致（imperative 语气、精简聚焦）

**保存位置**：`~/.claude/rules/`

### 3. 告知用户

说明文件创建位置（`~/.claude/rules/`），用户所有项目都会受此影响。

---

## 规范类型参考

- **代码风格**：命名约定、导入组织、类型定义、注释文档
- **组件规范**：文件结构、Props 定义、状态管理、样式方案、拆分粒度
- **架构规范**：目录结构、模块依赖方向、数据流、错误处理、本地存储
- **工作流规范**：Git 提交格式、分支命名、Code Review checklist
- **UI/UX 规范**：设计 tokens、布局模式、响应式、暗色模式
- **API / 数据规范**：接口模式、数据格式、错误响应、存储路径

---

## 示例：项目规则

**用户说**："给项目定一下组件命名规范"

1. 翻看项目组件目录下的现有文件，确认当前命名风格
2. 查看 `.claude/rules/` 已有规则，无冲突
3. 判断：只影响 `src/` 下的 TSX/TS 文件，加 `paths` 限定
4. 撰写 `.claude/rules/component-naming.md`：

```markdown
---
paths:
  - "src/**/*.tsx"
  - "src/**/*.ts"
---

# 组件命名规范

## 文件命名
- 组件文件使用 **PascalCase**：`UserProfile.tsx`，`SideNav.tsx`
- 工具/非组件文件使用 **camelCase**：`formatDate.ts`，`useAuth.ts`

## 组件命名
- 组件名与文件名一致
- 使用具名导出（`export function`），避免默认导出
- 回调 Props 使用 `on` 前缀：`onSubmit`、`onClose`
- 布尔 Props 使用 `is`/`has`/`show` 前缀：`isLoading`、`hasError`、`showDetails`
```

5. 告知用户："已创建 `.claude/rules/component-naming.md`，覆盖文件命名、组件命名、Props 命名三方面，仅在编辑 `src/` 下的 TS/TSX 文件时生效。"

## 示例：用户规则

**用户说**："我习惯 commit 信息用中文写"

1. 确认：这是个人习惯而非项目约定，走用户规则
2. 撰写 `~/.claude/rules/commit-convention.md`：

```markdown
# Git 提交规范

所有 Commit 信息使用中文撰写。
```

3. 告知："已写入 `~/.claude/rules/commit-convention.md`，之后所有项目的 commit 都会按此规范执行。"
