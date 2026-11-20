"""Tests for theme.py - the single source of truth for report styling."""
import pathlib
import re

from _report_modules import load

theme = load("theme")
_REPORTS = (pathlib.Path(__file__).resolve().parents[2]
            / "src" / "osdagbridge" / "core" / "reports")
_CHAPTERS = sorted(_REPORTS.glob("chap*.py")) + [_REPORTS / "live_load_tables.py",
                                                 _REPORTS / "executive_summary.py"]


def _preamble():
    return theme.build_preamble("Proj", "J-1", "2026-01-01", "Rev 0")


def test_text_width_follows_page_geometry():
    assert theme.TEXT_WIDTH_PT == round(theme.PAGE_WIDTH_PT - 2 * theme.MARGIN_PT, 1)
    assert theme.TEXT_WIDTH_PT == 450.7


def test_preamble_uses_theme_values():
    pre = _preamble()
    assert "footskip=%gpt" % theme.FOOTSKIP_PT in pre
    assert "\\setlength{\\tabcolsep}{%gpt}" % theme.TABCOLSEP_PT in pre
    assert pre.rstrip().endswith("\\begin{document}")


def test_every_theme_colour_is_defined_in_the_preamble():
    pre = _preamble()
    for name, hexval in theme.COLOURS.items():
        assert "\\definecolor{%s}{HTML}{%s}" % (name, hexval) in pre


def test_chapter_macros_and_colours_are_defined():
    pre = _preamble()
    used_macros, used_colours = set(), set()
    for f in _CHAPTERS:
        src = f.read_text(encoding="utf-8")
        used_macros |= set(re.findall(r"\\+(rowgap(?:large)?|tabcolsep(?:compact|tight|narrow)|arraystretchairy)\b", src))
        used_colours |= set(re.findall(r"textcolor\{\{?([A-Za-z]+)\}?\}", src))
    for m in used_macros:
        assert "\\newcommand{\\%s}" % m in pre, m
    for c in used_colours:
        assert c in theme.COLOURS, c


def test_no_hardcoded_style_literals_left_in_chapters():
    banned = [r"\[6pt\]", r"\[8pt\]", r"textcolor\{\{?(red|black|blue)\}?\}",
              r"tabcolsep\}\{[0-9.]+pt\}", r"arraystretch\}\{[0-9.]+\}"]
    for f in _CHAPTERS:
        src = f.read_text(encoding="utf-8")
        for pat in banned:
            assert not re.search(pat, src), "%s still contains %s" % (f.name, pat)