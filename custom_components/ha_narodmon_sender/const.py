"""Constants for HA Narodmon Sender integration."""

DOMAIN = "ha_narodmon_sender"

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_ALTITUDE = "altitude"
CONF_MAC_ADDRESS = "mac_address"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 360  # seconds (6 minutes)

# Supported high-level sensor groups and their narodmon identifiers
SUPPORTED_SENSOR_TYPES = {
    "temperature": "TEMP",
    "humidity": "RH",
    "pressure": "PRESS",
    "wind_speed": "WS",
    "wind_dir": "DIR",
    "illuminance": "LUX",
    "radiation": "RAD",
    "co": "CO",
    "co2": "CO2",
    "ch4": "CH4",
    "ppm": "PPM",
    "uv": "UV",
    "pm": "PM",
    "dew_point": "DP",
    # coordinates / altitude
    "latitude": "LAT",
    "longitude": "LON",
    "altitude": "ALT",
}

# For UI selection: aggregation options
AGGREGATION_MODES = ["minimum", "maximum", "average"]

# Minimal mapping heuristics for filtering sensors by "type".
# We will check sensor.state_attributes.get("device_class") first,
# then try to guess by unit_of_measurement if device_class is absent.
# Keys below are candidate "device_class" strings or unit substrings.
SENSOR_TYPE_MATCH = {
    "temperature": {"device_class": ["temperature"], "unit_substr": ["°C", "C", "F"]},
    "humidity": {"device_class": ["humidity"], "unit_substr": ["%"]},
    "pressure": {"device_class": ["pressure"], "unit_substr": ["hPa", "Pa", "bar"]},
    "wind_speed": {"device_class": ["speed"], "unit_substr": ["m/s", "km/h", "kph", "mph"]},
    "illuminance": {"device_class": ["illuminance"], "unit_substr": ["lx", "lm"]},
    "radiation": {"device_class": ["radiation"], "unit_substr": []},
    "co2": {"device_class": ["carbon_dioxide", "co2"], "unit_substr": ["ppm"]},
    "pm": {"device_class": ["pm25", "pm10"], "unit_substr": ["µg/m3", "ug/m3"]},
    "uv": {"device_class": ["uv_index"], "unit_substr": []},
    # fallback for custom: allow any sensor
    "custom": {"device_class": [], "unit_substr": []},
}

# UI defaults
DEFAULT_LATITUDE = 0.0
DEFAULT_LONGITUDE = 0.0
DEFAULT_ALTITUDE = 0.0
