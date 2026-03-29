"""Tests for the loxone.sync_areas service."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN

pytestmark = pytest.mark.usefixtures("init_integration")


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_switches.json"


def _get_device_for_entity(hass, entity_id):
    """Return the DeviceEntry for the device that owns *entity_id*."""
    er_registry = er.async_get(hass)
    dr_registry = dr.async_get(hass)
    entry = er_registry.async_get(entity_id)
    assert entry is not None, f"entity {entity_id} not found"
    assert entry.device_id is not None, f"entity {entity_id} has no device"
    device = dr_registry.async_get(entry.device_id)
    assert device is not None
    return device


# -- Device-level area sync ---------------------------------------------------


async def test_sync_areas_assigns_area_to_device(
    hass: HomeAssistant,
) -> None:
    """sync_areas should assign the area to the device, not the entity."""
    ar_registry = ar.async_get(hass)
    er_registry = er.async_get(hass)

    area = ar_registry.async_get_area_by_name("Living Room")
    assert area is not None

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": True}, blocking=True
    )

    for entity_id in ("switch.wall_switch", "switch.bathroom_fan"):
        device = _get_device_for_entity(hass, entity_id)
        assert device.area_id == area.id, (
            f"device for {entity_id} should be in Living Room"
        )
        entry = er_registry.async_get(entity_id)
        assert entry.area_id is None, (
            f"{entity_id} should have no entity-level area override"
        )


# -- Entity override cleanup --------------------------------------------------


async def test_sync_areas_clears_entity_level_area_overrides(
    hass: HomeAssistant,
) -> None:
    """sync_areas should clear stale entity-level area_id overrides
    (left by the old upstream implementation) so entities inherit from device."""
    ar_registry = ar.async_get(hass)
    er_registry = er.async_get(hass)

    area = ar_registry.async_get_area_by_name("Living Room")
    assert area is not None

    er_registry.async_update_entity("switch.wall_switch", area_id=area.id)
    entry = er_registry.async_get("switch.wall_switch")
    assert entry.area_id == area.id

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": True}, blocking=True
    )

    entry = er_registry.async_get("switch.wall_switch")
    assert entry.area_id is None, "entity-level override should be cleared"
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id == area.id, "device should have the area instead"


# -- create_areas behaviour ---------------------------------------------------


async def test_sync_areas_create_areas_true_recreates_deleted_area(
    hass: HomeAssistant,
) -> None:
    """With create_areas=true, sync should recreate a deleted area and assign to device."""
    ar_registry = ar.async_get(hass)

    area = ar_registry.async_get_area_by_name("Living Room")
    ar_registry.async_delete(area.id)
    assert ar_registry.async_get_area_by_name("Living Room") is None

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": True}, blocking=True
    )

    area = ar_registry.async_get_area_by_name("Living Room")
    assert area is not None, "Area should be recreated with create_areas=true"
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id == area.id


async def test_sync_areas_create_areas_false_does_not_create(
    hass: HomeAssistant,
) -> None:
    """With create_areas=false, sync should not create missing areas."""
    ar_registry = ar.async_get(hass)

    area = ar_registry.async_get_area_by_name("Living Room")
    ar_registry.async_delete(area.id)

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": False}, blocking=True
    )

    assert ar_registry.async_get_area_by_name("Living Room") is None
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id is None


async def test_sync_areas_default_does_not_create_areas(
    hass: HomeAssistant,
) -> None:
    """Calling sync_areas without create_areas should not create new areas."""
    ar_registry = ar.async_get(hass)

    area = ar_registry.async_get_area_by_name("Living Room")
    ar_registry.async_delete(area.id)

    await hass.services.async_call(DOMAIN, "sync_areas", {}, blocking=True)

    assert ar_registry.async_get_area_by_name("Living Room") is None
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id is None


# -- Re-sync after area deletion -----------------------------------------------


async def test_sync_areas_reassigns_device_after_area_deleted(
    hass: HomeAssistant,
) -> None:
    """After deleting an area, sync_areas should recreate and re-assign device."""
    ar_registry = ar.async_get(hass)

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": True}, blocking=True
    )
    area = ar_registry.async_get_area_by_name("Living Room")
    old_area_id = area.id
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id == old_area_id

    ar_registry.async_delete(old_area_id)
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id is None

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": True}, blocking=True
    )

    new_area = ar_registry.async_get_area_by_name("Living Room")
    assert new_area is not None
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id == new_area.id


# -- Re-sync corrects wrong area assignment ------------------------------------


async def test_sync_areas_moves_device_from_wrong_area(
    hass: HomeAssistant,
) -> None:
    """If a device is in the wrong area, sync_areas should move it."""
    ar_registry = ar.async_get(hass)
    dr_registry = dr.async_get(hass)

    wrong_area = ar_registry.async_get_or_create("Kitchen")
    right_area = ar_registry.async_get_area_by_name("Living Room")
    assert right_area is not None

    device = _get_device_for_entity(hass, "switch.wall_switch")
    dr_registry.async_update_device(device.id, area_id=wrong_area.id)
    device = dr_registry.async_get(device.id)
    assert device.area_id == wrong_area.id

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": True}, blocking=True
    )

    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id == right_area.id, (
        "Device should be moved from Kitchen to Living Room"
    )


# -- Idempotency --------------------------------------------------------------


async def test_sync_areas_is_idempotent(
    hass: HomeAssistant,
) -> None:
    """Running sync_areas twice should produce the same result."""
    ar_registry = ar.async_get(hass)
    er_registry = er.async_get(hass)

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": True}, blocking=True
    )
    area = ar_registry.async_get_area_by_name("Living Room")
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id == area.id

    await hass.services.async_call(
        DOMAIN, "sync_areas", {"create_areas": True}, blocking=True
    )
    device = _get_device_for_entity(hass, "switch.wall_switch")
    assert device.area_id == area.id
    entry = er_registry.async_get("switch.wall_switch")
    assert entry.area_id is None
