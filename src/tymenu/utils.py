import emoji
from markupsafe import Markup
from markdown import markdown
import bleach


def label_is_required(text, is_required=True):
    # Add a star emoji if this field is required.
    star = emoji.emojize("<sup>:star2:</sup>", language="alias", variant="emoji_type")
    if is_required:
        text = f"{text} {star}"
    return Markup(text)


def clean_markdown_to_html(value: str, emojify=True) -> str:
    allowed_tags = [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "code",
        "em",
        "i",
        "li",
        "ol",
        "pre",
        "strong",
        "ul",
        "h1",
        "h2",
        "h3",
        "p",
    ]
    cleaned = bleach.linkify(
        bleach.clean(
            markdown(value, output_format="html"),
            tags=allowed_tags,
            strip=True,
        )
    )
    if emojify:
        cleaned = emojify_str(cleaned)
    return cleaned


def emojify_str(s: str) -> str:
    return emoji.emojize(s, language="alias", variant="emoji_type")
