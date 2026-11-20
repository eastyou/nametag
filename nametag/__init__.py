"""nametag：A4 折叠姓名桌牌生成器。"""

from __future__ import annotations

from .model import (
    Student,
    NameTagError,
    decode_students,
    find_duplicates,
    load_students,
    parse_students,
)
from .render import card_size, name_font_size, render_card, render_html

__version__ = "0.1.0"

__all__ = [
    "NameTagError",
    "Student",
    "card_size",
    "decode_students",
    "find_duplicates",
    "load_students",
    "name_font_size",
    "parse_students",
    "render_card",
    "render_html",
    "__version__",
]
