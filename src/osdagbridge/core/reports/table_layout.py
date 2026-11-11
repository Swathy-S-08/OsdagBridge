"""Keep generated tables inside the text area (no hanging into the margin).

Most tables in the report are written with fixed column widths in centimetres,
e.g. ``{|L{5.5cm}|L{10cm}|}``.  LaTeX adds ``2*\\tabcolsep`` of padding per
column plus the rule widths, so many of them end up 5-60 pt wider than the
text block and stick out of the right margin.

``fit_table_widths`` is run once on the finished document string.  For every
``longtable`` / ``tabular`` whose columns *all* have an explicit width, it
scales those widths down (only if needed) so the whole table fits.
"""
import re

TEXT_WIDTH_PT = 450.7      # A4, geometry margin=1in  ->  595.28 - 2*72.27
SAFETY_PT = 1.5
TABCOLSEP_PT = 6.0         # \setlength{\tabcolsep}{6pt} in the preamble
RULE_PT = 0.5              # \setlength{\arrayrulewidth}{0.5pt}
_UNIT_PT = {"cm": 28.4528, "mm": 2.84528, "pt": 1.0, "in": 72.27}
_WIDTH = re.compile(r"^\s*([\d.]+)\s*(cm|mm|pt|in)\s*$")
_BEGIN = re.compile(r"\\begin\{(longtable|tabular)\}(\[[^\]]*\])?\{")


def _match_brace(s, i):
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "\\":
            continue
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j
    raise ValueError("unbalanced braces in column spec")


def _parse_spec(spec):
    """Return (columns, rules) or None when any column has no fixed width.

    ``columns`` is a list of (start, end, number, unit) giving the position of
    each width number inside ``spec``.
    """
    cols, rules, i, n = [], 0, 0, len(spec)
    while i < n:
        c = spec[i]
        if c == "|":
            rules += 1
            i += 1
        elif c in "<>@!":                      # skip their {...} argument
            if i + 1 >= n or spec[i + 1] != "{":
                return None
            i = _match_brace(spec, i + 1) + 1
        elif c in "pmbLCR":
            if i + 1 >= n or spec[i + 1] != "{":
                return None
            end = _match_brace(spec, i + 1)
            m = _WIDTH.match(spec[i + 2:end])
            if not m:
                return None
            cols.append((i + 2, end, float(m.group(1)), m.group(2)))
            i = end + 1
        elif c.isspace():
            i += 1
        else:                                  # l, c, r, X, ... : unknown width
            return None
    return (cols, rules) if cols else None


def _fit_spec(spec):
    parsed = _parse_spec(spec)
    if parsed is None or "@" in spec:
        return spec
    cols, rules = parsed
    widths = [num * _UNIT_PT[unit] for _, _, num, unit in cols]
    fixed = len(cols) * 2 * TABCOLSEP_PT + rules * RULE_PT
    natural = sum(widths) + fixed
    target = TEXT_WIDTH_PT - SAFETY_PT
    if natural <= target:
        return spec
    f = (target - fixed) / sum(widths)
    out, last = [], 0
    for (a, b, num, unit) in cols:
        out.append(spec[last:a])
        out.append(("%.3f" % (num * f)).rstrip("0").rstrip(".") + unit)
        last = b
    out.append(spec[last:])
    return "".join(out)


def fit_table_widths(tex):
    """Return ``tex`` with over-wide fixed-width tables scaled to fit."""
    out, pos = [], 0
    while True:
        m = _BEGIN.search(tex, pos)
        if not m:
            out.append(tex[pos:])
            break
        brace = m.end() - 1
        end = _match_brace(tex, brace)
        out.append(tex[pos:brace + 1])
        out.append(_fit_spec(tex[brace + 1:end]))
        pos = end
    return "".join(out)