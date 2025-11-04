# HA Narodmon Sender

Home Assistant integration that aggregates sensor data and sends to Narodmon.ru using MAC-based station ID.

## Features
- Per-group aggregation (min/max/average) sampled every 10 seconds
- Sliding-window average across upload interval (configurable)
- Supports many weather groups and custom sensors
- Persistent notifications for group failures; auto-dismiss on recovery
- Configurable upload interval, coordinates (LAT/LON/ALT), and station MAC

## Installation (manual)
1. Unzip package and copy `ha_narodmon_sender` folder into `/config/custom_components/`
2. Restart Home Assistant
3. Add integration: Settings → Devices & Services → Add Integration → HA Narodmon Sender

## Installation (HACS)
1. Add repo URL to HACS custom repositories: `https://github.com/Gmarapet/ha-narodmon-sender`
2. Category: Integration
3. Install and restart Home Assistant

## Configuration
- MAC address (station ID) — auto-generated but editable
- Latitude / Longitude / Elevation — from HA by default, editable
- Upload interval (seconds)
- For each supported group (TEMP, RH, PRESS, WS, DIR, LUX, RAD, CO, CO2, CH4, PPM, UV, PM, DP) choose one or more sensors and aggregation method (average/minimum/maximum)
- Add custom sensors with a user-defined identifier if needed

## Example JSON payload
```
{
  "ID": "AA:BB:CC:DD:EE:FF",
  "LAT": 55.7522,
  "LON": 37.6156,
  "ALT": 190,
  "TEMP": 22.3,
  "RH": 41,
  "PRESS": 1010.5,
  "WS": 3.2,
  "DIR": 270,
  "LUX": 860,
  "RAD": 0.11,
  "CO2": 415,
  "PM": 15,
  "DP": 14.5,
  "UPTIME": 48293,
  "BATCHARGE": 89
}
```

## Notes
- Only numeric sensor states are used.
- Sensors with `unknown`/`unavailable` are skipped.
- Group-level aggregation is computed per SAMPLE_INTERVAL and then the buffer of these aggregated readings is averaged across upload interval.
