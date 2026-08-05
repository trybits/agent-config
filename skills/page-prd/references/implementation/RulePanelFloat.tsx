// ============================================================
// 「需求文档」悬浮球 + 规则面板 —— 跨项目实现模板
// 复制到目标项目：src/components/page-rules/RulePanelFloat.tsx
// 依赖（模板已在其所在项目验证）：
//   - useIsMobile  → @/hooks/use-mobile（shadcn/ui 标准 hook，无则自实现 <768px 判断）
//   - cn           → @/lib/utils（clsx + tailwind-merge）
//   - usePageRule  → 见 page-rules-registry.md
//   - useUiStore   → 见 ui-store.ts
//   - Iconfont     → 项目 Iconfont symbol（cebianlanshouqi 收起图标），无则换 lucide-react
//   - 语义色变量  → text-text-title / text-text-primary / text-text-secondary /
//                   bg-muted / border-border-subtle / bg-background / text-primary
//                   目标项目无这些变量时，替换为等价的 Tailwind 色值即可
// 关键实现点（勿随意改动）：
//   - 拖拽/调宽高过程直接改 DOM style（不走 React 渲染），松手一次性提交 store —— 保证跟手无延迟
//   - 球和面板 z-[60]，必须高于顶部导航（本项目 TopNavBar 为 z-50）
//   - 过渡只写 transition-[transform,box-shadow]，不写 left/top，否则拖拽延迟
// ============================================================

import { useState, useRef, useCallback, useEffect } from 'react'
import { useIsMobile } from '@/hooks/use-mobile'
import { usePageRule } from '@/hooks/usePageRule'
import { useUiStore } from '@/store/ui'
import type { RulePanelPos, RulePanelSize } from '@/store/ui'
import { cn } from '@/lib/utils'
import { MarkdownContent } from './MarkdownContent'

const BALL_SIZE = 64 // 悬浮球直径
const PANEL_GAP = 12 // 面板与悬浮球间距
const PANEL_MARGIN = 12 // 面板距视口边缘
const MIN_PANEL_W = 280
const MIN_PANEL_H = 200

/** Iconfont 图标（沿用项目内内联定义模式，也可改为项目全局图标组件） */
function IconFont({ name, className = '' }: { name: string; className?: string }) {
  return (
    <svg className={className} aria-hidden="true">
      <use xlinkHref={`#icon-${name}`} />
    </svg>
  )
}

/** 根据悬浮球位置计算面板摆放：球在左半边 → 面板放右侧，球在右半边 → 面板放左侧，并夹紧在视口内 */
function getPanelStyle(pos: RulePanelPos, size: RulePanelSize) {
  const vw = window.innerWidth
  const vh = window.innerHeight
  const w = Math.min(size.w, vw - PANEL_MARGIN * 2)
  const h = Math.min(size.h, vh - PANEL_MARGIN * 2)
  const ballCenterX = pos.x + BALL_SIZE / 2
  const ballCenterY = pos.y + BALL_SIZE / 2
  const placeRight = ballCenterX < vw / 2
  const left = Math.max(
    PANEL_MARGIN,
    Math.min(placeRight ? pos.x + BALL_SIZE + PANEL_GAP : pos.x - w - PANEL_GAP, vw - w - PANEL_MARGIN)
  )
  const top = Math.max(PANEL_MARGIN, Math.min(ballCenterY - h / 2, vh - h - PANEL_MARGIN))
  return { left, top, width: w, height: h }
}

/**
 * 页面规则悬浮球 + 规则面板：
 * - 悬浮球可拖到页面任意位置，仅当前页面有规则时显示、可点击展开/收起
 * - 面板按悬浮球位置智能翻转（空间大的一侧），支持拖拽右下角调整宽高
 * - 拖拽/调宽高过程直接操作 DOM style 跟随（不经过 React 渲染），松手一次性提交 store，保证跟手无延迟
 */
