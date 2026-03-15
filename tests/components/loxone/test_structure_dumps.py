"""Unit tests that parse real Miniserver structure dumps.

Each dump file in fixtures/dumps/ is a real LoxAPP3.json snapshot.
Tests are parametrized over all dumps, ensuring backwards compatibility
and reporting unhandled control types with full JSON examples.

Create new dumps with:  scripts/dump_miniserver
"""

import json
from collections import Counter
from pathlib import Path

import pytest

from .known_types import KNOWN_CONTROL_TYPES, KNOWN_SUBCONTROL_TYPES

DUMP_DIR = Path(__file__).parent / "fixtures" / "dumps"


def _dump_files() -> list[Path]:
    """Collect all dump JSON files (excluding _expected.json companions)."""
    if not DUMP_DIR.is_dir():
        return []
    return sorted(
        p
        for p in DUMP_DIR.glob("*.json")
        if not p.name.endswith("_expected.json") and p.name != ".gitkeep"
    )


def _dump_ids() -> list[str]:
    """Generate readable test IDs from dump filenames."""
    return [p.stem for p in _dump_files()]


def _load_dump(path: Path) -> dict:
    return json.loads(path.read_text())


def _expected_path(dump_path: Path) -> Path:
    return dump_path.with_name(dump_path.stem + "_expected.json")


def _compute_expectations(structure: dict) -> dict:
    """Compute entity counts per platform from a structure file."""
    controls = structure.get("controls", {})
    type_counter: Counter = Counter()
    for control in controls.values():
        type_counter[control.get("type", "UNKNOWN")] += 1

    by_platform: Counter = Counter()
    unhandled_types: list[str] = []
    unhandled_count = 0

    for ctype, count in sorted(type_counter.items()):
        platform = KNOWN_CONTROL_TYPES.get(ctype)
        if platform:
            by_platform[platform] += count
        else:
            unhandled_types.append(ctype)
            unhandled_count += count

    return {
        "total_controls": len(controls),
        "by_platform": dict(sorted(by_platform.items())),
        "unhandled_types": sorted(unhandled_types),
        "unhandled_count": unhandled_count,
    }


dump_files = _dump_files()
skip_no_dumps = pytest.mark.skipif(
    not dump_files, reason="No dump files in fixtures/dumps/"
)


