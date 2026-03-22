"""Sensor entities for Seismic World Earthquakes."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, UNITS_KM
from .coordinator import SeismicData, SeismicWorldEarthquakesCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SeismicSensorEntityDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with SeismicData accessors."""

    value_fn: Callable[[SeismicData], Any]
    attributes_fn: Callable[[SeismicData], dict[str, Any]] | None = None


def _strongest_attrs(data: SeismicData) -> dict[str, Any]:
    if not data.strongest:
        return {}
    eq = data.strongest
    return {
        "place": eq.place,
        "time": eq.time.isoformat(),
        "depth_km": eq.depth,
        "magnitude_type": eq.mag_type,
        "alert_level": eq.alert,
        "tsunami_warning": eq.tsunami,
        "url": eq.url,
        "earthquake_id": eq.earthquake_id,
    }


def _latest_attrs(data: SeismicData) -> dict[str, Any]:
    if not data.latest:
        return {}
    eq = data.latest
    return {
        "magnitude": eq.magnitude,
        "place": eq.place,
        "depth_km": eq.depth,
        "alert_level": eq.alert,
        "tsunami_warning": eq.tsunami,
        "url": eq.url,
        "earthquake_id": eq.earthquake_id,
    }


def _nearest_distance_attrs(data: SeismicData) -> dict[str, Any]:
    if not data.nearest:
        return {}
    eq = data.nearest
    return {
        "place": eq.place,
        "magnitude": eq.magnitude,
        "time": eq.time.isoformat(),
        "depth_km": eq.depth,
        "latitude": eq.latitude,
        "longitude": eq.longitude,
        "alert_level": eq.alert,
        "url": eq.url,
    }


SENSOR_DESCRIPTIONS: tuple[SeismicSensorEntityDescription, ...] = (
    # ── Main sensors ──────────────────────────────────────
    SeismicSensorEntityDescription(
        key="total_earthquakes",
        translation_key="total_earthquakes",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.total,
    ),
    SeismicSensorEntityDescription(
        key="strongest_magnitude",
        translation_key="strongest_magnitude",
        icon="mdi:waveform",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.strongest.magnitude if d.strongest else None,
        attributes_fn=_strongest_attrs,
    ),
    SeismicSensorEntityDescription(
        key="strongest_location",
        translation_key="strongest_location",
        icon="mdi:map-marker-star",
        value_fn=lambda d: d.strongest.place if d.strongest else None,
        attributes_fn=_strongest_attrs,
    ),
    SeismicSensorEntityDescription(
        key="average_magnitude",
        translation_key="average_magnitude",
        icon="mdi:chart-bell-curve",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: d.average_magnitude if d.total else None,
    ),
    SeismicSensorEntityDescription(
        key="latest_earthquake",
        translation_key="latest_earthquake",
        icon="mdi:map-clock",
        value_fn=lambda d: d.latest.title if d.latest else None,
        attributes_fn=_latest_attrs,
    ),
    SeismicSensorEntityDescription(
        key="latest_earthquake_time",
        translation_key="latest_earthquake_time",
        icon="mdi:clock-alert-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.latest.time if d.latest else None,
    ),
    SeismicSensorEntityDescription(
        key="earthquakes_last_hour",
        translation_key="earthquakes_last_hour",
        icon="mdi:history",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.last_hour_count,
    ),
    SeismicSensorEntityDescription(
        key="significant_earthquakes",
        translation_key="significant_earthquakes",
        icon="mdi:alert-decagram-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.significant_count,
    ),
    SeismicSensorEntityDescription(
        key="tsunami_warnings",
        translation_key="tsunami_warnings",
        icon="mdi:waves",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.tsunami_count,
    ),
    SeismicSensorEntityDescription(
        key="highest_alert_level",
        translation_key="highest_alert_level",
        icon="mdi:shield-alert",
        value_fn=lambda d: d.highest_alert or "none",
    ),
    SeismicSensorEntityDescription(
        key="red_alert_count",
        translation_key="red_alert_count",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.red_alert_count,
    ),
    SeismicSensorEntityDescription(
        key="nearest_distance",
        translation_key="nearest_distance",
        icon="mdi:map-marker-distance",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.nearest_distance,
        attributes_fn=_nearest_distance_attrs,
    ),
    SeismicSensorEntityDescription(
        key="nearest_magnitude",
        translation_key="nearest_magnitude",
        icon="mdi:map-marker-radius-outline",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.nearest_magnitude,
        attributes_fn=_nearest_distance_attrs,
    ),
    # ── Diagnostic sensors ────────────────────────────────
    SeismicSensorEntityDescription(
        key="last_update",
        translation_key="last_update",
        icon="mdi:clock-check-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.last_update,
    ),
    SeismicSensorEntityDescription(
        key="api_status",
        translation_key="api_status",
        icon="mdi:api",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.api_status,
    ),
    SeismicSensorEntityDescription(
        key="events_fetched",
        translation_key="events_fetched",
        icon="mdi:download-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.events_fetched,
    ),
    SeismicSensorEntityDescription(
        key="events_displayed",
        translation_key="events_displayed",
        icon="mdi:map-marker-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.events_displayed,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for Seismic World Earthquakes."""
    coordinator: SeismicWorldEarthquakesCoordinator = entry.runtime_data
    async_add_entities(
        SeismicSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class SeismicSensor(CoordinatorEntity[SeismicWorldEarthquakesCoordinator], SensorEntity):
    """A single seismic summary sensor."""

    entity_description: SeismicSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SeismicWorldEarthquakesCoordinator,
        description: SeismicSensorEntityDescription,
    ) -> None:
        """Initialise."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

        # Unit of measurement for distance sensors uses configured unit
        if description.key in ("nearest_distance",):
            self._attr_native_unit_of_measurement = coordinator._units

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes if defined."""
        if self.coordinator.data is None or self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name=self.coordinator.config_entry.title,
            manufacturer="U.S. Geological Survey (USGS)",
            model="Earthquake Hazards Program API",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://earthquake.usgs.gov/earthquakes/feed/",
        )
