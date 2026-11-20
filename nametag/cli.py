"""命令行入口：把学生名单变成可打印的折叠姓名桌牌。"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Optional, Sequence

from .model import NameTagError, find_duplicates, load_students
from .render import render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nametag",
        description="姓名桌牌生成器：名单 CSV 生成 A4 折叠桌牌，前后两面镜像",
    )
    parser.add_argument("--version", action="version", version="nametag 0.1.0")
    parser.add_argument("-i", "--input", required=True, help="名单 CSV，两列为姓名,班级")
    parser.add_argument(
        "-o", "--output", default="姓名桌牌.html", help="输出 HTML 路径"
    )
    parser.add_argument("--columns", type=int, default=2, help="每页列数，1~4，默认 2")
    parser.add_argument("--rows", type=int, default=2, help="每页行数，1~4，默认 2")
    parser.add_argument("--title", default="姓名桌牌", help="文档标题")
    parser.add_argument(
        "--strict", action="store_true", help="发现重名时直接报错，不生成文件"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        students = load_students(args.input)
    except NameTagError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取名单失败: %s" % exc, file=sys.stderr)
        return 1

    duplicates = find_duplicates(students)
    for name, klass, lines in duplicates:
        label = "%s（%s）" % (name, klass) if klass else name
        print(
            "提示: 重名 %s 出现在第 %s 行"
            % (label, "、".join(str(line) for line in lines)),
            file=sys.stderr,
        )
    if duplicates and args.strict:
        print("错误: 名单中有重名，已按 --strict 要求中止", file=sys.stderr)
        return 2

    try:
        page = render_html(
            students,
            columns=args.columns,
            rows=args.rows,
            title=args.title,
        )
    except NameTagError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    per_page = args.columns * args.rows
    pages = int(math.ceil(len(students) / per_page))
    print(
        "已生成 %s：共 %d 人，每页 %d 张，共 %d 页"
        % (args.output, len(students), per_page, pages)
    )
    print("打印后沿虚线对折，姓名一面朝外即可立在桌上")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
