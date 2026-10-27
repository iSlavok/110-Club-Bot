import { expect, it } from 'vitest';

import { telegramToPlainText } from './telegram-html';

it('reads the text without tags, entities decoded', () => {
  expect(telegramToPlainText('<b>Привет</b> &amp; <a href="https://x.example">пока</a>')).toBe(
    'Привет & пока',
  );
});
