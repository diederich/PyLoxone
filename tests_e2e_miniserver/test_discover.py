from ipaddress import ip_address

import pytest

from custom_components.loxone.pyloxone_api.discover import discover


async def test_discover():
    result = await discover()
    if result is None:
        pytest.skip("No Miniserver responded to UDP broadcast (network/topology issue)")
    ip, port, response = result
    assert ip_address(ip)
    assert isinstance(port, int)
    assert response.startswith("LoxLIVE")
