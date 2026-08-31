import type { ReactNode } from 'react';

// A small, dependency-free renderer for the constrained markdown subset the
// AI Agent Assist is instructed to use: bold (**), italic (* or _),
// underline (__), inline code (backticks), "- " bullet lists, "1. "
// numbered lists, and blank-line-separated paragraphs.
//
// Deliberately builds React elements directly instead of parsing to HTML -
// this is chat content that can echo raw database values (customer names,
// ticket subjects, etc.), so there is no dangerouslySetInnerHTML anywhere
// in this file and never should be.

const INLINE_RE = /`([^`]+)`|\*\*([^*]+)\*\*|__([^_]+)__|\*([^*]+)\*|_([^_]+)_/g;

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let i = 0;
  INLINE_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = INLINE_RE.exec(text)) !== null) {
    if (match.index > lastIndex) nodes.push(text.slice(lastIndex, match.index));
    const key = `${keyPrefix}-${i++}`;
    if (match[1] !== undefined) {
      nodes.push(
        <code key={key} className="px-1 py-0.5 rounded bg-slate-100 dark:bg-gray-900 font-data text-[12px]">
          {match[1]}
        </code>
      );
    } else if (match[2] !== undefined) {
      nodes.push(<strong key={key} className="font-semibold">{match[2]}</strong>);
    } else if (match[3] !== undefined) {
      nodes.push(<u key={key}>{match[3]}</u>);
    } else {
      nodes.push(<em key={key}>{match[4] ?? match[5]}</em>);
    }
    lastIndex = INLINE_RE.lastIndex;
  }
  if (lastIndex < text.length) nodes.push(text.slice(lastIndex));
  return nodes;
}

const isBulletLine = (line: string) => /^\s*[-*]\s+/.test(line);
const isNumberedLine = (line: string) => /^\s*\d+\.\s+/.test(line);
const stripBullet = (line: string) => line.replace(/^\s*[-*]\s+/, '');
const stripNumber = (line: string) => line.replace(/^\s*\d+\.\s+/, '');

export function MarkdownLite({ text }: { text: string }) {
  const blocks = text.trim().split(/\n{2,}/);

  return (
    <>
      {blocks.map((block, bi) => {
        const lines = block.split('\n').filter(l => l.trim().length > 0);
        if (lines.length === 0) return null;

        if (lines.every(isBulletLine)) {
          return (
            <ul key={bi} className={`list-disc pl-4 space-y-1 ${bi > 0 ? 'mt-2' : ''}`}>
              {lines.map((line, li) => (
                <li key={li}>{renderInline(stripBullet(line), `${bi}-${li}`)}</li>
              ))}
            </ul>
          );
        }

        if (lines.every(isNumberedLine)) {
          return (
            <ol key={bi} className={`list-decimal pl-4 space-y-1 ${bi > 0 ? 'mt-2' : ''}`}>
              {lines.map((line, li) => (
                <li key={li}>{renderInline(stripNumber(line), `${bi}-${li}`)}</li>
              ))}
            </ol>
          );
        }

        return (
          <p key={bi} className={bi > 0 ? 'mt-2' : ''}>
            {lines.map((line, li) => (
              <span key={li}>
                {renderInline(line, `${bi}-${li}`)}
                {li < lines.length - 1 && <br />}
              </span>
            ))}
          </p>
        );
      })}
    </>
  );
}
