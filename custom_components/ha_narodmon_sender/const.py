"""Constants for HA Narodmon Sender integration."""

DOMAIN = "ha_narodmon_sender"

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_ALTITUDE = "altitude"
CONF_MAC_ADDRESS = "mac_address"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 360  # seconds (6 minutes)

# Список поддерживаемых типов сенсоров и их идентификаторов для narodmon.ru
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
    "latitude": "LAT",
    "longitude": "LON",
    "altitude": "ALT",
}

# Интервалы по умолчанию для проверки сенсоров и обновления данных
SENSOR_CHECK_INTERVAL = 60  # seconds
DEFAULT_LATITUDE = 0.0
DEFAULT_LONGITUDE = 0.0
DEFAULT_ALTITUDE = 0.0
