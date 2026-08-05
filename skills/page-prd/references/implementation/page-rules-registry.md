# 规则注册表与 Hook —— 实现参考

以下三个文件按本文件内容创建到目标项目。

## 1. `src/config/page-rules/index.ts` — 类型 + 注册表 + 匹配

```ts
import { MANAGEMENT_CENTER_PAGE_RULES } from './management-center'

export interface PageRuleEntry {
  /** 面板头部显示的标题 */
  title: string
  /** 精确匹配路径（与 location.pathname 全等，优先） */
  match?: string
  /** 前缀匹配路径（pathname.startsWith），动态路由兜底，最长者胜 */
  matchPrefix?: string
  /** Markdown 内容（Vite ?raw 导入，编译期内联） */
  content: string
}

export const PAGE_RULES: PageRuleEntry[] = [
  ...MANAGEMENT_CENTER_PAGE_RULES,
  // 后续领域在此追加，如 ...INFERENCE_CENTER_PAGE_RULES
]

/** 解析路径对应的规则条目；无命中返回 null（组件不渲染悬浮球） */
export function getPageRule(pathname: string): PageRuleEntry | null {
  // 精确匹配优先（无动态参数的路由）
  const exact = PAGE_RULES.find((r) => r.match === pathname)
  if (exact) return exact

  // 前缀匹配兜底（含 :id 等动态段的路由），取最长匹配
  let best: PageRuleEntry | null = null
  let bestLen = -1
  for (const r of PAGE_RULES) {
    if (r.matchPrefix && pathname.startsWith(r.matchPrefix) && r.matchPrefix.length > bestLen) {
      best = r
      bestLen = r.matchPrefix.length
    }
  }
  return best
}
```

匹配的是 `location.pathname` 实际值（如场景管理恒为 `/management-center/scene-manage`）。
精确匹配优先于前缀匹配；前缀匹配取最长；未命中 → 不渲染悬浮球。

## 2. 领域注册文件（按页面领域分组，每领域一个文件）

`src/config/page-rules/management-center.ts`：

```ts
import sceneManagementRules from './content/scene-management.md?raw'
import type { PageRuleEntry } from '.'

export const MANAGEMENT_CENTER_PAGE_RULES: PageRuleEntry[] = [
  {
    title: '场景管理 · 需求文档',
    // scene-manage 走 /management-center/:tab 兜底路由（default-page.tsx 内 'scene-manage' 分支），
    // pathname 恒为 /management-center/scene-manage，无更深路径，用精确匹配
    match: '/management-center/scene-manage',
    content: sceneManagementRules,
  },
]
```

新增页面规则时：`import xxx from './content/xxx.md?raw'` 并追加条目。
路径无动态参数 → `match`（精确）；含 `:id` 等动态段 → `matchPrefix`（前缀，多个动态页可共用一条规则）。

## 3. `src/hooks/usePageRule.ts` — 路由 → 规则条目

```ts
import { useLocation } from 'react-router-dom'
import { getPageRule } from '@/config/page-rules'
import type { PageRuleEntry } from '@/config/page-rules'

/** 当前路径对应的页面规则条目；无规则时返回 null（组件不渲染） */
export function usePageRule(): PageRuleEntry | null {
  const { pathname } = useLocation()
  return getPageRule(pathname)
}
```

注：`usePageRule` 依赖 react-router 的 `useLocation`；目标项目无 react-router 时，
改为读取项目自己的路由状态（如 query/自定义路由），仅此一处需要改造。
