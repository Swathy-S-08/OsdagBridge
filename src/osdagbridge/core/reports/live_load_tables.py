"""Chapter 3 live-load tables (vehicle live loads and footpath live load).

``live_load_tables(input_dict)`` returns LaTeX for two separate tables:

* the first table (Vehicle Live Loads)  - one row per vehicle *selected in the
  Loading tab* (Additional Inputs): total load, impact factor, braking load
  (considered / value / eccentricity) and centrifugal force.
* the second table (Footpath Live Load)  - mode, pressure and code reference.

Values come from the IRC 6 helpers in ``irc6_2017``.  Anything that cannot be
determined from the code or the grillage model (e.g. total load of Class AA and
Class 70R Bogie) is left as an en-dash rather than guessed.
"""
from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_SPAN,
)
from osdagbridge.core.reports.report_utils import _tex

DASH = r"--"
BRAKING_FRACTION = 0.20      # IRC 6 Cl. 211.2: 20 % of the first train of load

# (label, selection key, kind) - kind selects the total-load / impact rules.
_VEHICLES = [
    ("Class A",             KEY_LL_IRC_CLASS_A,        "A"),
    ("Class 70R (Wheeled)", KEY_LL_IRC_70R_WHEELED,    "70R_W"),
    ("Class 70R (Tracked)", KEY_LL_IRC_70R_TRACKED,    "70R_T"),
    ("Class 70R (Bogie)",   KEY_LL_IRC_70R_BOGIE,      "70R_B"),
    ("Class AA (Wheeled)",  KEY_LL_IRC_AA_WHEELED,     "AA_W"),
    ("Class AA (Tracked)",  KEY_LL_IRC_AA_TRACKED,     "AA_T"),
    ("Class SV",            KEY_LL_IRC_CLASS_SV,       "SV"),
    ("Class Fatigue",       KEY_LL_IRC_CLASS_FATIGUE,  "FAT"),
]
_HEAVY = {"70R_W", "70R_T", "70R_B", "AA_W", "AA_T"}      # IRC 6 Cl. 208.3


def _selected(value):
    return value is True or str(value).strip().lower() in ("true", "yes", "1", "checked")


def _total_load_kN(kind, irc6):
    """Total vehicle load in kN, or None when no source defines it."""
    try:
        if kind == "A":
            return sum(irc6.cl_204_1_ClassA_vehicle()["wheel_loads"]) / 1000.0
        if kind == "70R_W":
            return sum(irc6.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]) / 1000.0
        if kind == "70R_T":
            d = irc6.cl_204_1_Class70R_vehicle_track()
            return d["wheel_loads_udl"] * (d["x"][-1] - d["x"][0]) * len(d["z"]) / 1000.0
        if kind == "SV":
            return float(irc6.cl_204_5_1_special_vehicle()["total_load_kN"])
        if kind == "FAT":
            return sum(irc6.cl_204_6_fatigue_load()["wheel_loads"]) / 1000.0
    except Exception:
        return None
    return None          # Class AA and 70R Bogie are not defined in the code base


def _impact_factor(kind, span_m, irc6):
    if span_m is None:
        return None
    try:
        if kind == "A":
            return 1.0 + irc6.cl_208_2_impact_factor(span_m)
        if kind in _HEAVY:
            return 1.0 + irc6.cl_208_3_impact_factor(span_m)
    except Exception:
        return None
    return None


def _num(value, fmt):
    return DASH if value is None else format(value, fmt)


def _vehicle_rows(input_dict, irc6):
    try:
        span_m = float(input_dict.get(KEY_SPAN))
    except (TypeError, ValueError):
        span_m = None
    ecc = input_dict.get(KEY_LL_ECCENTRICITY)
    ecc_str = _tex(ecc) if ecc not in (None, "") else DASH

    rows = []
    for label, key, kind in _VEHICLES:
        if not _selected(input_dict.get(key)):
            continue
        total = _total_load_kN(kind, irc6)
        considered = (_selected(input_dict.get(KEY_BL_IRC_CLASS_SV))
                      if kind == "SV" else True)
        braking = total * BRAKING_FRACTION if (considered and total is not None) else None
        rows.append([
            label,
            _num(total, ".1f"),
            _num(_impact_factor(kind, span_m, irc6), ".3f"),
            "Yes" if considered else "No",
            _num(braking, ".1f"),
            ecc_str if considered else DASH,
            "N/A",
        ])

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if isinstance(custom, list):
        for c in custom:
            name = c.get("name") if isinstance(c, dict) else c
            if not name:
                continue
            axles = c.get("axle_loads") if isinstance(c, dict) else None
            try:
                total = float(sum(axles)) if axles else None
            except (TypeError, ValueError):
                total = None
            rows.append([_tex(name), _num(total, ".1f"), DASH, DASH, DASH, DASH, "N/A"])
    return rows


