DOMAIN = "ha_narodmon_sender"

CONF_INTERVAL = "interval"
CONF_MAC = "mac_address"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_ELEVATION = "elevation"
CONF_GROUPS = "groups"
CONF_CUSTOM = "custom_sensors"

DEFAULT_INTERVAL = 300  # seconds (upload interval)
SAMPLE_INTERVAL = 10    # seconds (how often to sample & compute group aggregate)
MAX_BUFFER_MULTIPLIER = 3  # keep buffers reasonably bounded

API_BASE = "https://narodmon.ru/post"

SUPPORTED_GROUPS = {
    "temperature": "TEMP",
    "humidity": "RH",
    "pressure": "PRESS",
    "wind_speed": "WS",
    "wind_dir": "DIR",
    "lux": "LUX",
    "radiation": "RAD",
    "co": "CO",
    "co2": "CO2",
    "ch4": "CH4",
    "ppm": "PPM",
    "uv": "UV",
    "pm": "PM",
    "dew_point": "DP"
}

AGGREGATION_MODES = ["average", "minimum", "maximum"]
