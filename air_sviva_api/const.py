"""Constants for the Sviva Air API wrapper."""

# Base URLs
BASE_URL = "https://air-papi.sviva.gov.il/v1/envista/"
MAIN_URL = "https://air.sviva.gov.il/"

# Base headers for all requests
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en,he;q=0.9",
    "origin": MAIN_URL.rstrip("/"),
    "referer": MAIN_URL,
    "domainname": "sviva",
    "envi-data-source": "MANA",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Auth endpoints
GET_API_TOKEN_URL = "https://air.sviva.gov.il/Account/GetApiToken"
GENERATE_TOKEN_URL = "https://air-papi.sviva.gov.il/v1/GenerateToken"

# Envista API endpoints (relative to BASE_URL)
GET_LUT_MNG_URL = "lut/mng"
GET_REGIONS_URL = "regions"
GET_REGIONS_LATEST_DATA_URL = "regions/data/latest"
GET_STATIONS_LATEST_INDEX_URL = "stations/index/latest"
GET_STATION_AVERAGE_URL = "stations/{station_id}/Average"  # + optional "/{channel_id}"
GET_STATION_DATA_AVERAGE_URL = "stations/{station_id}/data/average"
GET_STATION_INDEX_FAST_URL = "stations/{station_id}/indexFastSrv"
GET_STATION_MISSING_DAYS_URL = "stations/{station_id}/data/missing/days"
GET_POLLUTANTS_URL = "pollutants"
GET_DATA_UNITS_URL = "data/units"
GET_DATA_STATUS_URL = "data/status"
GET_MANUAL_STATIONS_URL = "manual/stations"
GET_MANUAL_POLLUTANTS_URL = "manual/pollutants"
GET_CONFIG_INDEX_URL = "config/index"
GET_INDEX_CONFIGURATION_URL = "index/configuration"
GET_STATION_TERMINOLOGY_URL = "StationTerminology/GetStationTerminology"
GET_LAYER_MNG_URL = "Layer/mng/sviva"
GET_LAYER_QUERIES_URL = "layer/{layer_id}/queries"
GET_LAYER_FILTERED_STATIONS_URL = "layer/{layer_id}/queries/filteredStations"
GET_INDEX_POLLUTANTS_URL = "factors/indexPollutants"
GET_THRESHOLDS_URL = "Pollutants/Threshold/get-all-threshold"
GET_WIDGET_URL = "widget/sviva"
GET_GUEST_MAP_VIEW_URL = "user/MapView/Guest"
GET_INTERPOLATION_MNG_URL = "interpolation/mng"
GET_ADVISORIES_URL = "Advisory"
GET_VINEYARD_LOCATION_URL = "vineyard/location/{location_id}"

# Server time endpoint (on main domain)
GET_SERVER_TIME_URL = MAIN_URL + "ajax/GetAPITime"

# Dashboard endpoints (on main domain)
GET_STATION_IMAGES_URL = MAIN_URL + "Dashboard/GetStationImages"

# Default values
DEFAULT_TIMEOUT = 30
DEFAULT_HOURS_BACK = 24
DEFAULT_REGION_HOURS_BACK = 4
DEFAULT_MISSING_DAYS_BACK = 180

# Sentinel value indicating no data / invalid reading
INVALID_VALUE = -9999
