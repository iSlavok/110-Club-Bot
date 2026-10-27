from html import escape
from html.parser import HTMLParser
from typing import Annotated, override
from urllib.parse import urlsplit

from pydantic import AfterValidator

# Telegram counts the message limit in UTF-16 code units of the text without tags.
TELEGRAM_TEXT_MAX_LEN = 4096
_SPOILER_CLASS = "tg-spoiler"
_CODE_LANGUAGE_PREFIX = "language-"
_LINK_SCHEMES = frozenset({"http", "https", "tg", "mailto"})
# Synonyms Telegram accepts, written back in one canonical form.
_CANONICAL_TAGS = {
    "b": "b",
    "strong": "b",
    "i": "i",
    "em": "i",
    "u": "u",
    "ins": "u",
    "s": "s",
    "strike": "s",
    "del": "s",
    "span": "span",
    "tg-spoiler": "span",
    "a": "a",
    "code": "code",
    "pre": "pre",
    "blockquote": "blockquote",
}
_TAGS_ONLY_ONCE_IN_STACK = frozenset({"a", "pre", "code", "blockquote"})


# Checks text against the Telegram HTML subset and writes it back escaped, with canonical tags.
def normalize_telegram_html(text: str) -> str:
    parser = _TelegramHtmlParser()
    parser.feed(text)
    parser.close()
    if parser.stack:
        raise ValueError(f"tag <{parser.stack[-1]}> is not closed")
    plain = "".join(parser.plain)
    if not plain.strip():
        raise ValueError("message is empty")
    if len(plain.encode("utf-16-le")) // 2 > TELEGRAM_TEXT_MAX_LEN:
        raise ValueError(f"message is longer than {TELEGRAM_TEXT_MAX_LEN} characters")
    return "".join(parser.out).strip()


def telegram_html_to_text(html: str) -> str:
    parser = _TelegramHtmlParser()
    parser.feed(html)
    parser.close()
    return "".join(parser.plain)


class _TelegramHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.out: list[str] = []
        self.plain: list[str] = []

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        canonical = _CANONICAL_TAGS.get(tag)
        if canonical is None:
            raise ValueError(f"tag <{tag}> is not supported by Telegram")
        if canonical in _TAGS_ONLY_ONCE_IN_STACK and canonical in self.stack:
            raise ValueError(f"tag <{tag}> cannot be nested in itself")
        parent = self.stack[-1] if self.stack else None
        if parent == "code" or (parent == "pre" and canonical != "code"):
            raise ValueError("code cannot contain other formatting")
        self.out.append(_open_tag(tag, canonical, dict(attrs), inside_pre=parent == "pre"))
        self.stack.append(canonical)

    @override
    def handle_endtag(self, tag: str) -> None:
        canonical = _CANONICAL_TAGS.get(tag)
        if not self.stack or self.stack[-1] != canonical:
            raise ValueError(f"closing tag </{tag}> does not match an open tag")
        self.stack.pop()
        self.out.append(f"</{canonical}>")

    @override
    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        raise ValueError(f"tag <{tag}/> is not supported by Telegram, use a line break")

    @override
    def handle_data(self, data: str) -> None:
        self.out.append(escape(data, quote=False))
        self.plain.append(data)

    @override
    def handle_comment(self, data: str) -> None:
        raise ValueError("comments are not supported by Telegram")

    @override
    def handle_decl(self, decl: str) -> None:
        raise ValueError("declarations are not supported by Telegram")

    @override
    def handle_pi(self, data: str) -> None:
        raise ValueError("processing instructions are not supported by Telegram")

    @override
    def unknown_decl(self, data: str) -> None:
        raise ValueError("declarations are not supported by Telegram")


def _open_tag(tag: str, canonical: str, attrs: dict[str, str | None], *, inside_pre: bool) -> str:
    match canonical:
        case "a":
            _allow_attrs(tag, attrs, {"href"})
            href = attrs.get("href")
            if not href or urlsplit(href).scheme.lower() not in _LINK_SCHEMES:
                raise ValueError("a link needs an http(s), tg or mailto address")
            return f'<a href="{escape(href)}">'
        case "span":
            if tag == "span":
                _allow_attrs(tag, attrs, {"class"})
                if attrs.get("class") != _SPOILER_CLASS:
                    raise ValueError(f'only <span class="{_SPOILER_CLASS}"> is supported by Telegram')
            else:
                _allow_attrs(tag, attrs, set())
            return f'<span class="{_SPOILER_CLASS}">'
        case "code":
            _allow_attrs(tag, attrs, {"class"} if inside_pre else set())
            language = attrs.get("class")
            if language is None:
                return "<code>"
            if not language.startswith(_CODE_LANGUAGE_PREFIX) or len(language) == len(_CODE_LANGUAGE_PREFIX):
                raise ValueError(f"code class must be {_CODE_LANGUAGE_PREFIX}<name>")
            return f'<code class="{escape(language)}">'
        case "blockquote":
            _allow_attrs(tag, attrs, {"expandable"})
            return "<blockquote expandable>" if "expandable" in attrs else "<blockquote>"
        case _:
            _allow_attrs(tag, attrs, set())
            return f"<{canonical}>"


def _allow_attrs(tag: str, attrs: dict[str, str | None], allowed: set[str]) -> None:
    extra = attrs.keys() - allowed
    if extra:
        raise ValueError(f"tag <{tag}> does not support the attribute {sorted(extra)[0]}")


# Message text in Telegram HTML: checked against what Telegram accepts and stored in canonical form.
type TelegramHtml = Annotated[str, AfterValidator(normalize_telegram_html)]
