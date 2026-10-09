import type { SheetIssueResponse } from '@/shared/api';

function columnName(column: string): string {
  return column === '' ? 'без заголовка' : `«${column}»`;
}

export function describeIssue(issue: SheetIssueResponse): string {
  const column = columnName(issue.column);
  const row = issue.row ?? '?';
  const value = issue.value ?? '';
  switch (issue.kind) {
    case 'unknown_column':
      return `Столбец ${column} отмечен, но блока с таким заголовком в клубе нет`;
    case 'missing_column':
      return `У блока со столбцом ${column} нет столбца в таблице`;
    case 'duplicate_column':
      return `Столбец ${column} отмечен дважды, учтён только первый`;
    case 'invalid_value':
      return `Столбец ${column}, строка ${row}: «${value}» — не VK id, пропущено`;
    case 'duplicate':
      return `Столбец ${column}, строка ${row}: VK id ${value} повторяется`;
  }
}
