"""theme.py - single source of truth for the visual style of the design report.

Every layout rule and visual attribute of the generated report lives here:
page geometry, fonts, colours, header/footer, table padding and rules, figure
widths and the chart palette.  Nothing else in the report code should type a
margin, colour, padding or figure width by hand.

How the values reach the report
-------------------------------
* The LaTeX preamble is built here (``build_preamble``).  It also defines a few
  LaTeX *macros* and *colours* from the values below, so the chapter files can
  use them by name without importing anything:

      \\rowgap  \\rowgaplarge  \\tabcolsepcompact  \\tabcolsepnarrow ...
      \\textcolor{statusfail}{FAIL}   \\textcolor{statuspass}{PASS}

  To restyle the whole report, change the value here; the macro follows.
* Python code that draws things itself (charts, table-width fitting, figure
  widths) imports the constants directly:

      from osdagbridge.core.reports import theme

Keep this file free of imports from the rest of the package so every module
can import it safely.
"""


def _pt(value):
    """6.0 -> '6pt', 0.5 -> '0.5pt'."""
    return "%gpt" % value


# --------------------------------------------------------------------------- #
# Document and page
# --------------------------------------------------------------------------- #
DOCUMENT_CLASS = "report"
FONT_SIZE_PT = 12
PAPER = "a4paper"
MARGIN = "1in"
FOOTSKIP_PT = 38          # keeps body text clear of the footer rule
LINE_STRETCH = 1.15

PAGE_WIDTH_PT = 595.276   # A4, 210 mm
MARGIN_PT = 72.27         # 1 in
# Width available to a table/figure; derived so it follows the margins.
TEXT_WIDTH_PT = round(PAGE_WIDTH_PT - 2 * MARGIN_PT, 1)
TABLE_FIT_SAFETY_PT = 1.5   # tables are fitted this far inside the text width

CAPTION_OPTIONS = [
    "labelfont=bf",
    "justification=raggedright",
    "singlelinecheck=false",
    "format=plain",
]

# --------------------------------------------------------------------------- #
# Colours (HTML hex, no '#').  Each becomes a LaTeX colour of the same name.
# --------------------------------------------------------------------------- #
COLOURS = {
    "osdagGreen": "91B014",   # accent: header/footer rules
    "statusfail": "FF0000",   # FAIL text, UR > 1.0
    "statuspass": "000000",   # PASS text
    "notetext":   "000000",   # footer note text
    "loginfo":    "0000FF",   # design log: information
    "logerror":   "FF0000",   # design log: error
}

# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #
TABCOLSEP_PT = 6.0            # default cell padding left/right
ARRAY_STRETCH = 1.12          # default row height factor
RULE_PT = 0.5                 # table rule thickness
EXTRA_ROW_PT = 0.6            # small extra height for every row
LT_PRE_PT = 0                 # space before a longtable
LT_POST_PT = 6                # space after a longtable
TABLE_NEEDSPACE = r"5\baselineskip"   # a table float needs this much room

ROW_GAP_PT = 6               # gap after a table row  (\\[6pt])
ROW_GAP_LARGE_PT = 8         # gap after a table row in the project-info tables

# Named alternative paddings used by a few tables.
TABCOLSEP_COMPACT_PT = 4
TABCOLSEP_TIGHT_PT = 3.5
TABCOLSEP_NARROW_PT = 3
ARRAY_STRETCH_AIRY = 1.25

# --------------------------------------------------------------------------- #
# Header / footer
# --------------------------------------------------------------------------- #
HEAD_RULE_PT = 1
HEAD_RULE_AFTER_PT = 2
FOOT_RULE_PT = 1
FOOT_RULE_AFTER_PT = 6
FOOT_RULE_RAISE_PT = 8        # pulls the rule up under the body text
SD_NOTE_RAISE_PT = 20         # "* Software default value" note, raised above the rule
SD_NOTE_GAP_PT = 4
HEADER_SEPARATOR = r" $|$ "
FOOTER_LEFT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
FOOTER_RIGHT = r"Page \thepage\ of \pageref{LastPage}"
SD_NOTE_TEXT = r"* Software default value"

# --------------------------------------------------------------------------- #
# Figures (widths are LaTeX lengths)
# --------------------------------------------------------------------------- #
FIG_WIDTH_FULL = r"\textwidth"
FIG_WIDTH_DEFAULT = r"0.9\textwidth"
FIG_WIDTH_DRAWING = r"0.85\textwidth"
FIG_WIDTH_UR_CHARTS = r"0.92\textwidth"
FIG_WIDTH_QTY_CHARTS = r"0.78\textwidth"
PLACEHOLDER_BOX_WIDTH = r"0.97\textwidth"
FIG_WIDTH_THIRD = r"0.31\textwidth"      # three drawings side by side

