"""Verify that known_types.py stays in sync with the actual platform code.

Scans each platform file under custom_components/loxone/ for get_all() calls,
extracts the Loxone control type strings, and checks they all appear in
KNOWN_CONTROL_TYPES.  Fails with a helpful diff if anything is missing or stale.
"""

import ast
from pathlib import Path

import pytest

from .known_types import KNOWN_CONTROL_TYPES

PLATFORM_DIR = Path(__file__).resolve().parents[3] / "custom_components" / "loxone"

SKIP_FILES = {
    "__init__",
    "const",
    "helpers",
    "coordinator",
    "miniserver",
    "scene",
}


_DISCOVERY_FUNCS = {"get_all", "get_all_including_subcontrols"}


def _extract_get_all_types() -> dict[str, set[str]]:
    """Scan platform .py files for control-discovery helper calls.

    Recognises ``get_all(loxconfig, ...)`` and the recursive variant
    ``get_all_including_subcontrols(loxconfig, ...)``. Returns a dict
    mapping each control type string to the platform(s) that handle
    it (derived from the filename).
    """
    type_to_platforms: dict[str, set[str]] = {}

    for py_file in sorted(PLATFORM_DIR.glob("*.py")):
        platform = py_file.stem
        if platform.startswith("_") or platform in SKIP_FILES:
            continue

        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Name) and func.id in _DISCOVERY_FUNCS):
                continue
            if len(node.args) < 2:
                continue

            arg = node.args[1]
            type_strings: list[str] = []

            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                type_strings.append(arg.value)
            elif isinstance(arg, ast.List):
                type_strings.extend(
                    elt.value for elt in arg.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                )

            for ts in type_strings:
                type_to_platforms.setdefault(ts, set()).add(platform)

    return type_to_platforms


class TestKnownTypesSync:
    """Ensure KNOWN_CONTROL_TYPES matches what the platform code actually uses."""

    def test_no_missing_types(self):
        """Every type used in a get_all() call should be in KNOWN_CONTROL_TYPES."""
        source_types = _extract_get_all_types()
        missing = {t: platforms for t, platforms in source_types.items() if t not in KNOWN_CONTROL_TYPES}
        if missing:
            lines = [f"  {t} (used in {', '.join(sorted(ps))})" for t, ps in sorted(missing.items())]
            pytest.fail(
                "Control types found in platform code but missing from "
                "KNOWN_CONTROL_TYPES in known_types.py:\n" + "\n".join(lines)
            )

    def test_no_stale_types(self):
        """Every type in KNOWN_CONTROL_TYPES should still be used by some platform."""
        source_types = _extract_get_all_types()
        stale = {t: platform for t, platform in KNOWN_CONTROL_TYPES.items() if t not in source_types}
        if stale:
            lines = [f"  {t} (was mapped to {p})" for t, p in sorted(stale.items())]
            pytest.fail(
                "Control types in KNOWN_CONTROL_TYPES that are no longer used "
                "in any platform's get_all() calls:\n" + "\n".join(lines)
            )

    def test_platform_mapping_correct(self):
        """The platform name in KNOWN_CONTROL_TYPES should match where it's used."""
        source_types = _extract_get_all_types()
        mismatches = []
        for ctype, platforms in source_types.items():
            if ctype not in KNOWN_CONTROL_TYPES:
                continue
            declared_platform = KNOWN_CONTROL_TYPES[ctype]
            if declared_platform not in platforms:
                mismatches.append(
                    f"  {ctype}: declared as '{declared_platform}' but used in {', '.join(sorted(platforms))}"
                )
        if mismatches:
            pytest.fail("Platform mismatches in KNOWN_CONTROL_TYPES:\n" + "\n".join(mismatches))
