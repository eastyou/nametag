"""命令行入口的单元测试。"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from nametag.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.roster = self.tmp / "students.csv"
        self.roster.write_text(
            "姓名,班级\n张三,初二(3)班\n李四,初二(3)班\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, argv: list) -> tuple:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_generate_file(self) -> None:
        output = self.tmp / "tags.html"
        code, out, err = self.run_cli(["-i", str(self.roster), "-o", str(output)])
        self.assertEqual(code, 0, err)
        self.assertTrue(output.exists())
        self.assertIn("共 2 人", out)
        self.assertIn("每页 4 张", out)

    def test_output_is_utf8(self) -> None:
        output = self.tmp / "tags.html"
        self.assertEqual(
            self.run_cli(["-i", str(self.roster), "-o", str(output)])[0], 0
        )
        content = output.read_text(encoding="utf-8")
        self.assertIn("张三", content)

    def test_default_output_name(self) -> None:
        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            code, _, err = self.run_cli(["-i", str(self.roster)])
            self.assertEqual(code, 0, err)
            self.assertTrue((self.tmp / "姓名桌牌.html").exists())
        finally:
            os.chdir(cwd)

    def test_layout_option(self) -> None:
        output = self.tmp / "tags.html"
        self.assertEqual(
            self.run_cli(
                ["-i", str(self.roster), "-o", str(output), "--columns", "2", "--rows", "1"]
            )[0],
            0,
        )
        self.assertIn("--cols: 2; --rows: 1", output.read_text(encoding="utf-8"))

    def test_custom_title(self) -> None:
        output = self.tmp / "tags.html"
        self.assertEqual(
            self.run_cli(
                ["-i", str(self.roster), "-o", str(output), "--title", "初二(3)班"]
            )[0],
            0,
        )
        self.assertIn("<title>初二(3)班</title>", output.read_text(encoding="utf-8"))

    def test_duplicate_warning(self) -> None:
        roster = self.tmp / "dup.csv"
        roster.write_text("张三,一班\n张三,一班\n", encoding="utf-8")
        code, _, err = self.run_cli(["-i", str(roster), "-o", str(self.tmp / "d.html")])
        self.assertEqual(code, 0)
        self.assertIn("重名", err)
        self.assertIn("第 1、2 行", err)

    def test_strict_duplicate_aborts(self) -> None:
        roster = self.tmp / "dup.csv"
        roster.write_text("张三,一班\n张三,一班\n", encoding="utf-8")
        output = self.tmp / "d.html"
        code, _, err = self.run_cli(
            ["-i", str(roster), "-o", str(output), "--strict"]
        )
        self.assertEqual(code, 2)
        self.assertIn("--strict", err)
        self.assertFalse(output.exists())

    def test_invalid_roster(self) -> None:
        roster = self.tmp / "bad.csv"
        roster.write_text(",一班\n", encoding="utf-8")
        code, _, err = self.run_cli(["-i", str(roster)])
        self.assertEqual(code, 2)
        self.assertIn("姓名不能为空", err)

    def test_missing_file(self) -> None:
        code, _, err = self.run_cli(["-i", str(self.tmp / "none.csv")])
        self.assertEqual(code, 1)
        self.assertIn("读取名单失败", err)

    def test_invalid_layout(self) -> None:
        code, _, err = self.run_cli(["-i", str(self.roster), "--columns", "5"])
        self.assertEqual(code, 2)
        self.assertIn("列数", err)

    def test_write_failure(self) -> None:
        code, _, err = self.run_cli(["-i", str(self.roster), "-o", str(self.tmp)])
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_help_exits_zero(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
