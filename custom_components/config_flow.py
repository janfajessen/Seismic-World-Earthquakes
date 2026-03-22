"""Config flow and Options flow for Seismic World Earthquakes."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .const import (
    ALERT_LEVEL_NONE,
    CONF_ALERT_MIN_MAGNITUDE,
    CONF_ALERT_TIME_WINDOW,
    CONF_FEED_PERIOD,
    CONF_INSTANCE_TYPE,
    CONF_LOCATION,
    CONF_MAX_DEPTH_KM,
    CONF_MAX_EVENTS,
    CONF_MIN_ALERT_LEVEL,
    CONF_MIN_MAGNITUDE,
    CONF_ONLY_REVIEWED,
    CONF_ONLY_TSUNAMI,
    CONF_SORT_BY,
    CONF_UNITS,
    DEFAULT_ALERT_MIN_MAGNITUDE,
    DEFAULT_ALERT_TIME_WINDOW,
    DEFAULT_FEED_PERIOD,
    DEFAULT_MAX_EVENTS,
    DEFAULT_MIN_ALERT_LEVEL,
    DEFAULT_MIN_MAGNITUDE,
    DEFAULT_ONLY_REVIEWED,
    DEFAULT_ONLY_TSUNAMI,
    DEFAULT_SORT_BY,
    DEFAULT_UNITS,
    DOMAIN,
    FEED_PERIOD_DAY,
    FEED_PERIOD_HOUR,
    FEED_PERIOD_MONTH,
    FEED_PERIOD_WEEK,
    INSTANCE_TYPE_CUSTOM,
    INSTANCE_TYPE_GLOBAL,
    SORT_BY_DISTANCE,
    SORT_BY_MAGNITUDE,
    SORT_BY_TIME,
    UNITS_KM,
    UNITS_MI,
    USGS_API_URL,
)

_LOGGER = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Shared schema helpers
# ──────────────────────────────────────────────

def _basic_schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("name", default=defaults.get("name", "Seismic World Earthquakes")): selector.selector(
                {"text": {}}
            ),
            vol.Required(CONF_INSTANCE_TYPE, default=defaults.get(CONF_INSTANCE_TYPE, INSTANCE_TYPE_GLOBAL)): selector.selector(
                {
                    "select": {
                        "options": [INSTANCE_TYPE_GLOBAL, INSTANCE_TYPE_CUSTOM],
                        "translation_key": "instance_type",
                        "mode": "list",
                    }
                }
            ),
            vol.Required(CONF_MIN_MAGNITUDE, default=defaults.get(CONF_MIN_MAGNITUDE, DEFAULT_MIN_MAGNITUDE)): selector.selector(
                {"number": {"min": 0.0, "max": 9.9, "step": 0.1, "mode": "slider"}}
            ),
            vol.Required(CONF_FEED_PERIOD, default=defaults.get(CONF_FEED_PERIOD, DEFAULT_FEED_PERIOD)): selector.selector(
                {
                    "select": {
                        "options": [FEED_PERIOD_HOUR, FEED_PERIOD_DAY, FEED_PERIOD_WEEK, FEED_PERIOD_MONTH],
                        "translation_key": "feed_period",
                        "mode": "list",
                    }
                }
            ),
            vol.Required(CONF_MAX_EVENTS, default=defaults.get(CONF_MAX_EVENTS, DEFAULT_MAX_EVENTS)): selector.selector(
                {"number": {"min": 50, "max": 500, "step": 50, "mode": "slider"}}
            ),
            vol.Required(CONF_UNITS, default=defaults.get(CONF_UNITS, DEFAULT_UNITS)): selector.selector(
                {
                    "select": {
                        "options": [UNITS_KM, UNITS_MI],
                        "translation_key": "units",
                        "mode": "list",
                    }
                }
            ),
            vol.Required(CONF_SORT_BY, default=defaults.get(CONF_SORT_BY, DEFAULT_SORT_BY)): selector.selector(
                {
                    "select": {
                        "options": [SORT_BY_MAGNITUDE, SORT_BY_TIME, SORT_BY_DISTANCE],
                        "translation_key": "sort_by",
                        "mode": "list",
                    }
                }
            ),
        }
    )


def _area_schema(defaults: dict) -> vol.Schema:
    """
    Area step schema using HA's native LocationSelector.
    Shows an interactive map with draggable radius circle.
    The selector stores: {latitude, longitude, radius} where radius is in METRES.
    """
    default_loc = defaults.get(CONF_LOCATION) or {
        "latitude": defaults.get("_hass_lat", 0.0),
        "longitude": defaults.get("_hass_lon", 0.0),
        "radius": 500_000,   # 500 km in metres (default)
    }
    return vol.Schema(
        {
            vol.Required(CONF_LOCATION, default=default_loc): selector.selector(
                {"location": {"radius": True, "icon": "mdi:map-marker-radius"}}
            ),
        }
    )


def _filters_schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_MIN_ALERT_LEVEL, default=defaults.get(CONF_MIN_ALERT_LEVEL, DEFAULT_MIN_ALERT_LEVEL)): selector.selector(
                {
                    "select": {
                        "options": [ALERT_LEVEL_NONE, "green", "yellow", "orange", "red"],
                        "translation_key": "alert_level",
                        "mode": "list",
                    }
                }
            ),
            vol.Required(CONF_ONLY_TSUNAMI, default=defaults.get(CONF_ONLY_TSUNAMI, DEFAULT_ONLY_TSUNAMI)): selector.selector(
                {"boolean": {}}
            ),
            vol.Required(CONF_MAX_DEPTH_KM, default=defaults.get(CONF_MAX_DEPTH_KM, 700)): selector.selector(
                {"number": {"min": 0, "max": 700, "step": 10, "mode": "box", "unit_of_measurement": "km"}}
            ),
            vol.Required(CONF_ONLY_REVIEWED, default=defaults.get(CONF_ONLY_REVIEWED, DEFAULT_ONLY_REVIEWED)): selector.selector(
                {"boolean": {}}
            ),
            vol.Required(CONF_ALERT_MIN_MAGNITUDE, default=defaults.get(CONF_ALERT_MIN_MAGNITUDE, DEFAULT_ALERT_MIN_MAGNITUDE)): selector.selector(
                {"number": {"min": 0.0, "max": 9.9, "step": 0.1, "mode": "slider"}}
            ),
            vol.Required(CONF_ALERT_TIME_WINDOW, default=defaults.get(CONF_ALERT_TIME_WINDOW, DEFAULT_ALERT_TIME_WINDOW)): selector.selector(
                {"number": {"min": 1, "max": 72, "step": 1, "mode": "slider", "unit_of_measurement": "h"}}
            ),
        }
    )


async def _test_api_connection(hass) -> bool:
    """Quick connectivity test to USGS API."""
    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(10):
            async with session.get(
                USGS_API_URL,
                params={"format": "geojson", "starttime": "2000-01-01", "endtime": "2000-01-01", "limit": 1},
            ) as resp:
                return resp.status == 200
    except (asyncio.TimeoutError, aiohttp.ClientError):
        return False


def _validate_coordinates(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


# ──────────────────────────────────────────────
# Config Flow
# ──────────────────────────────────────────────

class SeismicWorldEarthquakesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Seismic World Earthquakes."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise."""
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SeismicWorldEarthquakesOptionsFlow:
        """Return the options flow handler."""
        return SeismicWorldEarthquakesOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1 — basic settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not await _test_api_connection(self.hass):
                errors["base"] = "cannot_connect"
            else:
                self._data.update(user_input)
                if user_input.get(CONF_INSTANCE_TYPE) == INSTANCE_TYPE_CUSTOM:
                    return await self.async_step_area()
                return await self.async_step_filters()

        return self.async_show_form(
            step_id="user",
            data_schema=_basic_schema(self._data),
            errors=errors,
        )

    async def async_step_area(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2 — custom area. Uses LocationSelector (map + radius circle)."""
        errors: dict[str, str] = {}

        defaults = {
            CONF_LOCATION: self._data.get(CONF_LOCATION),
            "_hass_lat": self.hass.config.latitude,
            "_hass_lon": self.hass.config.longitude,
        }

        if user_input is not None:
            loc = user_input.get(CONF_LOCATION, {})
            lat = loc.get("latitude", 0.0)
            lon = loc.get("longitude", 0.0)
            radius_m = loc.get("radius", 500_000)
            if not _validate_coordinates(lat, lon):
                errors[CONF_LOCATION] = "invalid_coordinates"
            elif radius_m < 10_000:   # 10 km minimum in metres
                errors[CONF_LOCATION] = "invalid_radius"
            else:
                self._data[CONF_LOCATION] = loc
                return await self.async_step_filters()

        return self.async_show_form(
            step_id="area",
            data_schema=_area_schema(defaults),
            errors=errors,
        )

    async def async_step_filters(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 3 — optional filters and alert sensor config."""
        if user_input is not None:
            self._data.update(user_input)
            name = self._data.pop("name", "Seismic World Earthquakes")
            return self.async_create_entry(title=name, data={}, options=self._data)

        return self.async_show_form(
            step_id="filters",
            data_schema=_filters_schema(self._data),
        )


# ──────────────────────────────────────────────
# Options Flow (reconfiguración / rueda ⚙️)
# ──────────────────────────────────────────────

class SeismicWorldEarthquakesOptionsFlow(OptionsFlow):
    """Handle the options flow (reconfiguration) for Seismic World Earthquakes."""

    def __init__(self) -> None:
        """Initialise. self.config_entry is injected by HA before any step runs."""
        self._data: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1 — basic settings (same as config flow user step)."""
        errors: dict[str, str] = {}

        # Populate _data from current options on first entry into this step
        if not self._data:
            self._data = dict(self.config_entry.options)
        if "name" not in self._data:
            self._data["name"] = self.config_entry.title

        if user_input is not None:
            self._data.update(user_input)
            if user_input.get(CONF_INSTANCE_TYPE) == INSTANCE_TYPE_CUSTOM:
                return await self.async_step_area()
            return await self.async_step_filters()

        return self.async_show_form(
            step_id="init",
            data_schema=_basic_schema(self._data),
            errors=errors,
        )

    async def async_step_area(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2 — custom area (reconfiguration)."""
        errors: dict[str, str] = {}

        defaults = {
            CONF_LOCATION: self._data.get(CONF_LOCATION),
            "_hass_lat": self.hass.config.latitude,
            "_hass_lon": self.hass.config.longitude,
        }

        if user_input is not None:
            loc = user_input.get(CONF_LOCATION, {})
            lat = loc.get("latitude", 0.0)
            lon = loc.get("longitude", 0.0)
            radius_m = loc.get("radius", 500_000)
            if not _validate_coordinates(lat, lon):
                errors[CONF_LOCATION] = "invalid_coordinates"
            elif radius_m < 10_000:
                errors[CONF_LOCATION] = "invalid_radius"
            else:
                self._data[CONF_LOCATION] = loc
                return await self.async_step_filters()

        return self.async_show_form(
            step_id="area",
            data_schema=_area_schema(defaults),
            errors=errors,
        )

    async def async_step_filters(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 3 — filters and alert config."""
        if user_input is not None:
            self._data.update(user_input)
            # Update entry title if name changed
            new_name = self._data.pop("name", self.config_entry.title)
            self.hass.config_entries.async_update_entry(
                self.config_entry, title=new_name
            )
            return self.async_create_entry(data=self._data)

        return self.async_show_form(
            step_id="filters",
            data_schema=_filters_schema(self._data),
        )
