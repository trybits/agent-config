// ============================================================
// 全局 UI store —— 跨项目实现模板
// 复制到目标项目：src/store/ui.ts
// 依赖：zustand（含 persist 中间件）。项目无 zustand 时，
//   改用 localStorage 直读直写：三个键（pageRulesOpen / rulePanelPos / rulePanelSize），
//   组件内 useSyncExternalStore 或 useState + useEffect 同步，效果等价。
// 注意：初始值在模块加载时读 window.innerWidth，SSR 场景不可用（本项目纯 CSR 无此问题）。
// ============================================================

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface RulePanelPos {
  x: number
  y: number
}

export interface RulePanelSize {
  w: number
  h: number
}

interface UiState {
  /** 页面规则面板是否展开 */
  pageRulesOpen: boolean
  /** 悬浮球位置（视口坐标） */
  rulePanelPos: RulePanelPos
  /** 规则面板尺寸 */
  rulePanelSize: RulePanelSize
  setPageRulesOpen: (open: boolean) => void
  togglePageRules: () => void
  setRulePanelPos: (pos: RulePanelPos) => void
  setRulePanelSize: (size: RulePanelSize) => void
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      pageRulesOpen: false,
      rulePanelPos: { x: window.innerWidth - 96, y: window.innerHeight - 280 },
      rulePanelSize: { w: 360, h: 420 },
      setPageRulesOpen: (open) => set({ pageRulesOpen: open }),
      togglePageRules: () => set((state) => ({ pageRulesOpen: !state.pageRulesOpen })),
      setRulePanelPos: (pos) => set({ rulePanelPos: pos }),
      setRulePanelSize: (size) => set({ rulePanelSize: size }),
    }),
    {
      name: 'ui-storage',
      // partialize 限定只持久化这三个字段，函数不持久化
      partialize: (state) => ({
        pageRulesOpen: state.pageRulesOpen,
        rulePanelPos: state.rulePanelPos,
        rulePanelSize: state.rulePanelSize,
      }),
    }
  )
)
