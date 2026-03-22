"""Data update coordinator for Seismic World Earthquakes."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ALERT_LEVELS_ORDER,
    ALERT_LEVEL_NONE,
    ALWAYS_INCLUDE_MAGNITUDE,
    CONF_ALERT_MIN_MAGNITUDE,
    CONF_ALERT_TIME_WINDOW,
    CONF_FEED_PERIOD,
    CONF_INSTANCE_TYPE,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_MAX_DEPTH_KM,
    CONF_MAX_EVENTS,
    CONF_MIN_ALERT_LEVEL,
    CONF_MIN_MAGNITUDE,
    CONF_ONLY_REVIEWED,
    CONF_ONLY_TSUNAMI,
    CONF_RADIUS_KM,
    CONF_SORT_BY,
    CONF_UNITS,
    DEFAULT_ALERT_MIN_MAGNITUDE,
    DEFAULT_ALERT_TIME_WINDOW,
    DEFAULT_FEED_PERIOD,
    DEFAULT_MAX_EVENTS,
    DEFAULT_MIN_ALERT_LEVEL,
    DEFAULT_MIN_MAGNITUDE,
    DEFAULT_SORT_BY,
    DEFAULT_UNITS,
    DOMAIN,
    EARTH_RADIUS_KM,
    FEED_PERIOD_HOUR,
    FEED_PERIOD_WEEK,
    FEED_PERIOD_MONTH,
    FEED_PERIOD_DAY,
    FETCH_MULTIPLIER,
    INSTANCE_TYPE_CUSTOM,
    KM_TO_MI,
    MAX_FETCH_LIMIT,
    SCAN_INTERVAL_MINUTES,
    SHAKEMAP_MIN_MAGNITUDE,
    SIGNIFICANT_EARTHQUAKE_SIG,
    SORT_BY_DISTANCE,
    SORT_BY_MAGNITUDE,
    SORT_BY_TIME,
    UNITS_KM,
    USGS_API_TIMEOUT,
    USGS_API_URL,
    USGS_DETAIL_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class EarthquakeEvent:
    """Represents a single earthquake event."""

    earthquake_id: str
    magnitude: float
    place: str
    time: datetime          # HA local time
    latitude: float
    longitude: float
    depth: float            # km
    status: str             # "automatic" | "reviewed"
    tsunami: bool
    sig: int
    alert: str | None       # "green" | "yellow" | "orange" | "red" | None
    mmi: float | None
    felt: int | None
    cdi: float | None
    mag_type: str
    net: str
    nst: int | None
    dmin: float | None
    rms: float | None
    gap: float | None
    url: str
    title: str
    distance: float | None = None   # Distance to reference in configured units


@dataclass
class SeismicData:
    """All processed seismic data, ready for entity consumption."""

    earthquakes: list[EarthquakeEvent] = field(default_factory=list)
    new_earthquakes: list[EarthquakeEvent] = field(default_factory=list)  # Since last update
    events_fetched: int = 0
    events_displayed: int = 0
    api_status: str = "ok"
    last_update: datetime = field(default_factory=dt_util.now)
    shakemap_url: str | None = None
    # Summary
    total: int = 0
    strongest: EarthquakeEvent | None = None
    latest: EarthquakeEvent | None = None
    nearest: EarthquakeEvent | None = None
    last_hour_count: int = 0
    significant_count: int = 0
    tsunami_count: int = 0
    highest_alert: str | None = None
    red_alert_count: int = 0
    average_magnitude: float = 0.0
    nearest_distance: float | None = None
    nearest_magnitude: float | None = None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two lat/lon points."""
    lat1r, lon1r, lat2r, lon2r = (radians(x) for x in (lat1, lon1, lat2, lon2))
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = sin(dlat / 2) ** 2 + cos(lat1r) * cos(lat2r) * sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * asin(sqrt(a))


