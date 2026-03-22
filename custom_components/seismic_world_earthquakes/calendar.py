"""Calendar entity for Seismic World Earthquakes."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import EarthquakeEvent, SeismicWorldEarthquakesCoordinator

_LOGGER = logging.getLogger(__name__)

# Each earthquake "occupies" 1 hour on the calendar for visibility
_EVENT_DURATION = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calendar entities."""
    coordinator: SeismicWorldEarthquakesCoordinator = entry.runtime_data
    async_add_entities([SeismicCalendar(coordinator)])


def _to_calendar_event(eq: EarthquakeEvent) -> CalendarEvent:
    """Convert an EarthquakeEvent to a CalendarEvent."""
    alert_str = f" | ⚠️ Alert: {eq.alert.upper()}" if eq.alert else ""
    tsunami_str = " | 🌊 TSUNAMI" if eq.tsunami else ""

    summary = f"M{eq.magnitude:.1f} — {eq.place}"

    description_parts = [
        f"Magnitude: {eq.magnitude:.1f} ({eq.mag_type})",
        f"Depth: {eq.depth:.1f} km",
        f"Status: {eq.status}",
    ]
    if eq.sig:
        description_parts.append(f"Significance: {eq.sig}/1000")
    if eq.alert:
        description_parts.append(f"PAGER Alert: {eq.alert.upper()}")
    if eq.tsunami:
        description_parts.append("🌊 TSUNAMI WARNING ACTIVE")
    if eq.felt:
        description_parts.append(f"Felt reports: {eq.felt}")
    if eq.mmi:
        description_parts.append(f"Max intensity (MMI): {eq.mmi:.1f}")
    description_parts.append(f"Network: {eq.net}")
    description_parts.append(f"ID: {eq.earthquake_id}")
    description_parts.append(f"URL: {eq.url}")

    return CalendarEvent(
        start=eq.time,
        end=eq.time + _EVENT_DURATION,
        summary=summary,
        description="\n".join(description_parts),
        location=f"{eq.latitude:.4f}, {eq.longitude:.4f}",
    )


class SeismicCalendar(CoordinatorEntity[SeismicWorldEarthquakesCoordinator], CalendarEntity):
    """Calendar entity showing all earthquakes in the current data window."""

    _attr_has_entity_name = True
    _attr_translation_key = "earthquakes"
    _attr_icon = "mdi:calendar-alert"

    def __init__(self, coordinator: SeismicWorldEarthquakesCoordinator) -> None:
        """Initialise."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_calendar"

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

    @property
    def event(self) -> CalendarEvent | None:
        """
        Return the most recent earthquake as the 'current' calendar event.
        This makes the calendar show activity in the HA dashboard card.
        """
        if self.coordinator.data is None or not self.coordinator.data.latest:
            return None
        return _to_calendar_event(self.coordinator.data.latest)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return all earthquakes that fall within the requested date range."""
        if self.coordinator.data is None:
            return []

        events: list[CalendarEvent] = []
        for eq in self.coordinator.data.earthquakes:
            event_end = eq.time + _EVENT_DURATION
            # Include if event overlaps with the requested range
            if eq.time <= end_date and event_end >= start_date:
                events.append(_to_calendar_event(eq))

        # Sort chronologically for the calendar view
        events.sort(key=lambda e: e.start, reverse=True)
        return events
