"""Geo-location entities for Seismic World Earthquakes — one pin per earthquake on the HA map."""
from __future__ import annotations

import logging
from collections.abc import Callable

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SOURCE, UNITS_KM
from .coordinator import EarthquakeEvent, SeismicWorldEarthquakesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the geo_location platform — manages dynamic earthquake pins on the map."""
    coordinator: SeismicWorldEarthquakesCoordinator = entry.runtime_data
    managed: dict[str, SeismicGeolocationEvent] = {}

    @callback
    def _handle_coordinator_update() -> None:
        """Diff the current event list and add/remove/update entities accordingly."""
        if coordinator.data is None:
            return

        current_ids: set[str] = {e.earthquake_id for e in coordinator.data.earthquakes}
        existing_ids: set[str] = set(managed.keys())

        # Remove stale entities
        for eid in existing_ids - current_ids:
            entity = managed.pop(eid)
            hass.async_create_task(entity.async_remove(force_remove=True))
            _LOGGER.debug("Removed geo_location entity for earthquake %s", eid)

        # Update existing
        for eid in existing_ids & current_ids:
            managed[eid].async_write_ha_state()

        # Add new
        new_entities: list[SeismicGeolocationEvent] = []
        quake_map = {e.earthquake_id: e for e in coordinator.data.earthquakes}
        for eid in current_ids - existing_ids:
            entity = SeismicGeolocationEvent(coordinator, quake_map[eid])
            managed[eid] = entity
            new_entities.append(entity)

        if new_entities:
            async_add_entities(new_entities)
            _LOGGER.debug("Added %d new geo_location entities", len(new_entities))

    # Subscribe to future coordinator updates
    entry.async_on_unload(coordinator.async_add_listener(_handle_coordinator_update))

    # Process the initial data already loaded by async_config_entry_first_refresh
    _handle_coordinator_update()


class SeismicGeolocationEvent(GeolocationEvent):
    """A single earthquake pin on the Home Assistant map."""

    _attr_should_poll = False
    _attr_source = SOURCE

    def __init__(
        self,
        coordinator: SeismicWorldEarthquakesCoordinator,
        earthquake: EarthquakeEvent,
    ) -> None:
        """Initialise the geo-location entity."""
        self._coordinator = coordinator
        self._earthquake = earthquake

        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_geo_{earthquake.earthquake_id}"
        self._attr_name = earthquake.title
        self._attr_latitude = earthquake.latitude
        self._attr_longitude = earthquake.longitude
        self._attr_unit_of_measurement = coordinator._units
        self._attr_icon = self._magnitude_icon(earthquake.magnitude)

    @property
    def device_info(self) -> DeviceInfo:
        """Associate this pin with the integration device so it appears on the device page."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.config_entry.entry_id)},
            name=self._coordinator.config_entry.title,
            manufacturer="U.S. Geological Survey (USGS)",
            model="Earthquake Hazards Program API",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://earthquake.usgs.gov/earthquakes/feed/",
        )

    # ------------------------------------------------------------------
    # State: distance to reference point (geo_location convention)
    # ------------------------------------------------------------------

    @property
    def distance(self) -> float | None:
        """Return distance to the reference point in the configured unit."""
        # Re-read from coordinator data so updates reflect in existing entities
        for event in self._coordinator.data.earthquakes if self._coordinator.data else []:
            if event.earthquake_id == self._earthquake.earthquake_id:
                return event.distance
        return self._earthquake.distance

    @property
    def extra_state_attributes(self) -> dict:
        """Return detailed attributes for this earthquake."""
        eq = self._earthquake
        # Re-read updated version if available
        if self._coordinator.data:
            for event in self._coordinator.data.earthquakes:
                if event.earthquake_id == eq.earthquake_id:
                    eq = event
                    break

        attrs: dict = {
            "earthquake_id": eq.earthquake_id,
            "magnitude": eq.magnitude,
            "magnitude_type": eq.mag_type,
            "place": eq.place,
            "time": eq.time.isoformat(),
            "depth_km": eq.depth,
            "status": eq.status,
            "tsunami_warning": eq.tsunami,
            "significance": eq.sig,
            "alert_level": eq.alert,
            "max_intensity_mmi": eq.mmi,
            "community_intensity_cdi": eq.cdi,
            "felt_reports": eq.felt,
            "network": eq.net,
            "station_count": eq.nst,
            "azimuthal_gap": eq.gap,
            "rms_residual": eq.rms,
            "min_station_distance_deg": eq.dmin,
            "url": eq.url,
            "integration": DOMAIN,
        }
        return {k: v for k, v in attrs.items() if v is not None}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _magnitude_icon(magnitude: float) -> str:
        """Return an appropriate icon based on magnitude."""
        if magnitude >= 7.0:
            return "mdi:alert-circle"
        if magnitude >= 6.0:
            return "mdi:alert"
        if magnitude >= 5.0:
            return "mdi:alert-outline"
        if magnitude >= 4.0:
            return "mdi:map-marker-alert"
        if magnitude >= 3.0:
            return "mdi:map-marker-radius"
        return "mdi:map-marker"
        
