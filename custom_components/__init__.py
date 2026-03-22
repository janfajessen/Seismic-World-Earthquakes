"""Seismic World Earthquakes integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import SeismicWorldEarthquakesCoordinator

_LOGGER = logging.getLogger(__name__)

type SeismicWorldEarthquakesConfigEntry = ConfigEntry[SeismicWorldEarthquakesCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SeismicWorldEarthquakesConfigEntry,
) -> bool:
    """Set up Seismic World Earthquakes from a config entry."""
    coordinator = SeismicWorldEarthquakesCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_options_update_listener))

    _LOGGER.debug(
        "Seismic World Earthquakes entry '%s' set up successfully",
        entry.title,
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SeismicWorldEarthquakesConfigEntry,
) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    _LOGGER.debug("Seismic World Earthquakes entry '%s' unloaded: %s", entry.title, unloaded)
    return unloaded


async def _async_options_update_listener(
    hass: HomeAssistant,
    entry: SeismicWorldEarthquakesConfigEntry,
) -> None:
    """Reload entry when options change (options flow reconfiguración)."""
    _LOGGER.debug(
        "Seismic World Earthquakes entry '%s' options updated, reloading",
        entry.title,
    )
    await hass.config_entries.async_reload(entry)
