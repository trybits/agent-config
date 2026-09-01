// ============================================================
// Markdown 渲染器（react-markdown + GFM）—— 跨项目实现模板
// 复制到目标项目：src/components/page-rules/MarkdownContent.tsx
// 依赖：react-markdown ^10 + remark-gfm ^4（pnpm add react-markdown remark-gfm）
//   注意：react-markdown 是 ESM-only 包，必须显式传 remarkPlugins=[remarkGfm]，否则表格不渲染
//   语义色变量说明见 RulePanelFloat.tsx 顶部注释；无变量时替换为等价 Tailwind 色值
// ============================================================

import { memo } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'

/** 目录项：由 extractHeadings 与渲染锚点共用，id 用源文档行号生成（prd-h-<line>，1 起），天然幂等 */
export interface HeadingItem {
  id: string
  level: 2 | 3 | 4 | 5
  text: string
}

/** 去掉标题文本中的常见行内标记，目录展示用 */
function cleanHeadingText(raw: string): string {
  return raw
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1') // [文本](链接) → 文本
    .replace(/`([^`]*)`/g, '$1') // 行内代码 → 文本
    .replace(/\*\*([^*]*)\*\*/g, '$1') // 加粗 → 文本
    .trim()
}

/**
 * 从 .md 原文提取 H2/H3/H4/H5 标题生成目录（H1 页面名与 H6 子项不进目录——H1 已显示在面板头部，
 * H6 缩进过深、保持目录简洁）。id = 标题所在行号（1 起），与渲染锚点同源。
 */
export function extractHeadings(content: string): HeadingItem[] {
  const items: HeadingItem[] = []
  const re = /^(#{2,5})\s+(.+)$/gm
  let m: RegExpExecArray | null
  while ((m = re.exec(content))) {
    const line = content.slice(0, m.index).split('\n').length
    items.push({
      id: `prd-h-${line}`,
      level: m[1].length as HeadingItem['level'],
      text: cleanHeadingText(m[2]),
    })
  }
  return items
}

const components: Components = {
  h1: ({ children }) => <h1 className="text-lg font-semibold text-text-title mt-4 mb-2">{children}</h1>,
  // 锚点 id 用 mdast 节点行号（与 extractHeadings 同源）；不用顺序计数——StrictMode 双渲染会使计数漂移
  h2: ({ children, node }) => (
    <h2 id={`prd-h-${node?.position?.start.line ?? 0}`} data-prd-h className="text-base font-medium text-text-title mt-5 mb-2">
      {children}
    </h2>
  ),
  h3: ({ children, node }) => (
    <h3 id={`prd-h-${node?.position?.start.line ?? 0}`} data-prd-h className="text-sm font-medium text-text-title mt-4 mb-1.5">
      {children}
    </h3>
  ),
  // h4：业务模块章节标题（如「页面布局概览」「数据表格区」「评级弹窗」等，见 rule-writing-guide.md 结构规范）
  h4: ({ children, node }) => (
    <h4 id={`prd-h-${node?.position?.start.line ?? 0}`} data-prd-h className="text-[13px] font-medium text-text-title mt-3 mb-1">
      {children}
    </h4>
  ),
  // h5：表格/弹窗内子项（如评级弹窗内「3.3.1. 本次评价」下的子项），与 H4 视觉接近但更次级
  h5: ({ children, node }) => (
    <h5 id={`prd-h-${node?.position?.start.line ?? 0}`} data-prd-h className="text-[13px] font-medium text-text-primary mt-2 mb-0.5">
      {children}
    </h5>
  ),
  // h6：操作项/二级子项（如「3.2.4.1. 智能体名称点击」），不进目录但支持锚点跳转与样式
  h6: ({ children, node }) => (
    <h6 id={`prd-h-${node?.position?.start.line ?? 0}`} data-prd-h className="text-[13px] font-normal text-text-primary mt-1.5 mb-0.5">
      {children}
    </h6>
  ),
  p: ({ children }) => <p className="text-[13px] leading-relaxed text-text-primary my-2">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-5 my-2 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-5 my-2 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="text-[13px] leading-relaxed text-text-primary">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-text-title">{children}</strong>,
  // 行内代码带底色；带 language- 的为代码块（在 pre 内），交给 pre 统一样式
  code: ({ className, children }) => {
    const isBlock = typeof className === 'string' && className.includes('language-')
    return (
      <code
        className={cn(
          'font-mono',
          isBlock
            ? 'block bg-transparent p-0 text-inherit'
            : 'rounded bg-muted px-1 py-0.5 text-[12px] text-primary'
        )}
      >
        {children}
      </code>
    )
  },
  pre: ({ children }) => (
    <pre className="my-2 overflow-x-auto rounded-md bg-muted p-3 text-xs leading-relaxed text-text-primary">{children}</pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-primary pl-3 my-2 text-text-secondary">{children}</blockquote>
  ),
  // 图片：需求文档中仅允许 public 绝对路径引用（见 rule-writing-guide.md「图片引用规范」），
  // 这里约束 max-width 防止撑破面板
  img: ({ src, alt }) => (
    <img src={src} alt={alt} className="my-2 max-w-full rounded-md border border-border" />
  ),
  table: ({ children }) => <table className="w-full text-xs my-2 border-collapse">{children}</table>,
  th: ({ children }) => (
    <th className="border border-border px-2 py-1 text-left bg-muted/50 font-medium text-text-title">{children}</th>
  ),
  td: ({ children }) => <td className="border border-border px-2 py-1 text-text-primary">{children}</td>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-primary hover:underline">
      {children}
    </a>
  ),
  hr: () => <hr className="my-3 border-border-subtle" />,
}

/**
 * Markdown 渲染器（react-markdown + GFM），元素级映射 Tailwind 样式。
 * content 为编译期 ?raw 静态字符串，用 memo 避免侧栏重渲染时重复解析。
 */
export const MarkdownContent = memo(function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {content}
    </ReactMarkdown>
  )
})