# --------------------------------------------------------------------------- #
# Charts (matplotlib) - hex with '#'
# --------------------------------------------------------------------------- #
CHART_DPI = 200
CHART_FONT_SIZE = 8
CHART_LIMIT_COLOUR = "#e00000"        # UR = 1.0 line
CHART_FAIL_EDGE = "#c0392b"
CHART_ELEMENT_COLOURS = {
    "girder": "#2f6f9f",
    "deck":   "#6a9f58",
    "cb":     "#d08c2e",
    "ed":     "#7b5ea7",
}
CHART_TEXT = "#222222"                # value labels
CHART_MUTED_TEXT = "#666666"          # "N/A" / "not in BOM" labels
CHART_STEEL = "#2f6f9f"
CHART_BRACING = "#d08c2e"
CHART_DIAPHRAGM = "#7b5ea7"
CHART_CONCRETE = "#8c8c8c"
CHART_REBAR = "#b5532e"


# --------------------------------------------------------------------------- #
# LaTeX pieces generated from the values above
# --------------------------------------------------------------------------- #
def latex_colour_definitions():
    return "\n".join("\\definecolor{%s}{HTML}{%s}" % (name, hexval)
                     for name, hexval in COLOURS.items())


def latex_style_macros():
    """Macros the chapter files use instead of typing the values."""
    macros = {
        "rowgap": _pt(ROW_GAP_PT),
        "rowgaplarge": _pt(ROW_GAP_LARGE_PT),
        "tabcolsepcompact": _pt(TABCOLSEP_COMPACT_PT),
        "tabcolseptight": _pt(TABCOLSEP_TIGHT_PT),
        "tabcolsepnarrow": _pt(TABCOLSEP_NARROW_PT),
        "arraystretchairy": "%g" % ARRAY_STRETCH_AIRY,
    }
    return "\n".join("\\newcommand{\\%s}{%s}" % (k, v) for k, v in macros.items())


