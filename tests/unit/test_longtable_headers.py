"""Tests for repeating longtable headers in the generated LaTeX report."""
import importlib.util
import pathlib
import re

# Load the module by path so the test does not need the Qt/analysis stack.
_PATH = (pathlib.Path(__file__).resolve().parents[2]
         / "src" / "osdagbridge" / "core" / "reports" / "longtable_headers.py")
_spec = importlib.util.spec_from_file_location("longtable_headers", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
add_longtable_headers = _mod.add_longtable_headers


def _tables(tex):
    return re.findall(r"\\begin\{longtable\}.*?\\end\{longtable\}", tex, re.S)


SIMPLE = r"""
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Demo}}
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
a & 1 \\[6pt]
\hline
\end{longtable}
"""

MAKECELL_HEADER = r"""
\begin{longtable}{|>{\centering\arraybackslash}p{3cm}|c|}
\caption{\textbf{Demo2}}\\
\hline
\makecell{\textbf{Max}\\\textbf{(kN)}} & \textbf{Girder} \\
\hline
x & y \\
\hline
\end{longtable}
"""

ALREADY_OK = r"""
\begin{longtable}{|c|c|}
\caption{T}\\
\hline \textbf{A} & \textbf{B} \\ \hline
\endfirsthead
\hline \textbf{A} & \textbf{B} \\ \hline
\endhead
1 & 2 \\
\end{longtable}
"""

EMPTY_PAIR = r"""
\begin{longtable}{|c|c|}
\caption{T}\\
\hline \textbf{A} & \textbf{B} \\ \hline
\endfirsthead
\endhead
1 & 2 \\
\end{longtable}
"""

NO_HEADER = r"""
\begin{longtable}{|c|c|}
\caption{T}\\
\hline
Effective Span & 6950 \\
\hline
\end{longtable}
"""


def test_every_converted_table_has_head_blocks():
    out = add_longtable_headers(SIMPLE + MAKECELL_HEADER + EMPTY_PAIR)
    for t in _tables(out):
        assert t.count(r"\endfirsthead") == 1
        assert t.count(r"\endhead") == 1


def test_caption_gets_missing_row_terminator():
    out = add_longtable_headers(SIMPLE)
    assert re.search(r"\\caption\{\\textbf\{Demo\}\}\\\\", out)


def test_header_repeated_after_endfirsthead():
    t = _tables(add_longtable_headers(SIMPLE))[0]
    hdr = r"\textbf{parameter} & \textbf{value}"
    assert t.count(hdr) == 2
    assert t.index(hdr, t.index(r"\endfirsthead")) < t.index(r"\endhead")


def test_continued_label_uses_correct_column_count():
    t = _tables(add_longtable_headers(MAKECELL_HEADER))[0]
    assert r"\multicolumn{2}{l}" in t


def test_makecell_header_with_inner_backslashes_kept_whole():
    t = _tables(add_longtable_headers(MAKECELL_HEADER))[0]
    assert t.count(r"\makecell{\textbf{Max}\\\textbf{(kN)}}") == 2


def test_existing_header_kept_and_empty_pair_rebuilt():
    out = add_longtable_headers(ALREADY_OK)
    assert out.count(r"\textbf{A}") == 2          # header not duplicated
    assert out.count(r"\endhead") == 1
    t = _tables(add_longtable_headers(EMPTY_PAIR))[0]
    assert t.count(r"\textbf{A}") == 2


def test_table_without_header_row_is_left_without_heads():
    t = _tables(add_longtable_headers(NO_HEADER))[0]
    assert r"\endhead" not in t


def test_idempotent():
    once = add_longtable_headers(SIMPLE + MAKECELL_HEADER + NO_HEADER)
    assert add_longtable_headers(once) == once


MULTIROW_BODY = r"""
\begin{longtable}{|C{2cm}|C{3cm}|}
\caption{T}\\
\hline \textbf{Girder} & \textbf{Value} \\ \hline
\multirow{2}{*}{\makecell{G1}} & a \\[6pt]
\cline{2-2}
 & b \\[6pt]
\hline
\end{longtable}
"""


def test_multirow_label_kept_in_first_row_only():
    t = _tables(add_longtable_headers(MULTIROW_BODY))[0]
    assert r"\multirow" not in t
    assert t.count(r"\makecell{G1}") == 1

def test_closing_rule_added_at_page_breaks():
    for src in (SIMPLE, MAKECELL_HEADER, ALREADY_OK, EMPTY_PAIR):
        for t in _tables(add_longtable_headers(src)):
            assert t.count(r"\endfoot") == 1
            assert t.split(r"\endfoot")[0].rstrip().endswith(r"\hline")