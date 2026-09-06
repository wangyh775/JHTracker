import React from 'react';
import { FileText } from 'lucide-react';

export interface ResumeMarkdownViewerProps {
  content: string;
  highlightSkills?: string[];
  theme?: 'cyan' | 'emerald' | 'amber';
  emptyMessage?: string;
  className?: string;
}

/**
 * High-performance ATS Resume Markdown Renderer with Skill Highlights
 * Supports:
 * - Headings (H1, H2, H3, H4) with stylized badges and borders
 * - Lists (Unordered -/ *, Ordered 1.)
 * - Emphasis (Bold **, Italic *, Strike ~~)
 * - Inline Code (`) and Code Blocks (```)
 * - Blockquotes (>)
 * - Horizontal Rules (---)
 * - Tables (| col | col |)
 * - Precise skill badge highlighting with safe tokenized nesting
 */
export const ResumeMarkdownViewer: React.FC<ResumeMarkdownViewerProps> = ({
  content,
  highlightSkills = [],
  theme = 'cyan',
  emptyMessage = '暂无简历内容',
  className = '',
}) => {
  if (!content || !content.trim()) {
    return (
      <div className={`flex flex-col items-center justify-center h-full text-[#6b7280] italic p-8 text-xs text-center ${className}`}>
        <FileText className="h-8 w-8 text-[#374151] mb-2" />
        {emptyMessage}
      </div>
    );
  }

  // Build sorted skills regex for high-priority matching (e.g. TypeScript before Type, C++ before C)
  const sortedSkills = React.useMemo(() => {
    return Array.from(new Set(highlightSkills.filter((s) => s && s.trim().length > 0)))
      .sort((a, b) => b.length - a.length);
  }, [highlightSkills]);

  const skillRegex = React.useMemo(() => {
    if (sortedSkills.length === 0) return null;
    const escaped = sortedSkills.map((s) => s.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&'));
    return new RegExp(`(${escaped.join('|')})`, 'gi');
  }, [sortedSkills]);

  // Skill badge color styles based on theme
  const getSkillBadgeClass = () => {
    switch (theme) {
      case 'emerald':
        return 'bg-emerald-950/80 text-emerald-300 px-1 py-0.5 rounded border border-emerald-500/40 font-semibold shadow-xs mx-0.5 inline-block';
      case 'amber':
        return 'bg-amber-950/80 text-amber-300 px-1 py-0.5 rounded border border-amber-500/40 font-semibold shadow-xs mx-0.5 inline-block';
      case 'cyan':
      default:
        return 'bg-cyan-950/80 text-cyan-300 px-1 py-0.5 rounded border border-cyan-500/40 font-semibold shadow-xs mx-0.5 inline-block';
    }
  };

  const badgeClass = getSkillBadgeClass();

  // Helper to render inline skills in raw text
  const highlightSkillsInText = (text: string, keyPrefix: string): React.ReactNode[] => {
    if (!skillRegex || !text) return [text];

    const parts = text.split(skillRegex);
    return parts.map((part, idx) => {
      const isMatched = sortedSkills.some((s) => s.toLowerCase() === part.toLowerCase());
      if (isMatched) {
        return (
          <span key={`${keyPrefix}-sk-${idx}`} className={badgeClass}>
            {part}
          </span>
        );
      }
      return part;
    });
  };

  // Inline Markdown parser: handles **bold**, *italic*, `code`, [link](url), ~~strike~~, and skills
  const renderInlineMarkdown = (lineText: string, keyPrefix: string): React.ReactNode => {
    if (!lineText) return null;

    // Tokenize inline markdown patterns:
    // 1: `code`
    // 2: **bold** or __bold__
    // 3: *italic* or _italic_
    // 4: ~~strike~~
    // 5: [link text](url)
    const inlinePattern = /(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|~~[^~]+~~|\[[^\]]+\]\([^)]+\))/g;
    const tokens = lineText.split(inlinePattern);

    return tokens.map((token, tIdx) => {
      const tokenKey = `${keyPrefix}-tok-${tIdx}`;

      // 1. Inline code: `...`
      if (token.startsWith('`') && token.endsWith('`') && token.length >= 2) {
        const codeContent = token.slice(1, -1);
        return (
          <code
            key={tokenKey}
            className="px-1.5 py-0.5 mx-0.5 rounded bg-[#1e2230] border border-[#2e3448] text-amber-200 font-mono text-[11px]"
          >
            {codeContent}
          </code>
        );
      }

      // 2. Bold: **...** or __...__
      if (
        (token.startsWith('**') && token.endsWith('**') && token.length >= 4) ||
        (token.startsWith('__') && token.endsWith('__') && token.length >= 4)
      ) {
        const boldContent = token.slice(2, -2);
        return (
          <strong key={tokenKey} className="font-bold text-white">
            {highlightSkillsInText(boldContent, `${tokenKey}-b`)}
          </strong>
        );
      }

      // 3. Italic: *...* or _..._
      if (
        (token.startsWith('*') && token.endsWith('*') && token.length >= 2) ||
        (token.startsWith('_') && token.endsWith('_') && token.length >= 2)
      ) {
        const italicContent = token.slice(1, -1);
        return (
          <em key={tokenKey} className="italic text-[#e5e7eb]">
            {highlightSkillsInText(italicContent, `${tokenKey}-i`)}
          </em>
        );
      }

      // 4. Strikethrough: ~~...~~
      if (token.startsWith('~~') && token.endsWith('~~') && token.length >= 4) {
        const strikeContent = token.slice(2, -2);
        return (
          <del key={tokenKey} className="line-through text-gray-500">
            {highlightSkillsInText(strikeContent, `${tokenKey}-s`)}
          </del>
        );
      }

      // 5. Link: [text](url)
      const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (linkMatch) {
        const [, linkText, linkUrl] = linkMatch;
        return (
          <a
            key={tokenKey}
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2 transition-colors mx-0.5"
          >
            {highlightSkillsInText(linkText, `${tokenKey}-a`)}
          </a>
        );
      }

      // Normal text with skill highlighting
      return (
        <React.Fragment key={tokenKey}>
          {highlightSkillsInText(token, tokenKey)}
        </React.Fragment>
      );
    });
  };

  // Block parser: groups lines into headings, lists, codeblocks, blockquotes, tables, paragraphs
  const rawLines = content.split('\n');
  const blocks: React.ReactNode[] = [];

  let i = 0;
  while (i < rawLines.length) {
    const line = rawLines[i];
    const trimmed = line.trim();

    // 1. Fenced code block (```lang ... ```)
    if (trimmed.startsWith('```')) {
      const codeLines: string[] = [];
      const lang = trimmed.replace(/^```/, '').trim();
      i++;
      while (i < rawLines.length && !rawLines[i].trim().startsWith('```')) {
        codeLines.push(rawLines[i]);
        i++;
      }
      i++; // skip closing ```
      blocks.push(
        <div
          key={`codeblock-${i}`}
          className="my-3 rounded-lg overflow-hidden border border-[#24283b] bg-[#0b0d13]"
        >
          {lang && (
            <div className="px-3 py-1 bg-[#151824] border-b border-[#24283b] text-[10px] font-mono text-gray-400 flex items-center justify-between">
              <span>{lang}</span>
            </div>
          )}
          <pre className="p-3 text-[11px] font-mono text-cyan-200/90 overflow-x-auto leading-relaxed custom-scrollbar">
            <code>{codeLines.join('\n')}</code>
          </pre>
        </div>
      );
      continue;
    }

    // 2. Horizontal Rule (---, ***, ___)
    if (/^(\*{3,}|-{3,}|_{3,})$/.test(trimmed)) {
      blocks.push(
        <hr key={`hr-${i}`} className="my-3 border-t border-[#24283b]" />
      );
      i++;
      continue;
    }

    // 3. Headings (#, ##, ###, ####)
    if (line.startsWith('# ') || line.startsWith('#\t')) {
      const headingText = line.replace(/^#\s+/, '');
      blocks.push(
        <h1
          key={`h1-${i}`}
          className="text-base font-bold text-cyan-400 border-b border-cyan-500/30 pb-1.5 mt-3.5 mb-2 flex items-center gap-2"
        >
          <span className="w-1.5 h-4 bg-cyan-500 rounded-full inline-block" />
          <span>{renderInlineMarkdown(headingText, `h1-${i}`)}</span>
        </h1>
      );
      i++;
      continue;
    }

    if (line.startsWith('## ') || line.startsWith('##\t')) {
      const headingText = line.replace(/^##\s+/, '');
      blocks.push(
        <h2
          key={`h2-${i}`}
          className="text-sm font-bold text-[#f3f4f6] border-b border-[#24283b] pb-1 mt-3 mb-1.5 flex items-center gap-1.5"
        >
          <span className="w-1 h-3 bg-cyan-400/70 rounded-full inline-block" />
          <span>{renderInlineMarkdown(headingText, `h2-${i}`)}</span>
        </h2>
      );
      i++;
      continue;
    }

    if (line.startsWith('### ') || line.startsWith('###\t')) {
      const headingText = line.replace(/^###\s+/, '');
      blocks.push(
        <h3
          key={`h3-${i}`}
          className="text-xs font-semibold text-cyan-300/95 mt-2.5 mb-1"
        >
          {renderInlineMarkdown(headingText, `h3-${i}`)}
        </h3>
      );
      i++;
      continue;
    }

    if (line.startsWith('#### ') || line.startsWith('####\t')) {
      const headingText = line.replace(/^####\s+/, '');
      blocks.push(
        <h4
          key={`h4-${i}`}
          className="text-xs font-medium text-gray-300 mt-2 mb-1"
        >
          {renderInlineMarkdown(headingText, `h4-${i}`)}
        </h4>
      );
      i++;
      continue;
    }

    // 4. Blockquotes (> ...)
    if (line.startsWith('>')) {
      const quoteLines: string[] = [];
      while (i < rawLines.length && rawLines[i].startsWith('>')) {
        quoteLines.push(rawLines[i].replace(/^>\s?/, ''));
        i++;
      }
      blocks.push(
        <blockquote
          key={`quote-${i}`}
          className="my-2 pl-3 py-1 border-l-2 border-cyan-500/60 bg-cyan-950/10 text-xs text-[#9ca3af] italic rounded-r"
        >
          {quoteLines.map((ql, qIdx) => (
            <div key={qIdx}>{renderInlineMarkdown(ql, `quote-${i}-${qIdx}`)}</div>
          ))}
        </blockquote>
      );
      continue;
    }

    // 5. Unordered List (- item, * item, + item)
    if (/^(\s*)[-*+]\s+/.test(line)) {
      const listItems: { text: string; indent: number }[] = [];
      while (i < rawLines.length && /^(\s*)[-*+]\s+/.test(rawLines[i])) {
        const match = rawLines[i].match(/^(\s*)[-*+]\s+(.*)$/);
        if (match) {
          listItems.push({
            indent: Math.floor(match[1].length / 2),
            text: match[2],
          });
        }
        i++;
      }
      blocks.push(
        <ul key={`ul-${i}`} className="my-1.5 space-y-1 text-xs">
          {listItems.map((item, lIdx) => (
            <li
              key={lIdx}
              style={{ marginLeft: `${item.indent * 14 + 14}px` }}
              className="list-disc text-[#9ca3af] leading-relaxed marker:text-cyan-500/60"
            >
              {renderInlineMarkdown(item.text, `ul-${i}-${lIdx}`)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 6. Ordered List (1. item, 2. item)
    if (/^(\s*)\d+\.\s+/.test(line)) {
      const listItems: { text: string; num: string }[] = [];
      while (i < rawLines.length && /^(\s*)\d+\.\s+/.test(rawLines[i])) {
        const match = rawLines[i].match(/^(\s*)(\d+)\.\s+(.*)$/);
        if (match) {
          listItems.push({
            num: match[2],
            text: match[3],
          });
        }
        i++;
      }
      blocks.push(
        <ol key={`ol-${i}`} className="my-1.5 space-y-1 text-xs list-decimal pl-5">
          {listItems.map((item, lIdx) => (
            <li
              key={lIdx}
              className="text-[#9ca3af] leading-relaxed marker:text-cyan-400 marker:font-mono marker:text-[10px]"
            >
              {renderInlineMarkdown(item.text, `ol-${i}-${lIdx}`)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 7. Markdown Table (| col | col |)
    if (line.startsWith('|') && line.endsWith('|')) {
      const tableLines: string[] = [];
      while (i < rawLines.length && rawLines[i].trim().startsWith('|') && rawLines[i].trim().endsWith('|')) {
        tableLines.push(rawLines[i].trim());
        i++;
      }
      if (tableLines.length >= 2) {
        const parseRow = (rowStr: string) =>
          rowStr
            .slice(1, -1)
            .split('|')
            .map((c) => c.trim());

        const headers = parseRow(tableLines[0]);
        const isDivider = tableLines[1].replace(/[\s|:-]/g, '').length === 0;
        const bodyRows = (isDivider ? tableLines.slice(2) : tableLines.slice(1)).map(parseRow);

        blocks.push(
          <div key={`table-${i}`} className="my-2.5 overflow-x-auto custom-scrollbar">
            <table className="min-w-full text-left text-xs border border-[#24283b] divide-y divide-[#24283b] rounded-lg">
              <thead className="bg-[#151824]">
                <tr>
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="px-3 py-1.5 font-semibold text-[#e5e7eb] border-r border-[#24283b] last:border-r-0">
                      {renderInlineMarkdown(h, `th-${i}-${hIdx}`)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#24283b] bg-[#0e1017]">
                {bodyRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-[#151824]/50 transition-colors">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="px-3 py-1.5 text-[#9ca3af] border-r border-[#24283b] last:border-r-0">
                        {renderInlineMarkdown(cell, `td-${i}-${rIdx}-${cIdx}`)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // 8. Empty lines
    if (!trimmed) {
      blocks.push(<div key={`blank-${i}`} className="h-1.5" />);
      i++;
      continue;
    }

    // 9. Standard Paragraph
    blocks.push(
      <p key={`p-${i}`} className="text-xs text-[#9ca3af] leading-relaxed my-1 min-h-[1.2em]">
        {renderInlineMarkdown(line, `p-${i}`)}
      </p>
    );
    i++;
  }

  return (
    <div className={`space-y-0.5 text-xs text-[#d1d5db] leading-relaxed select-text p-1 ${className}`}>
      {blocks}
    </div>
  );
};
