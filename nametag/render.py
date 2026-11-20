"""把学生名单渲染成可打印的折叠姓名桌牌。"""

from __future__ import annotations

import html
import math
from typing import List, Sequence, Tuple

from .model import NameTagError, Student

PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0
PADDING_MM = 10.0
GAP_MM = 4.0
MIN_COLUMNS = 1
MAX_COLUMNS = 4
MIN_ROWS = 1
MAX_ROWS = 4
MAX_FONT_MM = 32.0
MIN_FONT_MM = 5.0


def validate_layout(columns: int, rows: int) -> None:
    """校验每页的行列数。"""
    for value, label, low, high in (
        (columns, "列数", MIN_COLUMNS, MAX_COLUMNS),
        (rows, "行数", MIN_ROWS, MAX_ROWS),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise NameTagError("%s必须是整数，收到 %r" % (label, value))
        if not low <= value <= high:
            raise NameTagError(
                "%s必须在 %d~%d 之间，收到 %d" % (label, low, high, value)
            )


def card_size(columns: int, rows: int) -> Tuple[float, float]:
    """单张桌牌的宽高（毫米），已扣除页边距和卡片间距。"""
    validate_layout(columns, rows)
    width = (PAGE_WIDTH_MM - 2 * PADDING_MM - GAP_MM * (columns - 1)) / columns
    height = (PAGE_HEIGHT_MM - 2 * PADDING_MM - GAP_MM * (rows - 1)) / rows
    return width, height


def name_font_size(name: str, card_width: float, half_height: float) -> float:
    """按姓名长度和半张卡片尺寸算出字号，保证不溢出。"""
    if not name:
        raise NameTagError("姓名不能为空")
    if card_width <= 0 or half_height <= 0:
        raise NameTagError("卡片尺寸必须大于 0")
    width_limit = (card_width - 10.0) / max(len(name), 1)
    size = min(half_height * 0.36, width_limit * 0.95, MAX_FONT_MM)
    return max(round(size, 2), MIN_FONT_MM)


def _half(student: Student, side: str, name_size: float) -> str:
    klass = (
        '<div class="klass" style="font-size: %.2fmm">%s</div>'
        % (max(min(name_size * 0.34, 8.0), 3.4), html.escape(student.klass))
        if student.klass
        else '<div class="klass">&nbsp;</div>'
    )
    return (
        '<div class="half %s">'
        '<div class="name" style="font-size: %.2fmm">%s</div>%s'
        "</div>"
        % (side, name_size, html.escape(student.name), klass)
    )


def render_card(student: Student, card_width: float, card_height: float) -> str:
    """生成一张折叠桌牌：上半张旋转 180°，下半张正常。"""
    size = name_font_size(student.name, card_width, card_height / 2)
    return (
        '<div class="card" style="width: %.2fmm; height: %.2fmm">%s%s</div>'
        % (
            card_width,
            card_height,
            _half(student, "back", size),
            _half(student, "front", size),
        )
    )


STYLE = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 8mm 0 12mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .toolbar {
    width: 210mm;
    margin: 0 auto 6mm;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 13px;
  }
  .toolbar strong { font-size: 15px; letter-spacing: 1px; }
  .toolbar span { color: #64748b; font-size: 12px; }
  .sheet {
    width: 210mm;
    height: 297mm;
    margin: 0 auto 8mm;
    padding: 10mm;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    display: grid;
    grid-template-columns: repeat(var(--cols), 1fr);
    grid-template-rows: repeat(var(--rows), 1fr);
    gap: 4mm;
    overflow: hidden;
    page-break-after: always;
    break-after: page;
  }
  .sheet:last-child { page-break-after: auto; break-after: auto; }
  .card {
    display: grid;
    grid-template-rows: 1fr 1fr;
    border: 0.25mm solid #e2e8f0;
    min-height: 0;
    break-inside: avoid;
  }
  .half {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.5mm;
    min-height: 0;
    padding: 1mm 2mm;
    overflow: hidden;
    text-align: center;
  }
  .back { transform: rotate(180deg); }
  .front { border-top: 0.45mm dashed #94a3b8; }
  .name {
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }
  .klass { color: #475569; letter-spacing: 0.06em; white-space: nowrap; }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""


def render_html(
    students: Sequence[Student],
    columns: int = 2,
    rows: int = 2,
    title: str = "姓名桌牌",
) -> str:
    """生成完整 HTML；参数不合法时抛出 ``NameTagError``。"""
    validate_layout(columns, rows)
    if not students:
        raise NameTagError("名单为空，至少需要一名学生")
    if not isinstance(title, str) or not title.strip():
        raise NameTagError("标题不能为空")

    width, height = card_size(columns, rows)
    per_page = columns * rows
    total_pages = int(math.ceil(len(students) / per_page))

    sheets: List[str] = []
    for page in range(total_pages):
        chunk = students[page * per_page : (page + 1) * per_page]
        cards = "".join(render_card(student, width, height) for student in chunk)
        sheets.append(
            '<section class="sheet" style="--cols: %d; --rows: %d">%s</section>'
            % (columns, rows, cards)
        )

    toolbar = (
        '<div class="toolbar"><strong>%s</strong>'
        "<span>共 %d 人 · 每页 %d 张 · 沿虚线对折，姓名朝外</span></div>"
        % (html.escape(title.strip()), len(students), per_page)
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n%s\n</body>\n</html>\n"
        % (
            html.escape(title.strip()),
            STYLE,
            toolbar,
            "\n".join(sheets),
        )
    )
