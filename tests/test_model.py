"""名单解析与重名检测的单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nametag.model import (
    MAX_FILE_BYTES,
    MAX_NAME_LENGTH,
    NameTagError,
    Student,
    decode_students,
    find_duplicates,
    load_students,
    parse_students,
)


class ParseStudentsTest(unittest.TestCase):
    def test_two_columns(self) -> None:
        students = parse_students("张三,初二(3)班\n李四,初二(3)班\n")
        self.assertEqual([s.name for s in students], ["张三", "李四"])
        self.assertEqual(students[0].klass, "初二(3)班")
        self.assertEqual(students[0].line, 1)

    def test_single_column(self) -> None:
        students = parse_students("张三\n李四\n")
        self.assertEqual(len(students), 2)
        self.assertEqual(students[0].klass, "")

    def test_chinese_header_is_skipped(self) -> None:
        students = parse_students("姓名,班级\n张三,初二(3)班\n")
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].name, "张三")

    def test_name_header_variants(self) -> None:
        for header in ("名字", "学生姓名", "name", "Name"):
            students = parse_students("%s\n张三\n" % header)
            self.assertEqual(len(students), 1)

    def test_class_header_variants(self) -> None:
        for header in ("班级", "班", "班别", "class"):
            students = parse_students("姓名,%s\n张三,一班\n" % header)
            self.assertEqual(len(students), 1)

    def test_header_with_extra_columns(self) -> None:
        students = parse_students("姓名,班级,备注\n张三,初二(3)班\n")
        self.assertEqual(len(students), 1)

    def test_blank_lines_are_skipped(self) -> None:
        students = parse_students("\n\n张三,一班\n\n李四,一班\n\n")
        self.assertEqual(len(students), 2)

    def test_bom_is_removed(self) -> None:
        students = parse_students("\ufeff姓名,班级\n张三,一班\n")
        self.assertEqual(len(students), 1)

    def test_trailing_empty_columns(self) -> None:
        students = parse_students("张三,一班,\n")
        self.assertEqual(students[0].klass, "一班")

    def test_extra_columns_are_rejected(self) -> None:
        with self.assertRaises(NameTagError) as ctx:
            parse_students("张三,一班,备注\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_empty_name(self) -> None:
        with self.assertRaises(NameTagError) as ctx:
            parse_students("张三,一班\n,二班\n")
        self.assertIn("第 2 行", str(ctx.exception))
        self.assertIn("姓名不能为空", str(ctx.exception))

    def test_whitespace_is_collapsed(self) -> None:
        students = parse_students("  张   三 , 初二 3 班 \n")
        self.assertEqual(students[0].name, "张 三")
        self.assertEqual(students[0].klass, "初二 3 班")

    def test_name_too_long(self) -> None:
        with self.assertRaises(NameTagError) as ctx:
            parse_students("名" * (MAX_NAME_LENGTH + 1) + "\n")
        self.assertIn("姓名超过", str(ctx.exception))

    def test_class_too_long(self) -> None:
        with self.assertRaises(NameTagError):
            parse_students("张三," + "班" * 21 + "\n")

    def test_empty_text(self) -> None:
        with self.assertRaises(NameTagError):
            parse_students("   \n\n")

    def test_only_header(self) -> None:
        with self.assertRaises(NameTagError) as ctx:
            parse_students("姓名,班级\n")
        self.assertIn("没有有效姓名", str(ctx.exception))

    def test_windows_line_endings(self) -> None:
        students = parse_students("姓名,班级\r\n张三,一班\r\n")
        self.assertEqual(students[0].name, "张三")

    def test_quoted_class_with_comma(self) -> None:
        students = parse_students('张三,"初二(3)班,A 组"\n')
        self.assertEqual(students[0].klass, "初二(3)班,A 组")


class DecodeStudentsTest(unittest.TestCase):
    def test_utf8(self) -> None:
        students = decode_students("张三,一班\n".encode("utf-8"))
        self.assertEqual(students[0].name, "张三")

    def test_utf8_bom(self) -> None:
        students = decode_students("张三,一班\n".encode("utf-8-sig"))
        self.assertEqual(students[0].name, "张三")

    def test_gbk(self) -> None:
        students = decode_students("张三,一班\n".encode("gbk"))
        self.assertEqual(students[0].name, "张三")

    def test_empty_bytes(self) -> None:
        with self.assertRaises(NameTagError) as ctx:
            decode_students(b"")
        self.assertIn("空文件", str(ctx.exception))

    def test_binary_file(self) -> None:
        with self.assertRaises(NameTagError):
            decode_students(b"PK\x03\x04\x00\x00")

    def test_oversize_file(self) -> None:
        with self.assertRaises(NameTagError) as ctx:
            decode_students(b"a" * (MAX_FILE_BYTES + 1))
        self.assertIn("5 MB", str(ctx.exception))


class LoadStudentsTest(unittest.TestCase):
    def test_load_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "students.csv"
            path.write_text("姓名,班级\n张三,一班\n", encoding="utf-8")
            students = load_students(str(path))
            self.assertEqual(len(students), 1)

    def test_missing_file_raises_oserror(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_students("/no/such/students.csv")


class DuplicatesTest(unittest.TestCase):
    def test_same_name_same_class(self) -> None:
        students = parse_students("张三,一班\n李四,一班\n张三,一班\n")
        duplicates = find_duplicates(students)
        self.assertEqual(len(duplicates), 1)
        name, klass, lines = duplicates[0]
        self.assertEqual((name, klass), ("张三", "一班"))
        self.assertEqual(lines, [1, 3])

    def test_same_name_different_class(self) -> None:
        students = parse_students("张三,一班\n张三,二班\n")
        self.assertEqual(find_duplicates(students), [])

    def test_no_duplicates(self) -> None:
        students = parse_students("张三,一班\n李四,一班\n")
        self.assertEqual(find_duplicates(students), [])

    def test_student_defaults(self) -> None:
        student = Student("张三")
        self.assertEqual(student.klass, "")
        self.assertEqual(student.line, 0)


if __name__ == "__main__":
    unittest.main()
