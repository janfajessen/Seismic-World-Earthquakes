<div align="center">

# Seismic World Earthquakes
and Tsunamis
# Home Assistant Integration


<img src="https://github.com/janfajessen/Seismic-World-Earthquakes---Home-Assistant/blob/c5ed7b9293d4c40c7f7a4e4975365c573db037a7/brand/logo%402x.png" width="450"/>


![Version](https://img.shields.io/badge/version-1.2.8-blue?style=for-the-badge)
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
- 🌐 **Multilingual** — +49 languages 

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

<img src="https://github.com/janfajessen/Seismic-World-Earthquakes---Home-Assistant/blob/c5ed7b9293d4c40c7f7a4e4975365c573db037a7/brand/icon%402x.png" width="100"/>


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
alias: Seismic Earthquake neer Home SEISMIC WORLD EARTHQUAKES Telegram
description: ""
triggers:
  - trigger: state
    entity_id:
      - >-
        sensor.seismos_y_terremotos_cerca_de_casa_distancia_al_terremoto_mas_cercano
conditions:
  - condition: template
    value_template: >
      {{ trigger.to_state.state | float > 0 and trigger.to_state.state !=
      'unknown' and trigger.to_state.state != 'unavailable' }}
  - condition: template
    value_template: >
      {{ trigger.from_state.state == 'unknown' or trigger.from_state.state ==
      'unavailable' or trigger.from_state.state | float == 0 }}
  - condition: template
    value_template: |
      {{ this.attributes.last_triggered is none or 
         (as_timestamp(now()) - as_timestamp(this.attributes.last_triggered)) > 300 }}
actions:
  - action: telegram_bot.send_message
    entity_id:
      - notify.telegram_jan
    data:
      message: >
        📈 EARTHQUAKE ⚠️⚠️ in 

        {{ 
        state_attr('sensor.seismos_y_terremotos_cerca_de_casa_distancia_al_terremoto_mas_cercano',
        'place') }} 


        at {{ states(
        'sensor.seismos_y_terremotos_cerca_de_casa_distancia_al_terremoto_mas_cercano'
        ) }} km de casa


        magnitude {{
        state_attr('sensor.seismos_y_terremotos_cerca_de_casa_distancia_al_terremoto_mas_cercano',
        'magnitude') }}


        📅 {{
        as_timestamp(state_attr('sensor.seismos_y_terremotos_cerca_de_casa_distancia_al_terremoto_mas_cercano',
        'time')) | timestamp_custom('%H:%M %d/%m/%y') }}
mode: single

```

### Tsunami warning automation

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
theme_mode: auto
```


### Last Earthquakes card excluding unknown & unavailable

```yaml
type: custom:auto-entities
card:
  type: entities
  title: Last Earthquakes
  show_header_toggle: false
filter:
  include:
    - entity_id: geo_location.seismic_world_earthquakes_*
    - entity_id: geo_location.seismos_y_terremotos_cerca_de_casa_*
  exclude:
    - state: unknown
    - state: unavailable
    - options: {}
      attributes:
        magnitude: null
options:
  type: custom:multiple-entity-row
  entity: this
  name: "{{ state_attr(config.entity, 'place') | default('Lugar desconocido') }}"
  secondary_info: |-
    🌊 Magnitud {{ state_attr(config.entity, 'magnitude') }} | 
    📍 Distancia: {{ state(config.entity) }}
  entities:
    - attribute: magnitude
      name: Magnitud
      hide_if: null

```

### Last Earthquakes markdown card

```yaml
type: markdown
content: >
  ## Last Earthquakes


  {% set terremotos = states.geo_location 
     | selectattr('entity_id', 'search', 'seismic_world_earthquakes_')
     | selectattr('state', 'ne', 'unknown')
     | selectattr('state', 'ne', 'unavailable')
     | list %}

  {% if terremotos | length == 0 %}

  ✅ No active Earthquakes at this moment.

  {% else %}

  {% for t in terremotos %}

  {% set magnitud = t.attributes.magnitude | float(0) %}

  {% set fecha_hora = as_timestamp(t.attributes.time) | timestamp_custom('%H:%M
  %d/%m/%y') if t.attributes.time else 'Fecha desconocida' %}

  {% set tsunami = ' 🌊 TSUNAMI WARNING' if t.attributes.tsunami_warning else ''
  %}

  *   **{{ t.attributes.place | default('Unknown location') }}**
      *   📈 Magnitude: **{{ magnitud }}**
      *   📍 Distance: **{{ t.state }}** from home
      *   🕐 Time/Date: **{{ fecha_hora }}**
      *   **{{ tsunami }}**
  {% endfor %}

  {% endif %}
```

---

## Technical details

| | |
|---|---|
| Data source | [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/) |
| API | `https://earthquake.usgs.gov/fdsnws/event/1/query` |
| Authentication | None — public free API |
| Update interval | 1-120 minutes, default 5 min |
| IoT class | `cloud_polling` |
| Minimum HA version | 2024.1.0 |
| External dependencies | None |

---

## Credits

Earthquake data provided by the [U.S. Geological Survey (USGS)](https://www.usgs.gov/) Earthquake Hazards Program, a public domain data source.

---

<div align="center">

<img src="https://github.com/janfajessen/Seismic-World-Earthquakes---Home-Assistant/blob/c5ed7b9293d4c40c7f7a4e4975365c573db037a7/brand/icon%402x.png" width="150"/>


Made with ❤️ by [@janfajessen](https://github.com/janfajessen) · Data: [USGS](https://earthquake.usgs.gov/)

*If this integration is useful to you, consider giving it a ⭐ on GitHub.*
Or consider supporting development ☺️💸

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?style=for-the-badge)](https://www.buymeacoffee.com/janfajessen)
[![Patreon](https://img.shields.io/badge/Patreon-Support-red.svg?style=for-the-badge)](https://www.patreon.com/janfajessen)
</div>


© [@janfajessen](https://github.com/janfajessen)

