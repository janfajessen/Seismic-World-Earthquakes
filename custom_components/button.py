"""Button entities for Seismic World Earthquakes."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SeismicWorldEarthquakesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    coordinator: SeismicWorldEarthquakesCoordinator = entry.runtime_data
    async_add_entities([ForceRefreshButton(coordinator)])


class ForceRefreshButton(ButtonEntity):
    """Button that forces an immediate data refresh from USGS."""

    _attr_has_entity_name = True
    _attr_translation_key = "force_refresh"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: SeismicWorldEarthquakesCoordinator) -> None:
        """Initialise."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_force_refresh"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.config_entry.entry_id)},
            name=self._coordinator.config_entry.title,
            manufacturer="U.S. Geological Survey (USGS)",
            model="Earthquake Hazards Program API",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://earthquake.usgs.gov/earthquakes/feed/",
        )

    async def async_press(self) -> None:
        """Trigger an immediate coordinator refresh."""
        _LOGGER.debug(
            "Force refresh requested for Seismic World Earthquakes entry '%s'",
            self._coordinator.config_entry.title,
        )
        await self._coordinator.async_request_refresh()
