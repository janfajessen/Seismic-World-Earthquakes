# 🌍 Seismic World Earthquakes

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)
![HA](https://img.shields.io/badge/Home%20Assistant-2024.1+-orange?style=for-the-badge&logo=home-assistant)
![HACS](https://img.shields.io/badge/HACS-Custom-teal?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Real-time global earthquake monitoring for Home Assistant**

Data from the [USGS Earthquake Hazards Program API](https://earthquake.usgs.gov/fdsnws/event/1/) · No API key required · Free

</div>

---

## Description

A Home Assistant custom integration that displays earthquakes worldwide — or within a custom area — in real time, directly from the USGS public API. Each earthquake appears as a **pin on the HA map**, with summary sensors, configurable alerts, a calendar of events, and much more. No account or API key needed.

---

## Features

- 🗺️ **Map pins** — one dynamic pin per earthquake, icon changes by magnitude
- 📊 **17 sensors** — total count, strongest magnitude, average magnitude, latest event, nearest earthquake, PAGER alert levels, tsunami count, and more
- 🔔 **Configurable alert binary sensor** — triggers based on magnitude threshold and time window
- 🌊 **Tsunami binary sensor** — turns ON if any current event carries a tsunami flag
- 🖼️ **ShakeMap image** — USGS intensity map for the strongest earthquake (M ≥ 4.5)
- 📅 **Calendar** — every earthquake as a 1-hour calendar event with full details
- ⚡ **Event entity** — fires HA events to trigger automations on newly detected earthquakes
- 🌍 **Global or custom area** — interactive map selector with adjustable radius
- 🔄 **Multiple instances** — monitor different areas or thresholds simultaneously
- 🌐 **Multilingual** — EN, CA, ES, FR (more coming)

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → ⋮ menu → **Custom Repositories**
2. Add URL: `https://github.com/janfajessen/seismic_world_earthquakes`
3. Category: **Integration**
4. Search for **Seismic World Earthquakes** and install
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → + Add Integration**
7. Search for **Seismic World Earthquakes**

### Manual

1. Copy the `custom_components/seismic_world_earthquakes` folder into your HA `custom_components` directory
2. Restart Home Assistant
3. Add the integration from **Settings → Devices & Services**

---

## Configuration

Setup is done in **3 steps** through the config flow UI.

### Step 1 — Basic settings

| Option | Description | Default |
|---|---|---|
| Instance name | Friendly name for this instance | `Seismic World Earthquakes` |
| Instance type | Global (worldwide) or Custom area (radius) | Global |
| Minimum magnitude | Richter scale threshold (0.0–9.9) | 4.5 |
| Data period | Last hour / 24 h / 7 days / 30 days | 24 h |
| Maximum events | Map pin limit (50–500) | 100 |
| Distance units | Kilometres or miles | km |
| Sort events by | Magnitude / Time / Distance | Magnitude |

> **Note:** Events with M ≥ 6.0 are always retained regardless of the maximum events limit.

### Step 2 — Custom area *(only for custom area instances)*

An interactive map selector lets you drag a pin to set the centre point and adjust the radius circle visually. Minimum radius: 10 km.

### Step 3 — Filters & alert sensor

| Option | Description | Default |
|---|---|---|
| Minimum PAGER alert level | None / Green / Yellow / Orange / Red | None |
| Only tsunami events | Filter to show only events with tsunami flag | Off |
| Maximum depth (km) | 0–700 · set to 700 for no limit | 700 |
| Only reviewed events | USGS quality filter — more accurate, may be delayed | Off |
| Alert sensor — min magnitude | Magnitude threshold for the alert binary sensor | 5.0 |
| Alert sensor — time window | Hours to look back when evaluating the alert (1–72) | 24 |

---

## Entities

### 📍 Geo-location
One map pin per active earthquake. State = distance to the reference point in the configured unit.

| Icon | Magnitude |
|---|---|
| `mdi:alert-circle` | M ≥ 7.0 |
| `mdi:alert` | M ≥ 6.0 |
| `mdi:alert-outline` | M ≥ 5.0 |
| `mdi:map-marker-alert` | M ≥ 4.0 |
| `mdi:map-marker-radius` | M ≥ 3.0 |
| `mdi:map-marker` | M < 3.0 |

Each pin includes full attributes: magnitude, depth, place, time, alert level, tsunami flag, significance score, USGS URL, and more.

### 📊 Main sensors

| Sensor | Description |
|---|---|
| Total earthquakes | Total events in the configured period |
| Strongest earthquake | Maximum magnitude in the period |
| Strongest earthquake location | Place name of the highest-magnitude event |
| Average magnitude | Mean magnitude across all events |
| Latest earthquake | Title of the most recent event |
| Latest earthquake time | Timestamp of the most recent event |
| Earthquakes last hour | Count of events in the last 60 minutes |
| Significant earthquakes | Events with USGS significance score ≥ 600 |
| Active tsunami warnings | Count of events carrying a tsunami flag |
| Highest alert level | Highest PAGER alert level in the period |
| Red alert events | Count of events with PAGER RED alert |
| Nearest earthquake distance | Distance to the nearest event in km or mi |
| Nearest earthquake magnitude | Magnitude of the nearest event |

### 📊 Diagnostic sensors

| Sensor | Description |
|---|---|
| Last update | Timestamp of the last successful data refresh |
| API status | `ok` or error description |
| Events fetched | Total events downloaded from USGS API |
| Events displayed | Total after applying filters and the event cap |

### 🔔 Binary sensors

| Sensor | Turns ON when... |
|---|---|
| Earthquake alert | An event ≥ configured magnitude exists within the time window |
| Tsunami warning active | Any current event has a tsunami flag |

### 🖼️ Image — ShakeMap
Seismic intensity image for the strongest current earthquake, fetched directly from USGS.

> ⚠️ **USGS ShakeMaps are only available for earthquakes with magnitude ≥ 4.5 (Richter scale).** Below this threshold the image entity will show as unavailable.

### 📅 Calendar
Every earthquake appears as a 1-hour calendar event with full details in the description, including depth, alert level, significance score, felt reports, and a link to the USGS event page.

### ⚡ Event entity — New earthquake detected
Fires a Home Assistant event (`earthquake_detected`) each time a new earthquake appears in the feed. **Earthquakes already present on first load are skipped** to avoid flooding automations on startup. Events are fired in descending magnitude order.

Event attributes include: `magnitude`, `place`, `time`, `latitude`, `longitude`, `depth_km`, `tsunami_warning`, `alert_level`, `significance`, `url`, and more.

### 🔘 Button — Force refresh
Forces an immediate data refresh without waiting for the 5-minute cycle.

---

## Automation examples

### Notification for significant earthquakes

```yaml
automation:
  - alias: "Significant earthquake alert"
    trigger:
      - platform: event
        event_type: seismic_world_earthquakes_event
        event_data:
          event_type: earthquake_detected
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.magnitude >= 6.0 }}"
    action:
      - service: notify.notify
        data:
          title: "🌍 M{{ trigger.event.data.magnitude }} Earthquake"
          message: >
            {{ trigger.event.data.place }}
            Depth: {{ trigger.event.data.depth_km }} km
            {{ trigger.event.data.url }}
```

### Tsunami warning notification

```yaml
automation:
  - alias: "Tsunami warning active"
    trigger:
      - platform: state
        entity_id: binary_sensor.seismic_world_earthquakes_tsunami_warning
        to: "on"
    action:
      - service: notify.notify
        data:
          title: "🌊 TSUNAMI WARNING ACTIVE"
          message: "Check your local emergency authorities immediately."
```

---

## Technical details

| Detail | Value |
|---|---|
| Data source | [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/) |
| API endpoint | `https://earthquake.usgs.gov/fdsnws/event/1/query` |
| Authentication | None — public free API |
| Update interval | 5 minutes |
| IoT class | `cloud_polling` |
| Minimum HA version | 2024.1.0 |
| External dependencies | None |

---

## Credits

Earthquake data provided by the [U.S. Geological Survey (USGS)](https://www.usgs.gov/) Earthquake Hazards Program.

---

<div align="center">

Made with ❤️ by [@janfajessen](https://github.com/janfajessen) · Data: [USGS](https://earthquake.usgs.gov/)

</div>
