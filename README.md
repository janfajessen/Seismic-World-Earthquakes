<div align="center">

# Seismic World Earthquakes
and Tsunamis
# Home Assistant Integration


<img src="brands/logo@2x.png" width="450"/>

![Version](https://img.shields.io/badge/version-1.5.24-blue?style=for-the-badge)
![HA](https://img.shields.io/badge/Home%20Assistant-2024.1+-orange?style=for-the-badge&logo=home-assistant)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python)
![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=white)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow?style=for-the-badge&logo=buymeacoffee)](https://www.buymeacoffee.com/janfajessen)
[![Patreon](https://img.shields.io/badge/Patreon-Support-red?style=for-the-badge&logo=patreon)](https://www.patreon.com/janfajessen)
<!--[![Ko-Fi](https://img.shields.io/badge/Ko--Fi-Support-teal?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/janfajessen)
[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-Support-pink?style=for-the-badge&logo=githubsponsors)](https://github.com/sponsors/janfajessen)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-blue?style=for-the-badge&logo=paypal)](https://paypal.me/janfajessen)-->

**The earthquake monitoring integration Home Assistant deserves.**

Real-time global seismic data · Interactive map setup · No API key · No YAML

[Installation](#installation) · [Configuration](#configuration) · [Entities](#entities) · [Automations](#automation-examples) · [Why this integration?](#why-this-integration)

</div>

---

## Why this integration?

Home Assistant ships with a built-in USGS earthquake integration. It works — but it was introduced in **HA 0.84**, is officially marked as **Legacy**, has not been actively developed for years, and currently counts only **~521 active installations** worldwide. It only creates map pins and nothing else. Configuration requires editing `configuration.yaml` by hand.

**Seismic World Earthquakes** was built from scratch to do the job properly.

| Feature | HA Built-in (Legacy) | Seismic World Earthquakes |
|---|:---:|:---:|
| UI config flow (no YAML) | ❌ | ✅ |
| Interactive map area selector | ❌ | ✅ |
| Multiple instances | ❌ | ✅ |
| Custom magnitude threshold | ❌ Predefined feeds only | ✅ 0.0 – 9.9 slider |
| Custom data period | ❌ Predefined feeds only | ✅ Hour / Day / Week / Month |
| Max events cap (intelligent) | ❌ | ✅ M ≥ 6.0 always kept |
| Summary sensors | ❌ 0 sensors | ✅ 13 sensors |
| Diagnostic sensors | ❌ | ✅ 4 sensors |
| Earthquake alert binary sensor | ❌ | ✅ Configurable magnitude + window |
| Tsunami warning binary sensor | ❌ | ✅ |
| ShakeMap intensity image | ❌ | ✅ |
| Calendar entity | ❌ | ✅ |
| Event entity (for automations) | ❌ | ✅ |
| Force refresh button | ❌ | ✅ |
| Device page (grouped entities) | ❌ | ✅ |
| Depth, status, alert filters | ❌ | ✅ |
| Sort by magnitude / time / distance | ❌ | ✅ |
| km / miles configurable | ❌ km only | ✅ |
| Multilingual UI | ❌ English only | ✅ |
| Active development | ❌ Legacy | ✅ |

---

## Features at a glance

- 🗺️ **Map pins** — one dynamic pin per earthquake, icon scales with magnitude
- 📊 **13 summary sensors** — strongest, average, nearest, latest, tsunami count, PAGER alert level, and more
- 🔔 **Configurable alert binary sensor** — set your own magnitude threshold and time window
- 🌊 **Tsunami binary sensor** — instantly know if any active event carries a tsunami flag
- 🖼️ **ShakeMap image entity** — USGS intensity map for the strongest current earthquake
- 📅 **Calendar** — every earthquake as a 1-hour calendar event with full details
- ⚡ **Event entity** — fire automations the moment a new earthquake is detected
- 🌍 **Global or custom area** — drag a pin on an interactive map, adjust the radius visually
- 🔄 **Multiple instances** — one for global M4.5+, one for your region M2.5+, one tsunami-only...
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

Setup happens entirely in the UI — no YAML needed. Three steps:

### Step 1 — Basic settings

| Option | Description | Default |
|---|---|---|
| Instance name | Friendly name for this instance | `Seismic World Earthquakes` |
| Instance type | Global (worldwide) or Custom area | Global |
| Minimum magnitude | Richter scale (0.0 – 9.9) | 4.5 |
| Data period | Last hour / 24 h / 7 days / 30 days | 24 h |
| Maximum events | Map pin cap (50 – 500) | 100 |
| Distance units | km or miles | km |
| Sort events by | Magnitude / Time / Distance | Magnitude |

> Events with **M ≥ 6.0 are always retained** regardless of the maximum events cap.

### Step 2 — Custom area *(custom area instances only)*

An **interactive map** lets you drag a pin to set the centre point and resize the radius circle visually. No typing coordinates. Minimum radius: 10 km.

### Step 3 — Filters & alert sensor

| Option | Description | Default |
|---|---|---|
| Minimum PAGER alert level | None / Green / Yellow / Orange / Red | None |
| Only tsunami events | Show only events with tsunami flag | Off |
| Maximum depth (km) | 0 – 700, set 700 for no limit | 700 |
| Only reviewed events | USGS quality filter (may add delay) | Off |
| Alert sensor — min magnitude | Threshold for the alert binary sensor | 5.0 |
| Alert sensor — time window | Hours to look back for the alert (1 – 72) | 24 |

All settings can be changed at any time from the ⚙️ **Reconfigure** button — no restart needed.

---

## Entities

### 📍 Geo-location — map pins

One pin per active earthquake on the HA map. State = distance to the reference point in the configured unit.

| Icon | Magnitude |
|---|---|
| `mdi:alert-circle` | M ≥ 7.0 |
| `mdi:alert` | M ≥ 6.0 |
| `mdi:alert-outline` | M ≥ 5.0 |
| `mdi:map-marker-alert` | M ≥ 4.0 |
| `mdi:map-marker-radius` | M ≥ 3.0 |
| `mdi:map-marker` | M < 3.0 |

Attributes per pin: magnitude, depth, place, time, alert level, tsunami flag, significance score, felt reports, MMI, network, USGS URL.

### 📊 Summary sensors

| Sensor | Description |
|---|---|
| Total earthquakes | Total events in the configured period |
| Strongest earthquake | Maximum magnitude |
| Strongest earthquake location | Place of the highest-magnitude event |
| Average magnitude | Mean across all displayed events |
| Latest earthquake | Title of the most recent event |
| Latest earthquake time | Timestamp of the most recent event |
| Earthquakes last hour | Count of events in the past 60 minutes |
| Significant earthquakes | Events with USGS significance score ≥ 600 |
| Active tsunami warnings | Count of events with tsunami flag |
| Highest alert level | Top PAGER alert in the current period |
| Red alert events | Count of RED PAGER alert events |
| Nearest earthquake distance | Distance to the closest event |
| Nearest earthquake magnitude | Magnitude of the closest event |

### 📊 Diagnostic sensors

| Sensor | Description |
|---|---|
| Last update | Timestamp of the last successful refresh |
| API status | `ok` or error description |
| Events fetched | Raw count from USGS API |
| Events displayed | Count after filters and cap |

### 🔔 Binary sensors

| Sensor | ON when... |
|---|---|
| Earthquake alert | Event ≥ configured magnitude within the time window |
| Tsunami warning active | Any current event carries a tsunami flag |

### 🖼️ ShakeMap image

USGS intensity map image for the strongest current earthquake.

> ⚠️ **USGS ShakeMaps exist only for earthquakes with magnitude ≥ 4.5.** Below this threshold the entity will be unavailable.

### 📅 Calendar

Every earthquake as a 1-hour event. Includes depth, alert level, significance, felt reports, and a direct link to the USGS event page.

### ⚡ Event entity — New earthquake detected

Fires `earthquake_detected` each time a new earthquake appears in the feed. Earthquakes present on the first load are skipped to avoid flooding automations on startup. New events fire in descending magnitude order.

Available attributes: `magnitude`, `place`, `time`, `latitude`, `longitude`, `depth_km`, `tsunami_warning`, `alert_level`, `significance`, `distance`, `url`, and more.

### 🔘 Force refresh button

Triggers an immediate data pull from USGS without waiting for the 5-minute cycle.

---

## Automation examples

### Alert for strong earthquakes

```yaml
automation:
  - alias: "Strong earthquake detected"
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
          title: "🌍 M{{ trigger.event.data.magnitude }} — {{ trigger.event.data.place }}"
          message: >
            Depth: {{ trigger.event.data.depth_km }} km
            {{ trigger.event.data.url }}
```

### Tsunami warning

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

### Map card

```yaml
type: map
geo_location_sources:
  - seismic_world_earthquakes
entities:
  - zone.home
title: Earthquakes
```

---

## Technical details

| | |
|---|---|
| Data source | [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/) |
| API | `https://earthquake.usgs.gov/fdsnws/event/1/query` |
| Authentication | None — public free API |
| Update interval | 5 minutes |
| IoT class | `cloud_polling` |
| Minimum HA version | 2024.1.0 |
| External dependencies | None |

---

## Credits

Earthquake data provided by the [U.S. Geological Survey (USGS)](https://www.usgs.gov/) Earthquake Hazards Program, a public domain data source.

---

<div align="center">

Made with ❤️ by [@janfajessen](https://github.com/janfajessen) · Data: [USGS](https://earthquake.usgs.gov/)

*If this integration is useful to you, consider giving it a ⭐ on GitHub.*
Or onsider supporting development!

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?style=for-the-badge)](https://www.buymeacoffee.com/janfajessen)
[![Patreon](https://img.shields.io/badge/Patreon-Support-red.svg?style=for-the-badge)](https://www.patreon.com/janfajessen)
</div>