def _vehicle_table(input_dict, irc6):
    rows = _vehicle_rows(input_dict, irc6)
    header = (r"\textbf{Vehicle} & \textbf{Total Load (kN)} & \textbf{Impact Factor} & "
              r"\textbf{Braking Considered?} & \textbf{Braking Value (kN)} & "
              r"\textbf{Braking Eccentricity (m)} & \textbf{Centri\-fugal Force (kN)} \\[6pt]")
    if rows:
        body = "\n".join(
            " & ".join(r) + r" \\[6pt]" + "\n" + r"\hline" for r in rows)
    else:
        body = (r"\multicolumn{7}{|c|}{No vehicle class selected} \\[6pt]" + "\n" + r"\hline")
    return (
        "\\vspace{1em}\n"
        "\\begin{longtable}{|L{2.6cm}|C{1.5cm}|C{1.4cm}|C{1.8cm}|C{1.7cm}|C{2.0cm}|C{2.0cm}|}\n"
        "\\caption{\\textbf{Live Loads (LL) --- Vehicle Live Loads}}\n"
        "\\hline\n" + header + "\n\\hline\n" + body + "\n"
        "\\end{longtable}\n\n"
        "\\noindent\\textit{Note: Vehicles shown are those selected in the Loading tab. "
        "Impact factors per IRC 6 Cl. 208. Braking value is "
        + str(int(BRAKING_FRACTION * 100)) +
        "\\% of the vehicle total load (IRC 6 Cl. 211.2, first train), acting at the "
        "eccentricity shown above the deck. Centrifugal force (IRC 6 Cl. 212) applies "
        "to curved bridges only; no curvature is specified, so it is not applicable. "
        "A dash (--) means the value is not defined for that vehicle.}\n"
    )


def _footpath_table(input_dict, irc6):
    footpath = str(input_dict.get(KEY_FOOTPATH) or "").strip()
    mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE) or "").strip()
    value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)

    if footpath.lower() == "none":
        mode_s, pressure, ref = "Not applicable (no footpath)", DASH, DASH
    elif mode.lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            pressure = "%.3f" % irc6.cl_206_1_footway_load()
        except Exception:
            pressure = DASH
        mode_s, ref = "As per IRC 6", "IRC 6 Cl. 206.1"
    elif value not in (None, ""):
        mode_s, pressure, ref = "Custom (user-defined)", _tex(value), "User input"
    else:
        mode_s, pressure, ref = (_tex(mode) if mode else DASH), DASH, DASH

    return (
        "\\vspace{1em}\n"
        "\\begin{longtable}{|L{4.0cm}|L{4.5cm}|C{3.2cm}|L{3.3cm}|}\n"
        "\\caption{\\textbf{Live Loads (LL) --- Footpath Live Load}}\n"
        "\\hline\n"
        "\\textbf{Footpath} & \\textbf{Pressure Mode} & \\textbf{Pressure (kN/m\\textsuperscript{2})} "
        "& \\textbf{Reference} \\\\[6pt]\n"
        "\\hline\n"
        + (_tex(footpath) if footpath else DASH) + " & " + mode_s + " & " + pressure
        + " & " + ref + " \\\\[6pt]\n"
        "\\hline\n"
        "\\end{longtable}\n"
    )


def live_load_tables(input_dict):
    """LaTeX for the vehicle and footpath live-load tables ."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    return _vehicle_table(input_dict, IRC6_2017) + "\n" + _footpath_table(input_dict, IRC6_2017)