"""Binary sensor entities for Seismic World Earthquakes."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import SeismicWorldEarthquakesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator: SeismicWorldEarthquakesCoordinator = entry.runtime_data
    async_add_entities([
        EarthquakeAlertBinarySensor(coordinator),
        TsunamiWarningBinarySensor(coordinator),
    ])


class _SeismicBinarySensorBase(CoordinatorEntity[SeismicWorldEarthquakesCoordinator], BinarySensorEntity):
    """Base class for seismic binary sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SeismicWorldEarthquakesCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"

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


class EarthquakeAlertBinarySensor(_SeismicBinarySensorBase):
    """
    Binary sensor: ON if there is an earthquake ≥ alert_min_magnitude
    within the configured alert_time_window hours.
    Configurable in the options flow.
    """

    _attr_translation_key = "earthquake_alert"
    _attr_icon = "mdi:bell-alert"
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, coordinator: SeismicWorldEarthquakesCoordinator) -> None:
        super().__init__(coordinator, "earthquake_alert")

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        now = dt_util.now()
        window_start = now - timedelta(hours=self.coordinator.alert_time_window)
        threshold = self.coordinator.alert_min_magnitude
        return any(
            eq.magnitude >= threshold and eq.time >= window_start
            for eq in self.coordinator.data.earthquakes
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "min_magnitude_threshold": self.coordinator.alert_min_magnitude,
            "time_window_hours": self.coordinator.alert_time_window,
        }


class TsunamiWarningBinarySensor(_SeismicBinarySensorBase):
    """Binary sensor: ON if there is at least one event with an active tsunami flag."""

    _attr_translation_key = "tsunami_warning"
    _attr_icon = "mdi:waves-arrow-up"
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, coordinator: SeismicWorldEarthquakesCoordinator) -> None:
        super().__init__(coordinator, "tsunami_warning")

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.tsunami_count > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}
        tsunami_events = [
            {"id": eq.earthquake_id, "magnitude": eq.magnitude, "place": eq.place, "time": eq.time.isoformat()}
            for eq in self.coordinator.data.earthquakes
            if eq.tsunami
        ]
        return {"tsunami_events": tsunami_events, "count": len(tsunami_events)}
