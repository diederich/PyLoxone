"""End-to-end tests against a real Loxone Miniserver.

Run with:
    pytest tests_e2e_miniserver/ -s -v

Requires LOXONE_HOST, LOXONE_USERNAME, LOXONE_PASSWORD env vars (or .env).
"""

import asyncio
from collections import Counter
import contextlib
from datetime import UTC, datetime
import json

import pytest

from tests.components.loxone.known_types import KNOWN_CONTROL_TYPES, KNOWN_SUBCONTROL_TYPES


class TestConnection:
    """Verify we can connect and fetch data from the Miniserver."""

    async def test_connection_succeeds(self, loxone_connection):
        assert loxone_connection.structure_file, "open() should populate structure_file"

    def test_structure_file_valid(self, structure_file):
        for key in ("msInfo", "controls", "rooms", "cats"):
            assert key in structure_file, f"Missing top-level key '{key}'"

    def test_miniserver_info(self, structure_file, capsys):
        ms = structure_file["msInfo"]
        print(f"\n{'=' * 50}")
        print(f"Miniserver: {ms.get('msName', '?')}")
        print(f"Serial:     {ms.get('serialNr', '?')}")
        print(f"Software:   {ms.get('swVersion', '?')}")
        print(f"Type:       {ms.get('miniserverType', '?')}")
        print(f"Local URL:  {ms.get('localUrl', '?')}")
        print(f"Rooms:      {len(structure_file.get('rooms', {}))}")
        print(f"Categories: {len(structure_file.get('cats', {}))}")
        print(f"Controls:   {len(structure_file.get('controls', {}))}")
        print(f"{'=' * 50}")


class TestControlTypeCoverage:
    """Analyze which control types exist and which are unhandled."""

    def test_control_type_coverage(self, structure_file, capsys):
        controls = structure_file.get("controls", {})
        type_counter: Counter = Counter()
        examples: dict[str, dict] = {}
        for control in controls.values():
            ctype = control.get("type", "UNKNOWN")
            type_counter[ctype] += 1
            if ctype not in examples:
                examples[ctype] = control

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
            print(f"\n=== Unhandled Control Types: {len(unhandled)} types, {total_unhandled} controls total ===")
            for ctype in unhandled:
                print(f"\n--- {ctype} ({type_counter[ctype]} instances) — example: ---")
                print(json.dumps(examples[ctype], indent=2, ensure_ascii=False))
        else:
            print("\nAll control types are handled.")

    def test_subcontrol_type_coverage(self, structure_file, capsys):
        controls = structure_file.get("controls", {})
        sub_counter: Counter = Counter()
        sub_examples: dict[str, dict] = {}
        for control in controls.values():
            for sub in control.get("subControls", {}).values():
                stype = sub.get("type", "UNKNOWN")
                sub_counter[stype] += 1
                if stype not in sub_examples:
                    sub_examples[stype] = sub

        if not sub_counter:
            print("\nNo subControls found.")
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
            print(f"\n=== Unhandled SubControl Types: {len(unhandled)} types, {total_unhandled} total ===")
            for stype in unhandled:
                print(f"\n--- {stype} ({sub_counter[stype]} instances) — example: ---")
                print(json.dumps(sub_examples[stype], indent=2, ensure_ascii=False))


class TestStructureIntegrity:
    """Validate structure file references and completeness."""

    def test_room_and_category_coverage(self, structure_file, capsys):
        rooms = structure_file.get("rooms", {})
        cats = structure_file.get("cats", {})
        controls = structure_file.get("controls", {})

        print(f"\nRooms: {len(rooms)}, Categories: {len(cats)}")

        bad_rooms = []
        bad_cats = []
        for uuid, control in controls.items():
            room_ref = control.get("room", "")
            cat_ref = control.get("cat", "")
            if room_ref and room_ref not in rooms:
                bad_rooms.append((control.get("name", uuid), room_ref))
            if cat_ref and cat_ref not in cats:
                bad_cats.append((control.get("name", uuid), cat_ref))

        if bad_rooms:
            print(f"\nControls referencing invalid rooms ({len(bad_rooms)}):")
            for name, ref in bad_rooms[:10]:
                print(f"  {name} -> {ref}")
        if bad_cats:
            print(f"\nControls referencing invalid categories ({len(bad_cats)}):")
            for name, ref in bad_cats[:10]:
                print(f"  {name} -> {ref}")

        assert not bad_rooms, f"{len(bad_rooms)} controls reference invalid rooms"
        assert not bad_cats, f"{len(bad_cats)} controls reference invalid categories"

    def test_no_controls_without_states(self, structure_file, capsys):
        controls = structure_file.get("controls", {})
        stateless = []
        for uuid, control in controls.items():
            if "states" not in control or not control["states"]:
                stateless.append((control.get("name", uuid), control.get("type", "?")))

        if stateless:
            print(f"\nControls without states ({len(stateless)}):")
            for name, ctype in stateless:
                print(f"  {name} ({ctype})")
            print("(Some control types like SystemScheme are stateless by design.)")


class TestWebSocket:
    """Test the real-time WebSocket data path."""

    async def test_websocket_receives_events(self, loxone_connection):
        """Open WebSocket, wait for at least one state update, then stop."""
        received = []

        def callback(message):
            received.append(message)

        listen_task = asyncio.create_task(loxone_connection.start_listening(callback))

        try:
            for _ in range(30):
                await asyncio.sleep(0.5)
                if received:
                    break

            assert received, "No state updates received within 15 seconds. Is the Miniserver actively sending data?"
            print(f"\nReceived {len(received)} message(s) from WebSocket.")
        finally:
            listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await listen_task


class TestCommandRoundtrip:
    """Send a read-only command and verify a response."""

    async def test_command_roundtrip(self, loxone_connection, structure_file):
        """Find a sensor UUID and request its status (read-only)."""
        controls = structure_file.get("controls", {})

        sensor_uuid = None
        for uuid, control in controls.items():
            if control.get("type") == "InfoOnlyAnalog":
                sensor_uuid = control.get("uuidAction", uuid)
                sensor_name = control.get("name", "?")
                break

        if not sensor_uuid:
            pytest.skip("No InfoOnlyAnalog sensor found to test against")

        response = await loxone_connection.send_websocket_command(sensor_uuid, "status")
        print(f"\nCommand roundtrip to '{sensor_name}' ({sensor_uuid}): response={response}")


class TestSnapshot:
    """Save a structure file snapshot for later diffing."""

    def test_save_structure_snapshot(self, structure_file, snapshot_dir, capsys):
        ms = structure_file.get("msInfo", {})
        serial = ms.get("serialNr", "UNKNOWN")
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{serial}_{timestamp}.json"

        path = snapshot_dir / filename
        path.write_text(json.dumps(structure_file, indent=2, ensure_ascii=False) + "\n")
        print(f"\nSnapshot saved: {path}")
