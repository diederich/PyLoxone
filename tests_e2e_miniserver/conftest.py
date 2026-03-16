"""Fixtures for end-to-end Miniserver tests.

These tests talk directly to the Loxone Miniserver API — no Home Assistant
needed.  Run them from the repo root:

    pytest tests_e2e_miniserver/ -s -v

The HA test plugins (pytest-homeassistant-custom-component, pytest-socket) are
installed in the venv but unwanted here.  This conftest marks all e2e tests
with ``enable_socket`` and overrides cleanup checks so the tests work without
special CLI flags.

All fixtures are session-scoped — the connection is established once and
reused across all tests in a single run.

Configuration via environment variables (or .env in repo root):
  LOXONE_HOST      (required)
  LOXONE_PORT      (default: 8080)
  LOXONE_USERNAME  (required)
  LOXONE_PASSWORD  (required)
"""

import os
import sys
from pathlib import Path
from collections.abc import Generator
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT / "tests" / "components" / "loxone"))


def _load_env():
    """Load .env file if present, without overwriting existing vars."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env()


def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    """Mark all e2e tests with enable_socket so pytest-socket allows real sockets."""
    for item in items:
        item.add_marker(pytest.mark.enable_socket)


@pytest.fixture(autouse=True)
def verify_cleanup() -> Generator[None]:
    """Override the HA plugin's verify_cleanup so it doesn't fail on
    lingering timers from our long-lived WebSocket connection."""
    yield


# ---------------------------------------------------------------------------
# Miniserver connection fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def miniserver_config():
    """Load and validate Miniserver connection config.

    Skips the entire session if required env vars are missing.
    """
    host = os.environ.get("LOXONE_HOST")
    username = os.environ.get("LOXONE_USERNAME")
    password = os.environ.get("LOXONE_PASSWORD")
    port = int(os.environ.get("LOXONE_PORT", "8080"))

    missing = [
        name
        for name, val in [
            ("LOXONE_HOST", host),
            ("LOXONE_USERNAME", username),
            ("LOXONE_PASSWORD", password),
        ]
        if not val
    ]
    if missing:
        pytest.skip(
            f"Miniserver credentials not configured: {', '.join(missing)}. "
            f"Set them in env or .env at repo root."
        )

    return {"host": host, "port": port, "username": username, "password": password}


@pytest.fixture(scope="session")
async def loxone_connection(miniserver_config):
    """Create a LoxoneConnection, call open(), and yield it.

    Closes the connection after the test session.
    """
    from custom_components.loxone.pyloxone_api.connection import LoxoneConnection

    api = LoxoneConnection(
        host=miniserver_config["host"],
        username=miniserver_config["username"],
        password=miniserver_config["password"],
        port=miniserver_config["port"],
    )
    await api.open()
    yield api
    await api.close()


@pytest.fixture(scope="session")
def structure_file(loxone_connection):
    """Return the structure file dict from an open connection."""
    return loxone_connection.structure_file


@pytest.fixture(scope="session")
def snapshot_dir():
    """Ensure the snapshots directory exists and return its path."""
    d = Path(__file__).parent / "snapshots"
    d.mkdir(parents=True, exist_ok=True)
    return d
