"""Material-quantity bar charts for Chapter 7 (Material Take-off & Quantity Summary).

``build_quantity_charts(q, out_dir)`` reads the Bill-of-Materials values (the
same ``*_wt_total`` / ``*_vol_total`` strings that fill Table 7.1) and draws:

* ``qty_steel_tonnage.png``   - structural steel tonnage (MT) of Girders,
  Cross Bracing and End Diaphragms.
* ``qty_concrete_rebar.png``  - deck concrete volume (m^3) versus reinforcement
  steel weight (MT), in two panels with their own Y-axes (the units differ).

Anything that is "N.A." or missing is shown as "not in BOM" instead of a bar;
nothing is estimated here.

Matplotlib's object-oriented API (``Figure`` + ``FigureCanvasAgg``) is used
instead of ``pyplot`` so charts can be drawn from a worker thread.
"""
import os

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from . import theme

STEEL_COLOUR = theme.CHART_STEEL
BRACING_COLOUR = theme.CHART_BRACING
DIAPHRAGM_COLOUR = theme.CHART_DIAPHRAGM
CONCRETE_COLOUR = theme.CHART_CONCRETE
REBAR_COLOUR = theme.CHART_REBAR


def _num(value):
    """'14.06' -> 14.06 ; 'N.A.', '', None or garbage -> None."""
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _sum_if_any(values):
    nums = [v for v in values if v is not None]
    return sum(nums) if nums else None


def steel_tonnage(q):
    """(label, MT or None, colour) for Girders, Cross Bracing, End Diaphragms."""
    girders = _num(q.get("steel_girders_wt_total"))
    bracing = _sum_if_any([_num(q.get("bracing_top_wt_total")),
                           _num(q.get("bracing_bot_wt_total")),
                           _num(q.get("bracing_diag_wt_total"))])
    diaphragm = _num(q.get("end_diaphragm_wt_total"))   # not produced by the BOQ module yet
    return [
        ("Girders", girders, STEEL_COLOUR),
        ("Cross Bracing", bracing, BRACING_COLOUR),
        ("End Diaphragms", diaphragm, DIAPHRAGM_COLOUR),
    ]


def concrete_and_rebar(q):
    """(concrete volume m3 or None, reinforcement weight MT or None)."""
    return _num(q.get("concrete_deck_vol_total")), _num(q.get("rebar_deck_wt_total"))


def _save(fig, path):
    FigureCanvasAgg(fig)
    fig.savefig(path, dpi=theme.CHART_DPI, bbox_inches="tight", facecolor="white")


def _clean_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)


def _steel_chart(q, path):
    items = steel_tonnage(q)
    fig = Figure(figsize=(6.4, 3.3))
    ax = fig.add_subplot(111)
    top = max([v for _, v, _ in items if v is not None] + [1.0])
    for i, (label, val, colour) in enumerate(items):
        if val is None:
            ax.text(i, 0.03 * top, "not in BOM", ha="center", va="bottom",
                    fontsize=8.5, color=theme.CHART_MUTED_TEXT, style="italic")
        else:
            ax.bar(i, val, width=0.55, color=colour, zorder=2)
            ax.text(i, val, "%.2f MT" % val, ha="center", va="bottom", fontsize=9,
                    fontweight="bold", color=theme.CHART_TEXT, zorder=3)
    _clean_axes(ax)
    ax.set_ylim(0, top * 1.18)
    ax.set_xlim(-0.6, len(items) - 0.4)
    ax.set_xticks(range(len(items)))
    ax.set_xticklabels([l for l, _, _ in items], fontsize=9)
    ax.set_ylabel("Structural steel weight (MT)")
    ax.set_title("Structural Steel Tonnage", fontsize=11, fontweight="bold")
    _save(fig, path)


def _panel(ax, value, colour, fmt, ylabel, xlabel):
    """One single-bar panel with its own Y-axis (units differ between panels)."""
    if value is None:
        ax.text(0, 0.03, "not in BOM", ha="center", va="bottom", fontsize=8.5,
                color=theme.CHART_MUTED_TEXT, style="italic")
        top = 1.0
    else:
        ax.bar(0, value, width=0.5, color=colour, zorder=2)
        ax.text(0, value, fmt % value, ha="center", va="bottom", fontsize=9.5,
                fontweight="bold", color=theme.CHART_TEXT, zorder=3)
        top = value
    _clean_axes(ax)
    ax.set_ylim(0, top * 1.18)
    ax.set_xlim(-0.7, 0.7)
    ax.set_xticks([0])
    ax.set_xticklabels([xlabel], fontsize=9)
    ax.set_ylabel(ylabel)


def _concrete_rebar_chart(q, path):
    """Concrete volume and reinforcement weight side by side.

    The two quantities have different units, so each gets its own panel and
    Y-axis; a shared axis (or twin axes) would make the bars look comparable.
    """
    vol, wt = concrete_and_rebar(q)
    fig = Figure(figsize=(6.4, 3.3))
    ax1, ax2 = fig.subplots(1, 2)
    _panel(ax1, vol, CONCRETE_COLOUR, "%.2f m\u00b3", "Concrete volume (m\u00b3)",
           "Concrete (deck slab)")
    _panel(ax2, wt, REBAR_COLOUR, "%.2f MT", "Reinforcement steel weight (MT)",
           "Reinforcement steel")
    fig.suptitle("Concrete Volume vs. Reinforcement Steel Weight", fontsize=11,
                 fontweight="bold")
    fig.subplots_adjust(wspace=0.42)
    _save(fig, path)


def build_quantity_charts(q, out_dir):
    """Draw the quantity charts into ``out_dir``; return the PNG names written.

    ``q`` is the dict that also fills Table 7.1 (values are strings such as
    "14.06" or "N.A."). Returns ``[]`` when none of the plotted quantities is
    available (nothing to chart).
    """
    steel_vals = [v for _, v, _ in steel_tonnage(q) if v is not None]
    vol, wt = concrete_and_rebar(q)
    if not steel_vals and vol is None and wt is None:
        return []
    os.makedirs(out_dir, exist_ok=True)
    names = []
    if steel_vals:
        _steel_chart(q, os.path.join(out_dir, "qty_steel_tonnage.png"))
        names.append("qty_steel_tonnage.png")
    if vol is not None or wt is not None:
        _concrete_rebar_chart(q, os.path.join(out_dir, "qty_concrete_rebar.png"))
        names.append("qty_concrete_rebar.png")
    return names