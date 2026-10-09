import { describe, expect, it } from 'vitest';

import { describeIssue } from './issues';

describe('describeIssue', () => {
  it('points to the cell for value problems', () => {
    expect(describeIssue({ kind: 'invalid_value', column: 'Блок 5', row: 12, value: 'id42' })).toBe(
      'Столбец «Блок 5», строка 12: «id42» — не VK id, пропущено',
    );
    expect(describeIssue({ kind: 'duplicate', column: 'Блок 5', row: 7, value: '42' })).toBe(
      'Столбец «Блок 5», строка 7: VK id 42 повторяется',
    );
  });

  it('names columns, including ones without a header', () => {
    expect(describeIssue({ kind: 'unknown_column', column: '', row: null, value: null })).toBe(
      'Столбец без заголовка отмечен, но блока с таким заголовком в клубе нет',
    );
    expect(
      describeIssue({ kind: 'missing_column', column: 'Блок 6', row: null, value: null }),
    ).toContain('«Блок 6»');
    expect(
      describeIssue({ kind: 'duplicate_column', column: 'Блок 5', row: null, value: null }),
    ).toContain('отмечен дважды');
  });
});
