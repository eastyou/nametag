"""名单解析、校验与重名检测。"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

NAME_HEADERS = {"姓名", "名字", "学生姓名", "name"}
CLASS_HEADERS = {"班级", "班", "班别", "class"}
MAX_NAME_LENGTH = 20
MAX_CLASS_LENGTH = 20
MAX_FILE_BYTES = 5 * 1024 * 1024


class NameTagError(ValueError):
    """名单内容不合法。"""


@dataclass(frozen=True)
class Student:
    """一名学生：姓名、班级，以及它在名单中的行号。"""

    name: str
    klass: str = ""
    line: int = 0


def _looks_like_header(row: Sequence[str]) -> bool:
    first = row[0].strip().lower() if row else ""
    second = row[1].strip().lower() if len(row) > 1 else ""
    return first in NAME_HEADERS or second in CLASS_HEADERS


def _clean(value: str) -> str:
    return " ".join(value.split())


def parse_students(text: str, source: str = "<名单>") -> List[Student]:
    """解析 CSV 文本；表头可有可无，空行自动跳过。"""
    if not isinstance(text, str):
        raise NameTagError("名单内容必须是文本")
    text = text.lstrip("\ufeff")
    if not text.strip():
        raise NameTagError("%s 是空的，没有读到姓名" % source)

    rows = list(csv.reader(io.StringIO(text)))
    students: List[Student] = []
    header_checked = False

    for index, row in enumerate(rows, start=1):
        if not any(cell.strip() for cell in row):
            continue

        if not header_checked:
            header_checked = True
            if _looks_like_header(row):
                continue

        if len(row) > 2 and any(cell.strip() for cell in row[2:]):
            raise NameTagError("第 %d 行：最多两列（姓名,班级）" % index)

        name = _clean(row[0]) if row else ""
        if not name:
            raise NameTagError("第 %d 行：姓名不能为空" % index)
        if len(name) > MAX_NAME_LENGTH:
            raise NameTagError(
                "第 %d 行：姓名超过 %d 个字符" % (index, MAX_NAME_LENGTH)
            )

        klass = _clean(row[1]) if len(row) > 1 else ""
        if len(klass) > MAX_CLASS_LENGTH:
            raise NameTagError(
                "第 %d 行：班级超过 %d 个字符" % (index, MAX_CLASS_LENGTH)
            )

        students.append(Student(name=name, klass=klass, line=index))

    if not students:
        raise NameTagError("%s 里没有有效姓名，请检查是否只有表头" % source)
    return students


def decode_students(raw: bytes, source: str = "<名单>") -> List[Student]:
    """按 UTF-8（含 BOM）或 GBK 解码后解析。"""
    if not raw:
        raise NameTagError("%s 是空文件" % source)
    if len(raw) > MAX_FILE_BYTES:
        raise NameTagError("%s 超过 5 MB，请拆分后再试" % source)
    if b"\x00" in raw:
        raise NameTagError("%s 不是文本文件（检测到空字节）" % source)

    for encoding in ("utf-8-sig", "gb18030"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        return parse_students(text, source)
    raise NameTagError("%s 编码无法识别，请另存为 UTF-8 或 GBK" % source)


def load_students(path: str) -> List[Student]:
    """从文件读取名单；文件不存在时抛出 ``OSError``。"""
    data = Path(path).read_bytes()
    return decode_students(data, source=path)


def find_duplicates(
    students: Sequence[Student],
) -> List[Tuple[str, str, List[int]]]:
    """返回重名的（姓名, 班级, 行号列表），同一班级内同名才算重复。"""
    grouped: Dict[Tuple[str, str], List[int]] = {}
    for student in students:
        grouped.setdefault((student.name, student.klass), []).append(student.line)
    return [
        (name, klass, lines)
        for (name, klass), lines in grouped.items()
        if len(lines) > 1
    ]
