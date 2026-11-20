"""Utilization-ratio (UR = Demand / Capacity) bar charts for Section 5.5.

``build_ur_charts(rows, out_dir)`` draws two PNG charts from the rows of the
"Overall Design Check Summary" table and returns their file names:

* ``ur_by_element.png`` - governing (maximum) UR of each primary element
  (Steel Plate Girders, Concrete Deck Slab, Cross Bracing, End Diaphragms).
* ``ur_all_checks.png`` - UR of every individual check, coloured by element.

Both charts have the UR axis on the Y-axis and a red dashed line at UR = 1.0:
a bar above the line is a failing check, a bar on or below it passes.

Matplotlib's object-oriented API (``Figure`` + ``FigureCanvasAgg``) is used
instead of ``pyplot`` so it is safe to call from a worker thread and never
touches global GUI state.
"""
import os

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from . import theme

ELEMENTS = [
    # (key, display name, bar colour)
    ("girder", "Steel Plate Girders", theme.CHART_ELEMENT_COLOURS["girder"]),
    ("deck",   "Concrete Deck Slab",  theme.CHART_ELEMENT_COLOURS["deck"]),
    ("cb",     "Cross Bracing",       theme.CHART_ELEMENT_COLOURS["cb"]),
    ("ed",     "End Diaphragms",      theme.CHART_ELEMENT_COLOURS["ed"]),
]
_COLOUR = {k: c for k, _, c in ELEMENTS}
_NAME = {k: n for k, n, _ in ELEMENTS}
FAIL_EDGE = theme.CHART_FAIL_EDGE
LIMIT_COLOUR = theme.CHART_LIMIT_COLOUR


def element_of(label):
    """Map a Table 5.29 row label to one of the primary elements."""
    s = str(label).lower()
    if s.startswith("girder"):
        return "girder"
    if s.startswith("cross bracing"):
        return "cb"
    if s.startswith("end diaphragm"):
        return "ed"
    if s.startswith("deck") or "(slab)" in s:
        return "deck"
    return None


def _clean(label):
    """Table label (LaTeX) -> plain text for the chart."""
    return (str(label).replace("---", "-").replace(r"\&", "&")
            .replace("\\", "").replace("{", "").replace("}", "")
            .replace("  ", " ").strip())


def _save(fig, path):
    FigureCanvasAgg(fig)
    fig.savefig(path, dpi=theme.CHART_DPI, bbox_inches="tight", facecolor="white")


def _limit_line(ax):
    ax.axhline(1.0, color=LIMIT_COLOUR, linestyle="--", linewidth=1.6, zorder=3)


def _style(ax, ymax):
    ax.set_ylim(0, ymax)
    ax.set_ylabel("Utilization Ratio (Demand / Capacity)")
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def _bar(ax, x, value, colour):
    failing = value > 1.0
    ax.bar(x, value, width=0.62, color=colour, zorder=2,
           edgecolor=FAIL_EDGE if failing else colour,
           linewidth=1.8 if failing else 0.8,
           hatch="//" if failing else None)
    ax.text(x, value, "%.2f" % value, ha="center", va="bottom", fontsize=8.5,
            fontweight="bold", color=FAIL_EDGE if failing else theme.CHART_TEXT, zorder=5,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.8, alpha=0.9))


def _legend_handles(used_keys):
    h = [Patch(facecolor=_COLOUR[k], label=_NAME[k]) for k in used_keys]
    h.append(Patch(facecolor="white", edgecolor=FAIL_EDGE, hatch="//",
                   label="Fails (UR > 1.0)"))
    h.append(Line2D([0], [0], color=LIMIT_COLOUR, linestyle="--", linewidth=1.6,
                    label="UR = 1.0 limit"))
    return h


def _legend(ax, used_keys):
    """Legend above the plot area so it can never cover a bar."""
    ax.legend(handles=_legend_handles(used_keys), loc="lower center",
              bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=8, frameon=False)


def _by_element_chart(rows, path):
    best = {}
    for label, ur in rows:
        k = element_of(label)
        if k and ur is not None and (k not in best or ur > best[k]):
            best[k] = ur
    fig = Figure(figsize=(7.2, 3.0))
    ax = fig.add_subplot(111)
    top = max(list(best.values()) + [1.0])
    for i, (k, name, colour) in enumerate(ELEMENTS):
        if k in best:
            _bar(ax, i, best[k], colour)
        else:
            ax.text(i, 0.04 * top, "N/A\n(not designed)", ha="center", va="bottom",
                    fontsize=8, color=theme.CHART_MUTED_TEXT, zorder=4)
    _limit_line(ax)
    _style(ax, top * 1.18)
    ax.set_xlim(-0.6, len(ELEMENTS) - 0.4)
    ax.set_xticks(range(len(ELEMENTS)))
    ax.set_xticklabels([n.replace(" ", "\n", 1) for _, n, _ in ELEMENTS], fontsize=9)
    ax.set_title("Governing Utilization Ratio by Element", fontsize=11,
                 fontweight="bold", pad=34)
    _legend(ax, [k for k, _, _ in ELEMENTS if k in best])
    _save(fig, path)


def _all_checks_chart(rows, path):
    data = [(_clean(l), ur, element_of(l)) for l, ur in rows
            if ur is not None and element_of(l)]
    # Keep the element order of Table 5.29 (Girder, Deck, Cross Bracing, End
    # Diaphragm) whatever order the rows were produced in; the sort is stable.
    order = {k: i for i, (k, _, _) in enumerate(ELEMENTS)}
    data.sort(key=lambda d: order[d[2]])
    n = max(len(data), 1)
    fig = Figure(figsize=(max(7.2, 0.36 * n + 1.6), 3.8))
    ax = fig.add_subplot(111)
    top = max([d[1] for d in data] + [1.0])
    for i, (_, ur, k) in enumerate(data):
        _bar(ax, i, ur, _COLOUR[k])
    _limit_line(ax)
    _style(ax, top * 1.18)
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels([d[0] for d in data], rotation=45, ha="right", fontsize=8.5)
    ax.set_xlim(-0.7, len(data) - 0.3)
    ax.set_title("Utilization Ratio of All Design Checks", fontsize=11,
                 fontweight="bold", pad=34)
    _legend(ax, [k for k, _, _ in ELEMENTS if any(d[2] == k for d in data)])
    _save(fig, path)


def build_ur_charts(rows, out_dir):
    """Draw the UR charts into ``out_dir``.

    ``rows`` is a list of ``(label, ur)`` where ``ur`` is a float or ``None``
    (checks with no value, e.g. "design to be added").  Returns the list of
    PNG file names written, or ``[]`` when there is nothing to plot.
    """
    if not any(ur is not None and element_of(label) for label, ur in rows):
        return []
    os.makedirs(out_dir, exist_ok=True)
    names = ("ur_by_element.png", "ur_all_checks.png")
    _by_element_chart(rows, os.path.join(out_dir, names[0]))
    _all_checks_chart(rows, os.path.join(out_dir, names[1]))
    return list(names)