def build_preamble(pn, jn, rd, rv):
    """Complete LaTeX preamble (up to and including ``\\begin{document}``).

    ``pn``, ``jn``, ``rd`` and ``rv`` are the project name, job number, date and
    version, already escaped for LaTeX.
    """
    head_rule = ("\\renewcommand{\\headrule}{\\color{osdagGreen}\\hrule width\\headwidth "
                 "height %s \\vspace{%s}}" % (_pt(HEAD_RULE_PT), _pt(HEAD_RULE_AFTER_PT)))
    foot_rule_line = ("\\color{osdagGreen}\\hrule width\\headwidth height %s \\vspace{%s}"
                      % (_pt(FOOT_RULE_PT), _pt(FOOT_RULE_AFTER_PT)))
    header_lines = [
        "  \\fancyhead[L]{" + pn + HEADER_SEPARATOR + jn + "}",
        "  \\fancyhead[R]{" + rd + HEADER_SEPARATOR + rv + "}",
    ]
    footer_lines = [
        "  \\fancyfoot[L]{" + FOOTER_LEFT + "}",
        "  \\fancyfoot[R]{" + FOOTER_RIGHT + "}",
    ]
    footrule_with_note = [
        "  \\renewcommand{\\footrule}{%",
        "    \\ifbool{hasSDonPage}{%",
        "      \\vspace{-%s}%%" % _pt(SD_NOTE_RAISE_PT),
        "      \\hbox to \\headwidth{\\textcolor{notetext}{\\footnotesize\\textit{"
        + SD_NOTE_TEXT + "}}\\hfil}%",
        "      \\vspace{%s}%%" % _pt(SD_NOTE_GAP_PT),
        "    }{%",
        "      \\vspace{-%s}%%" % _pt(FOOT_RULE_RAISE_PT),
        "    }%",
        "    " + foot_rule_line + "%",
        "  }",
    ]

    def standard_style(name):
        return (["\\fancypagestyle{%s}{" % name, "  \\fancyhf{}"] + header_lines + footer_lines
                + ["  " + head_rule] + footrule_with_note + ["}"])

    first_style = (["\\fancypagestyle{firstpage}{", "  \\fancyhf{}",
                    "  \\renewcommand{\\headrulewidth}{0pt}"] + footer_lines
                   + ["  \\renewcommand{\\footrule}{\\vspace{-%s}%s}"
                      % (_pt(FOOT_RULE_RAISE_PT), foot_rule_line), "}"])

    caption_setup = "\\captionsetup{\n" + ",\n".join("    " + o for o in CAPTION_OPTIONS) + "\n}"

    parts = [
        "",
        "\\documentclass[%dpt,%s]{%s}" % (FONT_SIZE_PT, PAPER, DOCUMENT_CLASS),
        "",
        "% Packages",
        "\\usepackage[%s, margin=%s, footskip=%s]{geometry}  "
        "%% footskip: keep body text clear of the footer rule" % (PAPER, MARGIN, _pt(FOOTSKIP_PT)),
        "\\usepackage{graphicx}",
        "\\usepackage{amsmath}",
        "\\usepackage{amssymb}",
        "\\usepackage{booktabs}",
        "\\usepackage{array}",
        "\\usepackage{tabularx}",
        "\\usepackage{float}",
        "\\usepackage{fancyhdr}",
        "\\usepackage[hidelinks]{hyperref}",
        "\\usepackage{xcolor}",
        "\\usepackage{setspace}",
        "\\usepackage{enumitem}",
        "\\usepackage{caption}",
        "",
        caption_setup,
        "\\usepackage{subcaption}",
        "\\usepackage{multirow}",
        "\\usepackage{colortbl}",
        "\\usepackage{longtable}",
        "\\setlength{\\LTleft}{\\fill}",
        "\\setlength{\\LTright}{\\fill}",
        "\\usepackage{titlesec}",
        "\\usepackage{titletoc}",
        "\\usepackage{lastpage}",
        "\\usepackage{makecell}",
        "\\usepackage{etoolbox}",
        "\\usepackage{needspace}",
        "",
        "\\numberwithin{table}{chapter}",
        "\\numberwithin{figure}{chapter}",
        "% Table layout and spacing: consistent padding, row height, and longtable pre/post skips",
        "\\setlength{\\tabcolsep}{%s}" % _pt(TABCOLSEP_PT),
        "\\renewcommand{\\arraystretch}{%g}" % ARRAY_STRETCH,
        "\\setlength{\\LTpre}{%s}" % _pt(LT_PRE_PT),
        "\\setlength{\\LTpost}{%s}" % _pt(LT_POST_PT),
        "% Table rules (outline thickness) and small extra row height for clarity",
        "\\setlength{\\arrayrulewidth}{%s}" % _pt(RULE_PT),
        "\\setlength{\\extrarowheight}{%s}" % _pt(EXTRA_ROW_PT),
        "",
        "% Prevent tables from overflowing past the page bottom:",
        "% if fewer than 5 baseline-skips remain, break to the next page first.",
        "\\BeforeBeginEnvironment{table}{\\needspace{%s}}" % TABLE_NEEDSPACE,
        "% (no \\needspace before longtable: combined with repeating headers it leaves a",
        "% stray '(continued)' header at the top of a page; longtable breaks fine on its own)",
        "",
        "% Colours and style macros defined from theme.py",
        latex_colour_definitions(),
        latex_style_macros(),
        "",
    ]
    parts += standard_style("main")
    parts += standard_style("plain")
    parts += first_style
    parts += [
        "\\pagestyle{main}",
        "\\setstretch{%g}" % LINE_STRETCH,
        "",
        "% Custom Commands",
        "\\newcommand{\\placeholder}[1]{\\textit{\\textless #1\\textgreater}}",
        "\\newcommand{\\todo}[1]{\\colorbox{yellow}{TODO: #1}}",
        "\\newcolumntype{L}[1]{>{\\raggedright\\arraybackslash}p{#1}}",
        "\\newcolumntype{C}[1]{>{\\centering\\arraybackslash}p{#1}}",
        "\\newcolumntype{R}[1]{>{\\raggedleft\\arraybackslash}p{#1}}",
        "",
        "% Software-default asterisk",
        "\\newcommand{\\sdstar}{\\textsuperscript{*}}",
        "\\newbool{hasSDonPage}",
        "\\boolfalse{hasSDonPage}",
        "\\newcommand{\\markSD}{\\global\\booltrue{hasSDonPage}}",
        "\\renewcommand{\\sdstar}{\\textsuperscript{*}\\markSD{}}",
        "\\AddToHook{shipout/before}{\\global\\boolfalse{hasSDonPage}}",
        "",
        "\\title{\\Large\\textbf{OsdagBridge} \\\\ \\normalsize Open Source Software for Steel Girder Bridge Design"
        " \\\\ \\vspace{2cm} \\large Design Report}",
        "\\author{}",
        "\\date{}",
        "",
        "\\begin{document}",
    ]
    return "\n".join(parts)