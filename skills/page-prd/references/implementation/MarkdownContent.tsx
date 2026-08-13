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

const components: Components = {
  h1: ({ children }) => <h1 className="text-lg font-semibold text-text-title mt-4 mb-2">{children}</h1>,
  h2: ({ children }) => <h2 className="text-base font-medium text-text-title mt-5 mb-2">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-medium text-text-title mt-4 mb-1.5">{children}</h3>,
  // h4：需求文档「当前页面说明」下的九维度章节标题（见 rule-writing-guide.md 结构规范）
  h4: ({ children }) => <h4 className="text-[13px] font-medium text-text-title mt-3 mb-1">{children}</h4>,
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
