from ipaddress import ip_address

import pytest

from custom_components.loxone.pyloxone_api.discover import discover


async def test_discover_broadcast():
    """Broadcast discovery — may fail depending on network topology."""
    result = await discover()
    if result is None:
        pytest.skip("No Miniserver responded to UDP broadcast (network/topology issue)")
    ip, port, response = result
    assert ip_address(ip)
    assert isinstance(port, int)
    assert response.startswith("LoxLIVE")


async def test_discover_directed(miniserver_config):
    """Directed (unicast) discovery using the known host from env."""
    host = miniserver_config["host"]
    result = await discover(host=host)
    assert result is not None, f"Miniserver at {host} did not respond to directed discovery"
    ip, port, response = result
    assert ip_address(ip)
    assert isinstance(port, int)
    assert response.startswith("LoxLIVE")


async def test_discover_timeout_returns_none():
    """Zero timeout should return None immediately."""
    assert await discover(discovery_timeout=0) is None