@skip_no_dumps
@pytest.mark.parametrize("dump_path", dump_files, ids=_dump_ids())
class TestStructureDumps:
    """Tests run once per dump file."""

    def test_dump_parses_without_error(self, dump_path: Path):
        structure = _load_dump(dump_path)
        for key in ("msInfo", "controls", "rooms", "cats"):
            assert key in structure, f"Missing top-level key '{key}' in {dump_path.name}"

    def test_dump_entity_counts_match_expected(self, dump_path: Path):
        structure = _load_dump(dump_path)
        actual = _compute_expectations(structure)
        exp_path = _expected_path(dump_path)

        if not exp_path.exists():
            exp_path.write_text(json.dumps(actual, indent=2) + "\n")
            pytest.fail(
                f"No expectations file found. Auto-generated {exp_path.name} — "
                f"review it and re-run."
            )

        expected = json.loads(exp_path.read_text())

        assert actual["total_controls"] == expected["total_controls"], (
            f"Total controls changed: expected {expected['total_controls']}, "
            f"got {actual['total_controls']}"
        )

        for platform, count in expected["by_platform"].items():
            actual_count = actual["by_platform"].get(platform, 0)
            assert actual_count == count, (
                f"Platform '{platform}' count changed: expected {count}, "
                f"got {actual_count}"
            )

    def test_dump_control_type_coverage(self, dump_path: Path, capsys):
        structure = _load_dump(dump_path)
        controls = structure.get("controls", {})

        type_counter: Counter = Counter()
        examples: dict[str, dict] = {}
        for control in controls.values():
            ctype = control.get("type", "UNKNOWN")
            type_counter[ctype] += 1
            if ctype not in examples:
                examples[ctype] = control

        ms_info = structure.get("msInfo", {})
        print(f"\n{'=' * 60}")
        print(f"Dump: {dump_path.name}")
        print(f"Miniserver: {ms_info.get('msName', '?')} (v{ms_info.get('swVersion', '?')})")
        print(f"{'=' * 60}")

        print(f"\n=== Control Type Summary ({len(controls)} total) ===")
        max_name = max((len(t) for t in type_counter), default=0)
        unhandled = []
        for ctype, count in type_counter.most_common():
            platform = KNOWN_CONTROL_TYPES.get(ctype)
            label = f"({platform})" if platform else "*** UNHANDLED ***"
            dots = "." * (max_name + 4 - len(ctype))
            print(f"  {ctype} {dots} {count:>3}  {label}")
            if not platform:
                unhandled.append(ctype)

        if unhandled:
            total_unhandled = sum(type_counter[t] for t in unhandled)
            print(
                f"\n=== Unhandled Control Types: "
                f"{len(unhandled)} types, {total_unhandled} controls total ==="
            )
            for ctype in unhandled:
                print(f"\n--- {ctype} ({type_counter[ctype]} instances) — example: ---")
                print(json.dumps(examples[ctype], indent=2, ensure_ascii=False))
        else:
            print("\nAll control types are handled.")

    def test_dump_subcontrol_coverage(self, dump_path: Path, capsys):
        structure = _load_dump(dump_path)
        controls = structure.get("controls", {})

        sub_counter: Counter = Counter()
        sub_examples: dict[str, dict] = {}
        for control in controls.values():
            for sub in control.get("subControls", {}).values():
                stype = sub.get("type", "UNKNOWN")
                sub_counter[stype] += 1
                if stype not in sub_examples:
                    sub_examples[stype] = sub

        if not sub_counter:
            print(f"\n{dump_path.name}: No subControls found.")
            return

        print(f"\n=== SubControl Type Summary ({sum(sub_counter.values())} total) ===")
        max_name = max((len(t) for t in sub_counter), default=0)
        unhandled = []
        for stype, count in sub_counter.most_common():
            platform = KNOWN_SUBCONTROL_TYPES.get(stype)
            label = f"({platform})" if platform else "*** UNHANDLED ***"
            dots = "." * (max_name + 4 - len(stype))
            print(f"  {stype} {dots} {count:>3}  {label}")
            if not platform:
                unhandled.append(stype)

        if unhandled:
            total_unhandled = sum(sub_counter[t] for t in unhandled)
            print(
                f"\n=== Unhandled SubControl Types: "
                f"{len(unhandled)} types, {total_unhandled} controls total ==="
            )
            for stype in unhandled:
                print(f"\n--- {stype} ({sub_counter[stype]} instances) — example: ---")
                print(json.dumps(sub_examples[stype], indent=2, ensure_ascii=False))

    def test_dump_backwards_compat(self, dump_path: Path):
        """Every control type must be either known or explicitly acknowledged."""
        structure = _load_dump(dump_path)
        controls = structure.get("controls", {})
        exp_path = _expected_path(dump_path)

        acknowledged_unhandled: set[str] = set()
        if exp_path.exists():
            expected = json.loads(exp_path.read_text())
            acknowledged_unhandled = set(expected.get("unhandled_types", []))

        surprise_types: list[str] = []
        for control in controls.values():
            ctype = control.get("type", "UNKNOWN")
            if ctype not in KNOWN_CONTROL_TYPES and ctype not in acknowledged_unhandled:
                surprise_types.append(ctype)

        if surprise_types:
            unique = sorted(set(surprise_types))
            pytest.fail(
                f"New unrecognized control types found in {dump_path.name}: "
                f"{unique}. Either implement them or add to "
                f"'unhandled_types' in {exp_path.name}."
            )
