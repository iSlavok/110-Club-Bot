/** Text without tags, as Telegram counts and shows it. */
export function telegramToPlainText(html: string): string {
  return new DOMParser().parseFromString(html, 'text/html').body.textContent;
}
