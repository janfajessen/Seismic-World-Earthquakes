"""Constants for Seismic World Earthquakes."""
from __future__ import annotations

DOMAIN = "seismic_world_earthquakes"
PLATFORMS = [
    "geo_location",
    "sensor",
    "binary_sensor",
    "button",
    "image",
    "calendar",
    "event",
]

# --- Config keys ---
CONF_INSTANCE_TYPE = "instance_type"
CONF_MIN_MAGNITUDE = "min_magnitude"
CONF_FEED_PERIOD = "feed_period"
CONF_MAX_EVENTS = "max_events"
CONF_UNITS = "units"
CONF_SORT_BY = "sort_by"
# LocationSelector stores {latitude, longitude, radius} where radius is in metres
CONF_LOCATION = "location"
# Legacy keys kept for coordinator internal use
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_RADIUS_KM = "radius_km"
CONF_MIN_ALERT_LEVEL = "min_alert_level"
CONF_ONLY_TSUNAMI = "only_tsunami"
CONF_MAX_DEPTH_KM = "max_depth_km"
CONF_ONLY_REVIEWED = "only_reviewed"
CONF_ALERT_MIN_MAGNITUDE = "alert_min_magnitude"
CONF_ALERT_TIME_WINDOW = "alert_time_window"

# --- Instance types ---
INSTANCE_TYPE_GLOBAL = "global"
INSTANCE_TYPE_CUSTOM = "custom_area"

# --- Feed periods ---
FEED_PERIOD_HOUR = "hour"
FEED_PERIOD_DAY = "day"
FEED_PERIOD_WEEK = "week"
FEED_PERIOD_MONTH = "month"

# --- Units ---
UNITS_KM = "km"
UNITS_MI = "mi"

# --- Sort options ---
SORT_BY_MAGNITUDE = "magnitude"
SORT_BY_TIME = "time"
SORT_BY_DISTANCE = "distance"

# --- Alert levels (ordered low→high) ---
ALERT_LEVELS_ORDER: dict[str, int] = {
    "green": 0,
    "yellow": 1,
    "orange": 2,
    "red": 3,
}
ALERT_LEVEL_NONE = "none"

# --- Defaults ---
DEFAULT_MIN_MAGNITUDE = 4.5
DEFAULT_FEED_PERIOD = FEED_PERIOD_DAY
DEFAULT_MAX_EVENTS = 100
DEFAULT_UNITS = UNITS_KM
DEFAULT_SORT_BY = SORT_BY_MAGNITUDE
DEFAULT_MIN_ALERT_LEVEL = ALERT_LEVEL_NONE
DEFAULT_ONLY_TSUNAMI = False
DEFAULT_ONLY_REVIEWED = False
DEFAULT_ALERT_MIN_MAGNITUDE = 5.0
DEFAULT_ALERT_TIME_WINDOW = 24
DEFAULT_RADIUS_KM = 500.0

# --- API ---
USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_API_TIMEOUT = 30
USGS_DETAIL_TIMEOUT = 15
SCAN_INTERVAL_MINUTES = 5

# --- Logic ---
ALWAYS_INCLUDE_MAGNITUDE = 6.0          # M≥6 always kept regardless of max_events cap
SIGNIFICANT_EARTHQUAKE_SIG = 600        # USGS significance score threshold
SHAKEMAP_MIN_MAGNITUDE = 4.5            # Shakemaps generally exist from M4.5+
FETCH_MULTIPLIER = 2                    # Fetch max_events * this from USGS before client-side filter
MAX_FETCH_LIMIT = 1000                  # Hard cap for USGS requests

# --- Geo location source ---
SOURCE = DOMAIN

# --- Distance conversion ---
KM_TO_MI = 0.621371
EARTH_RADIUS_KM = 6371.0
