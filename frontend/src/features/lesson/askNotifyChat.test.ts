import { describe, expect, it } from 'vitest';

import { notifyChatTitle } from './askNotifyChat';

describe('notifyChatTitle', () => {
  it('names the change and the kind of the lesson', () => {
    expect(notifyChatTitle(['rescheduled'], 'lesson')).toBe('Сообщить в чат о переносе урока?');
    expect(notifyChatTitle(['cancelled'], 'curator_call')).toBe(
      'Сообщить в чат об отмене созвона?',
    );
  });

  it('joins several changes', () => {
    expect(notifyChatTitle(['rescheduled', 'deadline_changed'], 'lesson')).toBe(
      'Сообщить в чат о переносе урока и новом дедлайне ДЗ?',
    );
  });
});
