"""Helper: import a module from osdagbridge.core.reports without its heavy package init.

The reports package ``__init__`` pulls in the whole report generator.  The modules
under test only need their siblings (e.g. ``theme``), so when the real package
cannot be imported we register a light stand-in package that points at the same
folder.  If the real package imports fine, it is used as is.
"""
import importlib
import pathlib
import sys
import types

_REPORTS = (pathlib.Path(__file__).resolve().parents[2]
            / "src" / "osdagbridge" / "core" / "reports")


def load(name):
    full = "osdagbridge.core.reports." + name
    try:
        return importlib.import_module(full)
    except Exception:
        for key in [k for k in sys.modules if k == "osdagbridge" or k.startswith("osdagbridge.")]:
            del sys.modules[key]
        for pkg, path in (("osdagbridge", _REPORTS.parents[1]),
                          ("osdagbridge.core", _REPORTS.parent),
                          ("osdagbridge.core.reports", _REPORTS)):
            stub = types.ModuleType(pkg)
            stub.__path__ = [str(path)]
            sys.modules[pkg] = stub
        return importlib.import_module(full)