# 实现落地说明（实施顺序与依赖）

按顺序执行。模板组件文件（`RulePanelFloat.tsx`、`MarkdownContent.tsx`、`ui-store.ts`）可直接复制。

## 0. 依赖安装

```bash
pnpm add react-markdown remark-gfm
```

- `react-markdown` ^10（React 18+，自带类型，ESM-only——Vite 下无问题）
- `remark-gfm`（GFM 表格/删除线/任务列表；**必须显式传 `remarkPlugins=[remarkGfm]`，否则表格不渲染为表格**）
- 若项目无 zustand：`pnpm add zustand`，或按 `ui-store.ts` 顶部注释改用 localStorage 直写

## 1. 前置检查（tsconfig / 样式变量）

- `?raw` 导入需要 Vite；TS 侧 tsconfig 的 `types` 需含 `"vite/client"`，否则 `import xxx from './x.md?raw'` 报类型错误
- 项目若开启 `verbatimModuleSyntax`：类型导入必须 `import type`
- 模板使用的语义色（`text-text-title` / `text-text-primary` / `text-text-secondary` / `bg-muted` / `border-border-subtle` / `bg-background` / `text-primary`）需在目标项目 CSS 中定义；没有时替换为等价的 Tailwind 色值（如 `text-slate-800` / `bg-slate-100` / `border-slate-200`）
- 模板使用 `@/` 路径别名，需与目标项目 vite.config / tsconfig paths 一致，否则改为相对路径

## 2. 文件清单（按序创建/修改）

| # | 文件 | 来源 | 说明 |
| --- | --- | --- | --- |
| 1 | `src/store/ui.ts` | `ui-store.ts` | 全局 UI store（位置/尺寸/展开状态，persist） |
| 2 | `src/config/page-rules/index.ts` | `page-rules-registry.md` | 类型 + 注册表 + `getPageRule` 匹配 |
| 3 | `src/config/page-rules/<domain>.ts` | `page-rules-registry.md` | 领域注册文件（每领域一个，如 management-center.ts） |
| 4 | `src/config/page-rules/content/*.md` | 新建 | 规则内容（结构与写作规范见 `../rule-writing-guide.md`，含需求批次外壳模板；注意存量文档可能为旧格式，新增需求按新结构插入） |
| 5 | `src/hooks/usePageRule.ts` | `page-rules-registry.md` | `useLocation` → 规则条目 |
| 6 | `src/components/page-rules/MarkdownContent.tsx` | `MarkdownContent.tsx` | react-markdown 渲染器 |
| 7 | `src/components/page-rules/RulePanelFloat.tsx` | `RulePanelFloat.tsx` | 悬浮球 + 面板（核心组件） |
| 8 | `src/components/layout/Layout.tsx` | 修改 | 根节点挂载 `<RulePanelFloat />`（**唯一改动的既有文件**） |

## 3. Layout 挂载（唯一改动的既有文件）

在布局根节点追加组件，不改动原有结构：

```tsx
import { Outlet } from 'react-router-dom'
import TopNavBar from './TopNavBar'
import { RulePanelFloat } from '@/components/page-rules/RulePanelFloat'

export default function Layout() {
  return (
    <div className="min-h-screen bg-background">
      <TopNavBar />
      <main className="pt-[60px] overflow-x-hidden">
        <Outlet />
      </main>
      <RulePanelFloat />
    </div>
  )
}
```

- 悬浮球/面板为 `fixed` 定位，**不需要**给 main 预留空间，布局结构零改动
- z-index：球/面板 `z-[60]`，必须高于目标项目顶部导航的 z-index（本项目 TopNavBar 为 `z-50`）
- 不走 Layout 的路由（如登录页、运营大屏）天然不受影响

## 4. 验证清单（浏览器实测）

- [ ] 无规则页面（如 `/home`）不出现悬浮球
- [ ] 有规则页面：悬浮球显示为主色渐变球，点击展开面板、再点收起
- [ ] 拖拽球跟手无延迟（松手后位置记忆）
- [ ] 球在左半边 → 面板在球右侧；球在右半边 → 面板在球左侧（翻转正确）
- [ ] 面板右下角拖拽调宽高（最小 280×200，不超出视口）
- [ ] 刷新页面：球位置、面板尺寸、展开状态保留
- [ ] 滚动页面：球不遮挡操作入口，且不被顶部导航遮挡
- [ ] Markdown 内容正确渲染（H1–H4 标题层级、列表、代码块、GFM 表格）
- [ ] 有图片的页面：图片正常显示且不撑破面板（max-width 约束生效）
- [ ] 窗口 <768px：悬浮球不渲染，页面与改造前一致
