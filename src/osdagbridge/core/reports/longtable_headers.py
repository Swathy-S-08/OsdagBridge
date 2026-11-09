"""Make every ``longtable`` in the generated report repeat its column header.

The chapter modules build tables as raw LaTeX strings.  Instead of editing
~50 hand-written tables, ``add_longtable_headers`` is run once on the finished
document string and rewrites each ``longtable`` into the canonical form::

    \\begin{longtable}{spec}
    \\caption{...}\\\\                 <- first page only
    \\hline  HEADER ROW  \\hline
    \\endfirsthead
    \\multicolumn{n}{l}{Table 5.4 (continued)}\\\\
    \\hline  HEADER ROW  \\hline      <- repeated on every following page
    \\endhead
    ...body...
    \\end{longtable}

It also repairs a ``\\caption`` that is not followed by ``\\\\`` (59 of the 61
captions in the baseline report), which otherwise makes pdflatex raise
"Misplaced \\noalign" errors that ``-interaction=nonstopmode`` silently hides.

Assumption: the first row of the table body (after an optional caption) is the
column-header row.  Tables that already have a non-empty ``\\endhead`` are left
unchanged.
"""
import re

_LT_BEGIN = "\\begin{longtable}"
_LT_END = "\\end{longtable}"
_ROW_END = re.compile(r"\\\\(\*)?(\[[^\]]*\])?")
_RULE = re.compile(r"\s*(\\hline|\\cline\{[^}]*\})")
_COL_LETTERS = "lcrpmbLCRX"


# --------------------------------------------------------------------------- #
# small LaTeX scanning helpers
# --------------------------------------------------------------------------- #
def _match_brace(s, i):
    """``s[i]`` is '{' -> index of its matching '}'."""
    depth = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "%":
            nl = s.find("\n", i)
            if nl < 0:
                break
            i = nl
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced braces in LaTeX table")


def _find_row_end(s, i):
    """Return (start, end) of the next depth-0 row terminator ``\\\\[..]``.

    ``\\\\`` inside braces (e.g. ``\\makecell{a\\\\b}``) is ignored.
    """
    depth = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "%":
            nl = s.find("\n", i)
            if nl < 0:
                return None
            i = nl
            continue
        if c == "\\":
            if depth == 0 and s.startswith("\\\\", i):
                return i, _ROW_END.match(s, i).end()
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    return None


def _take_rules(s, i):
    """Consume consecutive ``\\hline`` / ``\\cline{..}`` starting at i."""
    found = []
    while True:
        m = _RULE.match(s, i)
        if not m:
            break
        found.append(m.group(1))
        i = m.end()
    return "\n".join(found), i


def _count_cols(spec):
    n = depth = 0
    for c in spec:
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif depth == 0 and c in _COL_LETTERS:
            n += 1
    return n


# --------------------------------------------------------------------------- #
# one table
# --------------------------------------------------------------------------- #
def _process_body(body, spec):
    m = re.search(r"\\endfirsthead(.*?)\\endhead", body, re.S)
    if m and m.group(1).strip():
        # already has a working repeating header (e.g. Table 4.1)
        return body
    if m:  # empty \endfirsthead\endhead pair (Table 2.8) -> drop and rebuild
        body = body[:m.start()] + body[m.end():]

    i = len(body) - len(body.lstrip())
    caption = None
    if body.startswith("\\caption", i):
        j = i + len("\\caption")
        if body[j] == "*":
            j += 1
        if body[j] == "[":
            j = body.index("]", j) + 1
        k = _match_brace(body, j)
        caption = body[i:k + 1]
        i = k + 1
        j = i + len(body[i:]) - len(body[i:].lstrip())
        if body.startswith("\\\\", j):          # caption already ends with \\
            i = _ROW_END.match(body, j).end()

    pre, i = _take_rules(body, i)
    r = _find_row_end(body, i)
    header = body[i:r[1]] if r else ""
    if r is None or not re.search(r"\\textbf|\\multicolumn", header):
        # first row does not look like a header: only fix the caption (e.g. key/value tables)
        cap = (caption + "\\\\\n") if caption else ""
        return ("\n" + cap + (pre + "\n" if pre else "")
                + body[i:].lstrip())

    post, i = _take_rules(body, r[1])
    rest = body[i:]
    pre = pre or "\\hline"
    post = post or "\\hline"
    block = pre + "\n" + header.strip() + "\n" + post

    parts = ["\n"]
    if caption:
        parts.append(caption + "\\\\\n")
    parts.append(block + "\n\\endfirsthead\n")
    if caption:
        ncols = _count_cols(spec)
        parts.append(
            "\\multicolumn{%d}{l}{\\small\\textit{\\tablename~\\thetable{} (continued)}}\\\\\n"
            % ncols
        )
    parts.append(block + "\n\\endhead\n")
    parts.append(rest)
    return "".join(parts)


# --------------------------------------------------------------------------- #
# public entry point
# --------------------------------------------------------------------------- #
def add_longtable_headers(tex):
    """Return ``tex`` with header repetition added to every ``longtable``."""
    out, pos = [], 0
    while True:
        b = tex.find(_LT_BEGIN, pos)
        if b < 0:
            out.append(tex[pos:])
            break
        out.append(tex[pos:b])
        s0 = b + len(_LT_BEGIN)
        spec_end = _match_brace(tex, s0)
        spec = tex[s0 + 1:spec_end]
        e = tex.index(_LT_END, spec_end)
        body = tex[spec_end + 1:e]
        out.append(_LT_BEGIN + "{" + spec + "}" + _process_body(body, spec))
        out.append(_LT_END)
        pos = e + len(_LT_END)
    return "".join(out)