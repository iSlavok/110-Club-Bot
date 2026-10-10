/** Russian plural form: plural(1, 'день', 'дня', 'дней') → 'день', 3 → 'дня', 11 → 'дней'. */
export function plural(n: number, one: string, few: string, many: string): string {
  const lastTwo = n % 100;
  const last = n % 10;
  if (last === 1 && lastTwo !== 11) {
    return one;
  }
  if (last >= 2 && last <= 4 && (lastTwo < 12 || lastTwo > 14)) {
    return few;
  }
  return many;
}
