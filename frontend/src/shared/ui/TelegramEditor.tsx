import '@mantine/tiptap/styles.css';

import { Input } from '@mantine/core';
import { Link, RichTextEditor, useRichTextEditorContext } from '@mantine/tiptap';
import { IconEyeOff } from '@tabler/icons-react';
import { Mark, useEditor, useEditorState } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import type { ReactNode } from 'react';

import { editorToTelegram, telegramToEditor } from '@/shared/lib/telegram-html';

import classes from './telegram.module.css';

const Spoiler = Mark.create({
  name: 'spoiler',
  parseHTML() {
    return [{ tag: 'span.tg-spoiler' }, { tag: 'tg-spoiler' }];
  },
  renderHTML() {
    return ['span', { class: 'tg-spoiler' }, 0];
  },
  addKeyboardShortcuts() {
    return {
      'Mod-Shift-p': () => this.editor.commands.toggleMark(this.name),
    };
  },
});

// Only what Telegram can show: no headings, lists or rules.
const EXTENSIONS = [
  StarterKit.configure({
    heading: false,
    bulletList: false,
    orderedList: false,
    listItem: false,
    listKeymap: false,
    horizontalRule: false,
    link: false,
  }),
  Link.configure({ openOnClick: false }),
  Spoiler,
];

const LABELS = {
  boldControlLabel: 'Жирный',
  italicControlLabel: 'Курсив',
  underlineControlLabel: 'Подчёркнутый',
  strikeControlLabel: 'Зачёркнутый',
  codeControlLabel: 'Моноширинный',
  codeBlockControlLabel: 'Блок кода',
  blockquoteControlLabel: 'Цитата',
  linkControlLabel: 'Ссылка',
  unlinkControlLabel: 'Убрать ссылку',
  clearFormattingControlLabel: 'Убрать оформление',
  undoControlLabel: 'Отменить',
  redoControlLabel: 'Вернуть',
  linkEditorInputLabel: 'Адрес ссылки',
  linkEditorInputPlaceholder: 'https://…',
  linkEditorSave: 'Сохранить',
  linkEditorExternalLink: 'Открывать в новой вкладке',
  linkEditorInternalLink: 'Открывать в этой вкладке',
};

interface TelegramEditorProps {
  label: string;
  /** Telegram HTML to start from; the editor keeps its own state afterwards. */
  initialValue: string;
  onChange: (html: string) => void;
  error?: ReactNode;
}

export function TelegramEditor({ label, initialValue, onChange, error }: TelegramEditorProps) {
  const editor = useEditor({
    extensions: EXTENSIONS,
    content: initialValue ? telegramToEditor(initialValue) : '',
    onUpdate: ({ editor: updated }) => {
      onChange(editorToTelegram(updated.getJSON()));
    },
  });

  return (
    <Input.Wrapper label={label} error={error} withAsterisk>
      <RichTextEditor editor={editor} labels={LABELS} className={classes.message} mt={4}>
        <RichTextEditor.Toolbar>
          <RichTextEditor.ControlsGroup>
            <RichTextEditor.Bold />
            <RichTextEditor.Italic />
            <RichTextEditor.Underline />
            <RichTextEditor.Strikethrough />
            <SpoilerControl />
          </RichTextEditor.ControlsGroup>
          <RichTextEditor.ControlsGroup>
            <RichTextEditor.Link />
            <RichTextEditor.Unlink />
          </RichTextEditor.ControlsGroup>
          <RichTextEditor.ControlsGroup>
            <RichTextEditor.Code />
            <RichTextEditor.CodeBlock />
            <RichTextEditor.Blockquote />
          </RichTextEditor.ControlsGroup>
          <RichTextEditor.ControlsGroup>
            <RichTextEditor.ClearFormatting />
            <RichTextEditor.Undo />
            <RichTextEditor.Redo />
          </RichTextEditor.ControlsGroup>
        </RichTextEditor.Toolbar>
        <RichTextEditor.Content mih={160} />
      </RichTextEditor>
    </Input.Wrapper>
  );
}

function SpoilerControl() {
  const { editor } = useRichTextEditorContext();
  const active = useEditorState({
    editor,
    selector: ({ editor: current }) => current?.isActive('spoiler') ?? false,
  });
  return (
    <RichTextEditor.Control
      aria-label="Скрытый текст"
      title="Скрытый текст"
      active={active === true}
      onClick={() => editor?.chain().focus().toggleMark('spoiler').run()}
    >
      <IconEyeOff size={16} stroke={1.5} />
    </RichTextEditor.Control>
  );
}