def _highest_alert(alerts: list[str | None]) -> str | None:
    """Return the highest PAGER alert level from a list."""
    best: str | None = None
    best_rank = -1
    for alert in alerts:
        if alert and alert in ALERT_LEVELS_ORDER:
            rank = ALERT_LEVELS_ORDER[alert]
            if rank > best_rank:
                best_rank = rank
                best = alert
    return best


class SeismicWorldEarthquakesCoordinator(DataUpdateCoordinator[SeismicData]):
    """Coordinator: fetches USGS data and processes it into SeismicData."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self.config_entry = entry

    # ------------------------------------------------------------------
    # Properties derived from config entry options (with defaults)
    # ------------------------------------------------------------------

    @property
    def _opts(self) -> dict:
        return self.config_entry.options

    @property
    def _min_magnitude(self) -> float:
        return float(self._opts.get(CONF_MIN_MAGNITUDE, DEFAULT_MIN_MAGNITUDE))

    @property
    def _feed_period(self) -> str:
        return self._opts.get(CONF_FEED_PERIOD, DEFAULT_FEED_PERIOD)

    @property
    def _max_events(self) -> int:
        return int(self._opts.get(CONF_MAX_EVENTS, DEFAULT_MAX_EVENTS))

    @property
    def _units(self) -> str:
        return self._opts.get(CONF_UNITS, DEFAULT_UNITS)

    @property
    def _sort_by(self) -> str:
        return self._opts.get(CONF_SORT_BY, DEFAULT_SORT_BY)

    @property
    def _instance_type(self) -> str:
        return self._opts.get(CONF_INSTANCE_TYPE, "global")

    @property
    def _location_dict(self) -> dict:
        """Return the stored LocationSelector dict for custom area instances."""
        return self._opts.get(CONF_LOCATION, {})

    @property
    def _ref_latitude(self) -> float:
        if self._instance_type == INSTANCE_TYPE_CUSTOM:
            return float(self._location_dict.get("latitude", self.hass.config.latitude))
        return self.hass.config.latitude

    @property
    def _ref_longitude(self) -> float:
        if self._instance_type == INSTANCE_TYPE_CUSTOM:
            return float(self._location_dict.get("longitude", self.hass.config.longitude))
        return self.hass.config.longitude

    @property
    def _radius_km(self) -> float | None:
        """Return search radius in km. LocationSelector stores metres."""
        if self._instance_type == INSTANCE_TYPE_CUSTOM:
            radius_m = self._location_dict.get("radius", 500_000)
            return max(10.0, float(radius_m) / 1000.0)
        return None

    @property
    def _min_alert_level(self) -> str:
        return self._opts.get(CONF_MIN_ALERT_LEVEL, DEFAULT_MIN_ALERT_LEVEL)

    @property
    def _only_tsunami(self) -> bool:
        return bool(self._opts.get(CONF_ONLY_TSUNAMI, False))

    @property
    def _max_depth_km(self) -> int | None:
        """Return max depth filter. Value 700 means no limit (passes all depths)."""
        val = self._opts.get(CONF_MAX_DEPTH_KM, 700)
        depth = int(val) if val is not None else 700
        return None if depth >= 700 else depth

    @property
    def _only_reviewed(self) -> bool:
        return bool(self._opts.get(CONF_ONLY_REVIEWED, False))

    @property
    def alert_min_magnitude(self) -> float:
        return float(self._opts.get(CONF_ALERT_MIN_MAGNITUDE, DEFAULT_ALERT_MIN_MAGNITUDE))

    @property
    def alert_time_window(self) -> int:
        return int(self._opts.get(CONF_ALERT_TIME_WINDOW, DEFAULT_ALERT_TIME_WINDOW))

    # ------------------------------------------------------------------
    # Main update method
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> SeismicData:
        """Fetch and process earthquake data from USGS."""
        previous_ids: set[str] = (
            {e.earthquake_id for e in self.data.earthquakes}
            if self.data
            else set()
        )

        raw_features = await self._fetch_usgs()
        if raw_features is None:
            raise UpdateFailed("Failed to retrieve data from USGS API")

        parsed = self._parse_features(raw_features)

        # Client-side filters
        parsed = self._apply_filters(parsed)

        # Intelligent cap: always keep M≥ALWAYS_INCLUDE_MAGNITUDE, then fill by magnitude
        selected = self._apply_intelligent_cap(parsed)

        # Compute distances to reference point
        ref_lat = self._ref_latitude
        ref_lon = self._ref_longitude
        for event in selected:
            dist_km = _haversine_km(ref_lat, ref_lon, event.latitude, event.longitude)
            event.distance = round(dist_km if self._units == UNITS_KM else dist_km * KM_TO_MI, 1)

        # Sort for display
        selected = self._sort_events(selected)

        # New earthquakes since last update (skip on first load to avoid flooding)
        new_quakes: list[EarthquakeEvent] = []
        if previous_ids:
            new_quakes = [e for e in selected if e.earthquake_id not in previous_ids]

        # Build summary
        data = self._build_summary(
            earthquakes=selected,
            new_earthquakes=new_quakes,
            events_fetched=len(raw_features),
        )

        # Best-effort shakemap fetch for strongest event
        if data.strongest and data.strongest.magnitude >= SHAKEMAP_MIN_MAGNITUDE:
            data.shakemap_url = await self._fetch_shakemap_url(data.strongest)

        _LOGGER.debug(
            "%s: fetched %d events, displaying %d, %d new since last update",
            self.config_entry.title,
            data.events_fetched,
            data.events_displayed,
            len(new_quakes),
        )
        return data

    # ------------------------------------------------------------------
    # USGS fetch
    # ------------------------------------------------------------------

    async def _fetch_usgs(self) -> list[dict] | None:
        """Fetch GeoJSON from USGS API. Returns list of features or None on error."""
        period_deltas = {
            FEED_PERIOD_HOUR: timedelta(hours=1),
            FEED_PERIOD_DAY: timedelta(days=1),
            FEED_PERIOD_WEEK: timedelta(weeks=1),
            FEED_PERIOD_MONTH: timedelta(days=30),
        }
        delta = period_deltas.get(self._feed_period, timedelta(days=1))
        start_time = dt_util.utcnow() - delta
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")

        fetch_limit = min(self._max_events * FETCH_MULTIPLIER, MAX_FETCH_LIMIT)

        params: dict[str, Any] = {
            "format": "geojson",
            "starttime": start_str,
            "minmagnitude": self._min_magnitude,
            "orderby": "time",
            "limit": fetch_limit,
        }

        if self._instance_type == INSTANCE_TYPE_CUSTOM and self._radius_km:
            params["latitude"] = self._ref_latitude
            params["longitude"] = self._ref_longitude
            params["maxradiuskm"] = self._radius_km

        if self._max_depth_km:
            params["maxdepth"] = self._max_depth_km

        if self._only_reviewed:
            params["reviewstatus"] = "reviewed"

        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(USGS_API_TIMEOUT):
                async with session.get(USGS_API_URL, params=params) as resp:
                    if resp.status == 400:
                        text = await resp.text()
                        _LOGGER.error(
                            "%s: USGS API returned 400 Bad Request — check configuration parameters. Details: %s",
                            self.config_entry.title,
                            text[:300],
                        )
                        return None
                    if resp.status == 429:
                        _LOGGER.warning(
                            "%s: USGS API rate limited (429). Will retry on next interval.",
                            self.config_entry.title,
                        )
                        return None
                    if resp.status != 200:
                        _LOGGER.warning(
                            "%s: USGS API returned unexpected status %d. Will retry on next interval.",
                            self.config_entry.title,
                            resp.status,
                        )
                        return None
                    geojson = await resp.json(content_type=None)
                    return geojson.get("features", [])

        except asyncio.TimeoutError:
            _LOGGER.warning(
                "%s: Timeout connecting to USGS API after %ds. Will retry.",
                self.config_entry.title,
                USGS_API_TIMEOUT,
            )
            return None
        except aiohttp.ClientError as err:
            _LOGGER.warning(
                "%s: Connection error fetching USGS data: %s. Will retry.",
                self.config_entry.title,
                err,
            )
            return None

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_features(self, features: list[dict]) -> list[EarthquakeEvent]:
        """Parse raw USGS GeoJSON features into EarthquakeEvent objects."""
        events: list[EarthquakeEvent] = []
        for feature in features:
            try:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [None, None, None])

                lon = coords[0]
                lat = coords[1]
                depth = coords[2] or 0.0

                if lat is None or lon is None:
                    continue

                time_ms = props.get("time")
                if time_ms is None:
                    continue

                local_time = dt_util.as_local(dt_util.utc_from_timestamp(time_ms / 1000))

                events.append(
                    EarthquakeEvent(
                        earthquake_id=feature.get("id", ""),
                        magnitude=float(props.get("mag") or 0.0),
                        place=props.get("place") or "Unknown location",
                        time=local_time,
                        latitude=float(lat),
                        longitude=float(lon),
                        depth=float(depth),
                        status=props.get("status") or "automatic",
                        tsunami=bool(props.get("tsunami", 0)),
                        sig=int(props.get("sig") or 0),
                        alert=props.get("alert"),
                        mmi=props.get("mmi"),
                        felt=props.get("felt"),
                        cdi=props.get("cdi"),
                        mag_type=props.get("magType") or "unknown",
                        net=props.get("net") or "us",
                        nst=props.get("nst"),
                        dmin=props.get("dmin"),
                        rms=props.get("rms"),
                        gap=props.get("gap"),
                        url=props.get("url") or "",
                        title=props.get("title") or f"M{props.get('mag')} earthquake",
                    )
                )
            except (KeyError, TypeError, ValueError) as err:
                _LOGGER.debug("Skipping malformed earthquake feature: %s", err)
                continue

        return events

    # ------------------------------------------------------------------
    # Client-side filters
    # ------------------------------------------------------------------

    def _apply_filters(self, events: list[EarthquakeEvent]) -> list[EarthquakeEvent]:
        """Apply optional client-side filters."""
        if self._only_tsunami:
            events = [e for e in events if e.tsunami]

        if self._min_alert_level != ALERT_LEVEL_NONE:
            min_rank = ALERT_LEVELS_ORDER.get(self._min_alert_level, 0)
            events = [
                e for e in events
                if e.alert and ALERT_LEVELS_ORDER.get(e.alert, -1) >= min_rank
            ]

        return events

    # ------------------------------------------------------------------
    # Intelligent cap
    # ------------------------------------------------------------------

    def _apply_intelligent_cap(self, events: list[EarthquakeEvent]) -> list[EarthquakeEvent]:
        """
        Cap events at max_events, but always retain events with M≥ALWAYS_INCLUDE_MAGNITUDE.
        Selection order: strongest always included, then fill by magnitude descending.
        """
        if len(events) <= self._max_events:
            return events

        by_magnitude = sorted(events, key=lambda e: e.magnitude, reverse=True)
        must_keep = [e for e in by_magnitude if e.magnitude >= ALWAYS_INCLUDE_MAGNITUDE]
        optional = [e for e in by_magnitude if e.magnitude < ALWAYS_INCLUDE_MAGNITUDE]

        remaining = max(0, self._max_events - len(must_keep))
        selected = must_keep + optional[:remaining]

        if len(selected) < len(events):
            _LOGGER.debug(
                "%s: Capped events from %d to %d (always kept %d with M≥%.1f)",
                self.config_entry.title,
                len(events),
                len(selected),
                len(must_keep),
                ALWAYS_INCLUDE_MAGNITUDE,
            )

        return selected

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def _sort_events(self, events: list[EarthquakeEvent]) -> list[EarthquakeEvent]:
        """Sort events for display based on configuration."""
        sort_by = self._sort_by
        if sort_by == SORT_BY_TIME:
            return sorted(events, key=lambda e: e.time, reverse=True)
        if sort_by == SORT_BY_DISTANCE:
            return sorted(
                events,
                key=lambda e: e.distance if e.distance is not None else float("inf"),
            )
        # Default: magnitude descending
        return sorted(events, key=lambda e: e.magnitude, reverse=True)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _build_summary(
        self,
        earthquakes: list[EarthquakeEvent],
        new_earthquakes: list[EarthquakeEvent],
        events_fetched: int,
    ) -> SeismicData:
        """Compute all summary fields from the selected event list."""
        now = dt_util.now()
        one_hour_ago = now - timedelta(hours=1)

        strongest: EarthquakeEvent | None = (
            max(earthquakes, key=lambda e: e.magnitude) if earthquakes else None
        )
        latest: EarthquakeEvent | None = (
            max(earthquakes, key=lambda e: e.time) if earthquakes else None
        )
        nearest: EarthquakeEvent | None = (
            min(
                (e for e in earthquakes if e.distance is not None),
                key=lambda e: e.distance,  # type: ignore[arg-type]
                default=None,
            )
        )

        last_hour = [e for e in earthquakes if e.time >= one_hour_ago]
        significant = [e for e in earthquakes if e.sig >= SIGNIFICANT_EARTHQUAKE_SIG]
        with_tsunami = [e for e in earthquakes if e.tsunami]
        red_alerts = [e for e in earthquakes if e.alert == "red"]

        avg_mag = (
            round(sum(e.magnitude for e in earthquakes) / len(earthquakes), 2)
            if earthquakes
            else 0.0
        )

        return SeismicData(
            earthquakes=earthquakes,
            new_earthquakes=new_earthquakes,
            events_fetched=events_fetched,
            events_displayed=len(earthquakes),
            api_status="ok",
            last_update=now,
            total=len(earthquakes),
            strongest=strongest,
            latest=latest,
            nearest=nearest,
            last_hour_count=len(last_hour),
            significant_count=len(significant),
            tsunami_count=len(with_tsunami),
            highest_alert=_highest_alert([e.alert for e in earthquakes]),
            red_alert_count=len(red_alerts),
            average_magnitude=avg_mag,
            nearest_distance=nearest.distance if nearest else None,
            nearest_magnitude=nearest.magnitude if nearest else None,
        )

    # ------------------------------------------------------------------
    # Shakemap fetch (best-effort)
    # ------------------------------------------------------------------

    async def _fetch_shakemap_url(self, event: EarthquakeEvent) -> str | None:
        """Attempt to retrieve the intensity shakemap image URL from USGS detail API."""
        detail_url = (
            f"https://earthquake.usgs.gov/fdsnws/event/1/query"
            f"?eventid={event.earthquake_id}&format=geojson"
        )
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(USGS_DETAIL_TIMEOUT):
                async with session.get(detail_url) as resp:
                    if resp.status != 200:
                        return None
                    detail = await resp.json(content_type=None)
                    products = detail.get("properties", {}).get("products", {})
                    shakemaps = products.get("shakemap", [])
                    if not shakemaps:
                        return None
                    contents = shakemaps[0].get("contents", {})
                    # Prefer intensity.jpg, fall back to intensity.png
                    for key in ("download/intensity.jpg", "download/intensity.png"):
                        if key in contents:
                            return contents[key].get("url")
        except (asyncio.TimeoutError, aiohttp.ClientError, KeyError, TypeError) as err:
            _LOGGER.debug(
                "%s: Could not fetch shakemap for event %s: %s",
                self.config_entry.title,
                event.earthquake_id,
                err,
            )
        return None