export function RulePanelFloat() {
  const isMobile = useIsMobile()
  const rule = usePageRule()
  const open = useUiStore((s) => s.pageRulesOpen)
  const togglePageRules = useUiStore((s) => s.togglePageRules)
  const pos = useUiStore((s) => s.rulePanelPos)
  const setPos = useUiStore((s) => s.setRulePanelPos)
  const size = useUiStore((s) => s.rulePanelSize)
  const setSize = useUiStore((s) => s.setRulePanelSize)

  const [dragging, setDragging] = useState(false)
  const [resizing, setResizing] = useState(false)
  const hasMoved = useRef(false)
  const dragStart = useRef({ x: 0, y: 0 })
  const dragOffset = useRef({ x: 0, y: 0 })
  const dragPos = useRef({ x: 0, y: 0 })
  const resizeStart = useRef({ x: 0, y: 0, w: 0, h: 0 })
  const resizeSize = useRef({ w: 0, h: 0 })
  const ballRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  // 悬浮球拖拽开始
  const handleBallMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return
      e.preventDefault()
      setDragging(true)
      hasMoved.current = false
      dragStart.current = { x: e.clientX, y: e.clientY }
      dragOffset.current = { x: e.clientX - pos.x, y: e.clientY - pos.y }
      dragPos.current = pos
    },
    [pos]
  )

  // 拖拽跟随：直接改 DOM style（不走 React 渲染），松手一次性提交 store，避免卡顿
  useEffect(() => {
    if (!dragging) return
    const onMove = (e: MouseEvent) => {
      const dx = Math.abs(e.clientX - dragStart.current.x)
      const dy = Math.abs(e.clientY - dragStart.current.y)
      if (dx > 3 || dy > 3) hasMoved.current = true
      const maxX = window.innerWidth - BALL_SIZE
      const maxY = window.innerHeight - BALL_SIZE
      const next = {
        x: Math.max(0, Math.min(e.clientX - dragOffset.current.x, maxX)),
        y: Math.max(0, Math.min(e.clientY - dragOffset.current.y, maxY)),
      }
      dragPos.current = next
      if (ballRef.current) {
        ballRef.current.style.left = `${next.x}px`
        ballRef.current.style.top = `${next.y}px`
      }
      // 面板开着时同步跟随（直接改定位样式，无需重渲染）
      if (panelRef.current) {
        const style = getPanelStyle(next, size)
        panelRef.current.style.left = `${style.left}px`
        panelRef.current.style.top = `${style.top}px`
      }
    }
    const onUp = () => {
      setDragging(false)
      setPos(dragPos.current)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'grabbing'
    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }
  }, [dragging, setPos, size])

  // 悬浮球点击：拖动过则忽略
  const handleBallClick = () => {
    if (hasMoved.current) return
    togglePageRules()
  }

  // 面板右下角拖拽调整尺寸
  const handleResizeStart = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return
      e.preventDefault()
      e.stopPropagation()
      setResizing(true)
      resizeStart.current = { x: e.clientX, y: e.clientY, w: size.w, h: size.h }
      resizeSize.current = size
    },
    [size]
  )

  // 调整尺寸：直接改 DOM style，松手一次性提交 store
  useEffect(() => {
    if (!resizing) return
    const onMove = (e: MouseEvent) => {
      const dx = e.clientX - resizeStart.current.x
      const dy = e.clientY - resizeStart.current.y
      const maxW = window.innerWidth - PANEL_MARGIN * 2
      const maxH = window.innerHeight - PANEL_MARGIN * 2
      const next = {
        w: Math.max(MIN_PANEL_W, Math.min(resizeStart.current.w + dx, maxW)),
        h: Math.max(MIN_PANEL_H, Math.min(resizeStart.current.h + dy, maxH)),
      }
      resizeSize.current = next
      if (panelRef.current) {
        const style = getPanelStyle(pos, next)
        panelRef.current.style.width = `${style.width}px`
        panelRef.current.style.height = `${style.height}px`
        panelRef.current.style.left = `${style.left}px`
        panelRef.current.style.top = `${style.top}px`
      }
    }
    const onUp = () => {
      setResizing(false)
      setSize(resizeSize.current)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.userSelect = 'none'
    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.userSelect = ''
    }
  }, [resizing, pos, setSize])

  // 移动端（<768px）或当前页面无规则时不渲染
  if (isMobile || !rule) return null

  const panelStyle = open ? getPanelStyle(pos, size) : null

  return (
    <>
      {/* 悬浮球（z-[60] 高于顶部导航 z-50）：渐变 + 玻璃高光 + 光晕 */}
      <button
        ref={ballRef}
        className={cn(
          'fixed z-[60] flex size-16 select-none items-center justify-center rounded-full text-white',
          'bg-gradient-to-br from-[#4C8CFF] via-[#0064FF] to-[#0048B8]',
          'shadow-[0_4px_16px_rgba(0,100,255,0.5)] ring-1 ring-white/30',
          // 只过渡 transform/shadow，不过渡 left/top，否则拖拽跟手会延迟
          'transition-[transform,box-shadow] duration-200',
          dragging
            ? 'cursor-grabbing scale-95'
            : 'cursor-grab hover:scale-105 hover:shadow-[0_6px_24px_rgba(0,100,255,0.65)]'
        )}
        style={{ left: pos.x, top: pos.y }}
        onMouseDown={handleBallMouseDown}
        onClick={handleBallClick}
        title={open ? '收起需求文档' : '展开需求文档'}
        draggable={false}
      >
        <span className="pointer-events-none absolute inset-0 rounded-full bg-gradient-to-b from-white/25 via-transparent to-transparent" />
        <span className="relative text-xs font-semibold leading-none">需求文档</span>
      </button>

      {/* 规则面板（z-[60] 高于顶部导航 z-50） */}
      {panelStyle && (
        <div
          ref={panelRef}
          className="fixed z-[60] flex flex-col overflow-hidden rounded-lg border border-border-subtle bg-background shadow-xl"
          style={panelStyle}
        >
          <div className="flex h-10 shrink-0 items-center justify-between border-b border-border-subtle pl-3 pr-1">
            <span className="truncate text-sm font-medium text-text-title">{rule.title}</span>
            <button
              onClick={togglePageRules}
              aria-label="收起需求文档"
              title="收起"
              className="rounded p-1 text-muted-foreground hover:bg-muted"
            >
              <IconFont name="cebianlanshouqi" className="size-4" />
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
            <MarkdownContent content={rule.content} />
          </div>
          {/* 右下角尺寸调整手柄 */}
          <div
            className="absolute right-0 bottom-0 size-4 cursor-se-resize"
            onMouseDown={handleResizeStart}
            title="拖动调整面板大小"
          >
            <div className="absolute right-1 bottom-1 size-2 border-r-2 border-b-2 border-muted-foreground/50" />
          </div>
        </div>
      )}
    </>
  )
}
