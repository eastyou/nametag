"""桌牌 HTML 渲染的单元测试。"""

from __future__ import annotations

import unittest

from nametag.model import Student
from nametag.render import (
    MIN_FONT_MM,
    card_size,
    name_font_size,
    render_card,
    render_html,
    validate_layout,
)


def students(count: int) -> list:
    return [Student("学生%d" % index, "初二(3)班", index + 2) for index in range(count)]


class LayoutTest(unittest.TestCase):
    def test_card_size_two_by_two(self) -> None:
        width, height = card_size(2, 2)
        self.assertAlmostEqual(width, 93.0)
        self.assertAlmostEqual(height, 136.5)

    def test_card_size_one_by_one(self) -> None:
        width, height = card_size(1, 1)
        self.assertAlmostEqual(width, 190.0)
        self.assertAlmostEqual(height, 277.0)

    def test_columns_must_be_in_range(self) -> None:
        for value in (0, 5, -1):
            with self.assertRaises(Exception):
                validate_layout(value, 2)

    def test_rows_must_be_in_range(self) -> None:
        for value in (0, 5):
            with self.assertRaises(Exception):
                validate_layout(2, value)

    def test_layout_must_be_integer(self) -> None:
        with self.assertRaises(Exception):
            validate_layout(2.5, 2)  # type: ignore[arg-type]
        with self.assertRaises(Exception):
            validate_layout(True, 2)  # type: ignore[arg-type]


class FontSizeTest(unittest.TestCase):
    def test_longer_name_gets_smaller_font(self) -> None:
        short = name_font_size("张三", 93.0, 68.25)
        long = name_font_size("欧阳司马诸葛上官", 93.0, 68.25)
        self.assertGreater(short, long)

    def test_font_never_below_minimum(self) -> None:
        size = name_font_size("名" * 20, 44.5, 30.0)
        self.assertGreaterEqual(size, MIN_FONT_MM)

    def test_font_fits_half_height(self) -> None:
        size = name_font_size("张三", 190.0, 138.5)
        self.assertLessEqual(size, 32.0)

    def test_empty_name_rejected(self) -> None:
        with self.assertRaises(Exception):
            name_font_size("", 93.0, 68.25)

    def test_zero_size_rejected(self) -> None:
        with self.assertRaises(Exception):
            name_font_size("张三", 0, 68.25)


class RenderTest(unittest.TestCase):
    def test_card_has_two_halves(self) -> None:
        card = render_card(Student("张三", "一班"), 93.0, 136.5)
        self.assertEqual(card.count('class="half'), 2)
        self.assertIn(">张三</div>", card)

    def test_back_half_is_rotated(self) -> None:
        card = render_card(Student("张三", "一班"), 93.0, 136.5)
        self.assertIn("half back", card)
        self.assertIn("rotate(180deg)", render_html(students(2)))

    def test_fold_line_is_dashed(self) -> None:
        html = render_html(students(1))
        self.assertIn("dashed", html)

    def test_card_count(self) -> None:
        html = render_html(students(5), columns=2, rows=2)
        self.assertEqual(html.count('class="card"'), 5)

    def test_page_count(self) -> None:
        html = render_html(students(5), columns=2, rows=2)
        self.assertEqual(html.count('class="sheet"'), 2)

    def test_exact_page_count(self) -> None:
        html = render_html(students(4), columns=2, rows=2)
        self.assertEqual(html.count('class="sheet"'), 1)

    def test_grid_variables(self) -> None:
        html = render_html(students(2), columns=3, rows=1)
        self.assertIn("--cols: 3; --rows: 1", html)

    def test_title_is_escaped(self) -> None:
        html = render_html(students(1), title="<桌牌>")
        self.assertIn("&lt;桌牌&gt;", html)
        self.assertNotIn("<桌牌>", html)

    def test_name_is_escaped(self) -> None:
        html = render_html([Student("<张三>", "一班")])
        self.assertIn("&lt;张三&gt;", html)

    def test_class_is_escaped(self) -> None:
        html = render_html([Student("张三", "<一班>")])
        self.assertIn("&lt;一班&gt;", html)

    def test_empty_class_still_keeps_layout(self) -> None:
        html = render_html([Student("张三")])
        self.assertIn("&nbsp;", html)

    def test_print_styles(self) -> None:
        html = render_html(students(1))
        self.assertIn("@page { size: A4 portrait; margin: 0; }", html)
        self.assertIn(".toolbar { display: none; }", html)

    def test_doctype_and_language(self) -> None:
        html = render_html(students(1))
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html)

    def test_empty_students_rejected(self) -> None:
        with self.assertRaises(Exception):
            render_html([])

    def test_blank_title_rejected(self) -> None:
        with self.assertRaises(Exception):
            render_html(students(1), title="  ")

    def test_invalid_layout_rejected(self) -> None:
        with self.assertRaises(Exception):
            render_html(students(1), columns=0)


if __name__ == "__main__":
    unittest.main()
