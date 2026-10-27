import type { JSONContent } from '@tiptap/react';
import { describe, expect, it } from 'vitest';

import {
  editorToTelegram,
  normalizeHref,
  telegramTextLength,
  telegramToEditor,
  telegramToPlainText,
} from './telegram-html';

const text = (value: string, ...marks: NonNullable<JSONContent['marks']>[]): JSONContent => ({
  type: 'text',
  text: value,
  ...(marks.length && { marks: marks.flat() }),
});
const paragraph = (...content: JSONContent[]): JSONContent =>
  content.length ? { type: 'paragraph', content } : { type: 'paragraph' };
const doc = (...content: JSONContent[]): JSONContent => ({ type: 'doc', content });
const bold = [{ type: 'bold' }];
const italic = [{ type: 'italic' }];
const link = (href: string) => [{ type: 'link', attrs: { href } }];

describe('editorToTelegram', () => {
  it('joins paragraphs with line breaks, keeping empty lines', () => {
    expect(
      editorToTelegram(doc(paragraph(text('Привет!!')), paragraph(), paragraph(text('ДЗ')))),
    ).toBe('Привет!!\n\nДЗ');
  });

  it('turns marks into Telegram tags, nested the same way every time', () => {
    const html = editorToTelegram(
      doc(
        paragraph(
          text('a', bold),
          text('b', [...italic, ...bold]),
          text('c', [{ type: 'underline' }, { type: 'strike' }]),
          text('d', [{ type: 'spoiler' }]),
          text('e', [{ type: 'code' }, ...bold]),
        ),
      ),
    );

    expect(html).toBe(
      '<b>a</b><b><i>b</i></b><u><s>c</s></u><span class="tg-spoiler">d</span><b><code>e</code></b>',
    );
  });

  it('escapes the text and the link address', () => {
    expect(
      editorToTelegram(doc(paragraph(text('a < b & "c"', link('https://x.example/?a=1&b="2"'))))),
    ).toBe('<a href="https://x.example/?a=1&amp;b=&quot;2&quot;">a &lt; b &amp; "c"</a>');
  });

  it('writes hard breaks, quotes and code blocks', () => {
    const html = editorToTelegram(
      doc(
        paragraph(text('a'), { type: 'hardBreak' }, text('b')),
        { type: 'blockquote', content: [paragraph(text('q1')), paragraph(text('q2'))] },
        { type: 'codeBlock', attrs: { language: null }, content: [text('x <\ny')] },
        { type: 'codeBlock', attrs: { language: 'python' }, content: [text('print(1)')] },
      ),
    );

    expect(html).toBe(
      'a\nb\n<blockquote>q1\nq2</blockquote>\n<pre>x &lt;\ny</pre>\n' +
        '<pre><code class="language-python">print(1)</code></pre>',
    );
  });

  it('drops a link Telegram would refuse and keeps its text', () => {
    expect(editorToTelegram(doc(paragraph(text('x', link('javascript:alert(1)')))))).toBe('x');
  });
});

describe('telegramToEditor', () => {
  it.each([
    ['lines and empty lines', doc(paragraph(text('Привет!!')), paragraph(), paragraph(text('ДЗ')))],
    [
      'marks and links',
      doc(paragraph(text('a', bold), text(' '), text('b', link('https://x.example/?a=1&b=2')))),
    ],
    [
      'quotes and code blocks between lines',
      doc(
        paragraph(text('before')),
        { type: 'blockquote', content: [paragraph(text('q1')), paragraph(text('q2'))] },
        { type: 'codeBlock', attrs: { language: 'python' }, content: [text('a\nb')] },
        paragraph(text('after')),
      ),
    ],
    ['a quote alone', doc({ type: 'blockquote', content: [paragraph(text('q'))] })],
  ])('reads back what the editor wrote: %s', (_, original) => {
    expect(telegramToEditor(editorToTelegram(original))).toEqual(original);
  });

  it('reads Telegram synonyms and spoilers', () => {
    expect(telegramToEditor('<strong>a</strong><tg-spoiler>b</tg-spoiler>')).toEqual(
      doc(paragraph(text('a', bold), text('b', [{ type: 'spoiler' }]))),
    );
  });

  it('splits a mark that spans lines', () => {
    expect(telegramToEditor('<b>a\nb</b>')).toEqual(
      doc(paragraph(text('a', bold)), paragraph(text('b', bold))),
    );
  });
});

describe('normalizeHref', () => {
  it.each([
    ['https://x.example', 'https://x.example'],
    ['lk.example/lesson/1', 'https://lk.example/lesson/1'],
    ['tg://resolve?domain=x', 'tg://resolve?domain=x'],
    ['mailto:a@x.example', 'mailto:a@x.example'],
    ['javascript:alert(1)', null],
    ['ftp://x.example', null],
  ])('%s → %s', (href, expected) => {
    expect(normalizeHref(href)).toBe(expected);
  });
});

it('counts the text without tags, entities decoded', () => {
  const html = '<b>Привет</b> &amp; <a href="https://x.example">пока</a>';

  expect(telegramToPlainText(html)).toBe('Привет & пока');
  expect(telegramTextLength(html)).toBe(13);
});
