import type { JSONContent } from '@tiptap/react';

/** Telegram limit on the message text without tags. */
export const TELEGRAM_TEXT_MAX_LEN = 4096;

const LINK_SCHEMES = new Set(['http:', 'https:', 'tg:', 'mailto:']);
// Outermost first, so marks always nest the same way; code goes innermost, it cannot contain others.
const MARK_TAGS: [mark: string, open: string, close: string][] = [
  ['bold', '<b>', '</b>'],
  ['italic', '<i>', '</i>'],
  ['underline', '<u>', '</u>'],
  ['strike', '<s>', '</s>'],
  ['spoiler', '<span class="tg-spoiler">', '</span>'],
  ['code', '<code>', '</code>'],
];
const TAG_MARKS: Record<string, string> = {
  b: 'bold',
  strong: 'bold',
  i: 'italic',
  em: 'italic',
  u: 'underline',
  ins: 'underline',
  s: 'strike',
  strike: 'strike',
  del: 'strike',
  'tg-spoiler': 'spoiler',
  code: 'code',
};

const escapeText = (text: string) =>
  text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const escapeAttr = (text: string) => escapeText(text).replaceAll('"', '&quot;');

/** An address typed without a scheme gets https://; one Telegram would refuse gets null. */
export function normalizeHref(href: string): string | null {
  const trimmed = href.trim();
  const withScheme = /^[a-z][a-z\d+.-]*:/i.test(trimmed) ? trimmed : `https://${trimmed}`;
  try {
    return LINK_SCHEMES.has(new URL(withScheme).protocol) ? withScheme : null;
  } catch {
    return null;
  }
}

/** Editor document → message text in Telegram HTML: blocks become lines, marks become tags. */
export function editorToTelegram(doc: JSONContent): string {
  return (doc.content ?? []).map(blockToTelegram).join('\n');
}

function blockToTelegram(block: JSONContent): string {
  switch (block.type) {
    case 'codeBlock': {
      const code = escapeText(textOf(block));
      const language = block.attrs?.language as string | null | undefined;
      return language
        ? `<pre><code class="language-${escapeAttr(language)}">${code}</code></pre>`
        : `<pre>${code}</pre>`;
    }
    case 'blockquote':
      return `<blockquote>${(block.content ?? []).map(blockToTelegram).join('\n')}</blockquote>`;
    default:
      return (block.content ?? []).map(inlineToTelegram).join('');
  }
}

function inlineToTelegram(node: JSONContent): string {
  if (node.type === 'hardBreak') {
    return '\n';
  }
  let html = escapeText(node.text ?? '');
  const marks = new Set((node.marks ?? []).map((mark) => mark.type));
  for (const [mark, open, close] of MARK_TAGS.toReversed()) {
    if (marks.has(mark)) {
      html = `${open}${html}${close}`;
    }
  }
  const link = node.marks?.find((mark) => mark.type === 'link');
  const href = normalizeHref((link?.attrs?.href as string | undefined) ?? '');
  return link && href ? `<a href="${escapeAttr(href)}">${html}</a>` : html;
}

function textOf(node: JSONContent): string {
  return (node.content ?? [])
    .map((child) => child.text ?? (child.type === 'hardBreak' ? '\n' : ''))
    .join('');
}

/** Message text in Telegram HTML → editor document; a line break starts a new paragraph. */
export function telegramToEditor(html: string): JSONContent {
  const body = new DOMParser().parseFromString(html, 'text/html').body;
  return { type: 'doc', content: blocksOf(body.childNodes) };
}

type Mark = NonNullable<JSONContent['marks']>[number];

// Mirrors editorToTelegram: lines are joined by "\n", and a quote or code block takes a line of its own.
function blocksOf(nodes: NodeListOf<ChildNode>): JSONContent[] {
  const blocks: JSONContent[] = [];
  let line: JSONContent[] = [];
  // lineOpen is false right after a block: the next "\n" only separates it from what follows.
  const state = { lineOpen: true };
  const endLine = () => {
    blocks.push(line.length ? { type: 'paragraph', content: line } : { type: 'paragraph' });
    line = [];
  };
  const addText = (text: string, marks: Mark[]) => {
    text.split('\n').forEach((part, index) => {
      if (index > 0) {
        if (state.lineOpen) {
          endLine();
        }
        state.lineOpen = true;
      }
      if (part) {
        state.lineOpen = true;
        line.push(
          marks.length ? { type: 'text', text: part, marks } : { type: 'text', text: part },
        );
      }
    });
  };
  const walk = (node: ChildNode, marks: Mark[]) => {
    if (node.nodeType === Node.TEXT_NODE) {
      addText(node.textContent ?? '', marks);
      return;
    }
    if (!(node instanceof Element)) {
      return;
    }
    const tag = node.tagName.toLowerCase();
    if (tag === 'pre' || tag === 'blockquote') {
      if (line.length) {
        endLine();
      }
      blocks.push(
        tag === 'pre'
          ? codeBlockOf(node)
          : { type: 'blockquote', content: blocksOf(node.childNodes) },
      );
      state.lineOpen = false;
      return;
    }
    const mark = markOf(node, tag);
    node.childNodes.forEach((child) => {
      walk(child, mark ? [...marks, mark] : marks);
    });
  };
  nodes.forEach((node) => {
    walk(node, []);
  });
  if (state.lineOpen || blocks.length === 0) {
    endLine();
  }
  return blocks;
}

function markOf(element: Element, tag: string): Mark | null {
  if (tag === 'a') {
    return { type: 'link', attrs: { href: element.getAttribute('href') } };
  }
  if (tag === 'span') {
    return element.classList.contains('tg-spoiler') ? { type: 'spoiler' } : null;
  }
  const type = TAG_MARKS[tag];
  return type ? { type } : null;
}

function codeBlockOf(pre: Element): JSONContent {
  const code = pre.querySelector('code');
  const language = /language-(\S+)/.exec(code?.className ?? '')?.[1] ?? null;
  const text = pre.textContent;
  return {
    type: 'codeBlock',
    attrs: { language },
    content: text ? [{ type: 'text', text }] : [],
  };
}

/** Text without tags, as Telegram counts and shows it. */
export function telegramToPlainText(html: string): string {
  return new DOMParser().parseFromString(html, 'text/html').body.textContent;
}

/** Telegram counts the limit in UTF-16 code units, the same as JavaScript string length. */
export function telegramTextLength(html: string): number {
  return telegramToPlainText(html).length;
}
