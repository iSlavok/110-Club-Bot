import pytest
from pydantic import TypeAdapter, ValidationError

from app.types import TELEGRAM_TEXT_MAX_LEN, TelegramHtml, telegram_html_to_text

adapter = TypeAdapter[str](TelegramHtml)


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("Привет!!\nДедлайн: 03.11 в 23:59", "Привет!!\nДедлайн: 03.11 в 23:59"),
        ("<b>a</b> <i>b</i> <u>c</u> <s>d</s>", "<b>a</b> <i>b</i> <u>c</u> <s>d</s>"),
        (
            "<strong>a</strong><em>b</em><ins>c</ins><del>d</del><strike>e</strike>",
            "<b>a</b><i>b</i><u>c</u><s>d</s><s>e</s>",
        ),
        (
            '<span class="tg-spoiler">x</span><tg-spoiler>y</tg-spoiler>',
            '<span class="tg-spoiler">x</span><span class="tg-spoiler">y</span>',
        ),
        (
            '<a href="https://example.com/a?b=1&amp;c=2">link</a>',
            '<a href="https://example.com/a?b=1&amp;c=2">link</a>',
        ),
        ("<code>x &lt; y</code>", "<code>x &lt; y</code>"),
        (
            '<pre><code class="language-python">print(1)</code></pre>',
            '<pre><code class="language-python">print(1)</code></pre>',
        ),
        ("<pre>a\nb</pre>", "<pre>a\nb</pre>"),
        (
            "<blockquote>q</blockquote><blockquote expandable>long</blockquote>",
            "<blockquote>q</blockquote><blockquote expandable>long</blockquote>",
        ),
        ("<b><i>both</i></b>", "<b><i>both</i></b>"),
        ("a < b & c > d", "a &lt; b &amp; c &gt; d"),
        ("\n\ntext\n\n", "text"),
    ],
)
def test_accepts_telegram_html(raw: str, normalized: str) -> None:
    assert adapter.validate_python(raw) == normalized


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   \n ",
        "<b></b>",
        "<p>paragraph</p>",
        "line<br>break",
        "line<br/>break",
        "<b>unclosed",
        "<b><i>crossed</b></i>",
        "closed</b>",
        "<span>plain span</span>",
        '<span class="other">x</span>',
        '<b class="x">x</b>',
        "<a>no address</a>",
        '<a href="javascript:alert(1)">x</a>',
        '<a href="/relative">x</a>',
        '<a href="https://a.example"><a href="https://b.example">x</a></a>',
        "<code><b>x</b></code>",
        "<pre><b>x</b></pre>",
        '<code class="language-python">inline with language</code>',
        '<pre><code class="python">x</code></pre>',
        "<blockquote><blockquote>x</blockquote></blockquote>",
        "<!-- comment -->text",
        "<script>alert(1)</script>",
    ],
)
def test_rejects_what_telegram_does_not_accept(raw: str) -> None:
    with pytest.raises(ValidationError):
        adapter.validate_python(raw)


def test_limits_the_text_without_tags() -> None:
    at_limit = "<b>" + "я" * TELEGRAM_TEXT_MAX_LEN + "</b>"
    assert adapter.validate_python(at_limit) == at_limit
    with pytest.raises(ValidationError):
        adapter.validate_python("я" * (TELEGRAM_TEXT_MAX_LEN + 1))


def test_counts_the_limit_in_utf16_units() -> None:
    with pytest.raises(ValidationError):
        adapter.validate_python("😀" * (TELEGRAM_TEXT_MAX_LEN // 2 + 1))


def test_text_drops_tags_and_entities() -> None:
    assert telegram_html_to_text('<b>Hi</b> <a href="https://example.com">there</a> &amp; you') == "Hi there & you"
