"""Event entity for Seismic World Earthquakes — fires on new earthquake detections."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EarthquakeEvent, SeismicWorldEarthquakesCoordinator

_LOGGER = logging.getLogger(__name__)

EVENT_TYPE_EARTHQUAKE_DETECTED = "earthquake_detected"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the event entity."""
    coordinator: SeismicWorldEarthquakesCoordinator = entry.runtime_data
    async_add_entities([NewEarthquakeEventEntity(coordinator)])


class NewEarthquakeEventEntity(CoordinatorEntity[SeismicWorldEarthquakesCoordinator], EventEntity):
    """
    HA Event entity that fires each time a new earthquake is detected in the feed.

    This is ideal for automations: trigger when a new earthquake appears,
    with full earthquake details available as event attributes.

    Note: on integration first load all existing earthquakes are skipped —
    only earthquakes that appear in subsequent data refreshes trigger the event.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "new_earthquake"
    _attr_icon = "mdi:earth-alert"
    _attr_event_types = [EVENT_TYPE_EARTHQUAKE_DETECTED]

    def __init__(self, coordinator: SeismicWorldEarthquakesCoordinator) -> None:
        """Initialise."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_new_earthquake"
        self._first_update_done = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name=self.coordinator.config_entry.title,
            manufacturer="U.S. Geological Survey (USGS)",
            model="Earthquake Hazards Program API",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://earthquake.usgs.gov/earthquakes/feed/",
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fire an event for each new earthquake detected since the last update."""
        if self.coordinator.data is None:
            return

        # Skip on first load to avoid flooding with existing events
        if not self._first_update_done:
            self._first_update_done = True
            self.async_write_ha_state()
            return

        new_quakes = self.coordinator.data.new_earthquakes
        if not new_quakes:
            self.async_write_ha_state()
            return

        # Sort new earthquakes by magnitude descending — fire strongest first
        for eq in sorted(new_quakes, key=lambda e: e.magnitude, reverse=True):
            _LOGGER.debug(
                "New earthquake detected: M%.1f — %s (%s)",
                eq.magnitude,
                eq.place,
                eq.earthquake_id,
            )
            self._trigger_event(
                EVENT_TYPE_EARTHQUAKE_DETECTED,
                self._earthquake_to_attributes(eq),
            )

        self.async_write_ha_state()

    @staticmethod
    def _earthquake_to_attributes(eq: EarthquakeEvent) -> dict[str, Any]:
        """Serialize earthquake data as event attributes for automations."""
        return {
            "earthquake_id": eq.earthquake_id,
            "magnitude": eq.magnitude,
            "magnitude_type": eq.mag_type,
            "place": eq.place,
            "time": eq.time.isoformat(),
            "latitude": eq.latitude,
            "longitude": eq.longitude,
            "depth_km": eq.depth,
            "status": eq.status,
            "tsunami_warning": eq.tsunami,
            "significance": eq.sig,
            "alert_level": eq.alert,
            "max_intensity_mmi": eq.mmi,
            "felt_reports": eq.felt,
            "community_intensity_cdi": eq.cdi,
            "network": eq.net,
            "distance": eq.distance,
            "url": eq.url,
            "title": eq.title,
        }
