from dataclasses import dataclass
from typing import List, Union


@dataclass
class _HomeAssistantForecastCommon:
    wind_bearing: float
    wind_speed: float
    temperature: float
    humidity: float
    uv_index: float


@dataclass
class _HomeAssistantForecastMeta:
    temperature_unit: str
    pressure_unit: str
    wind_speed_unit: str
    visibility_unit: str
    precipitation_unit: str
    attribution: str
    friendly_name: str
    supported_features: int


@dataclass
class _HomeAssistantFutureForecast:
    condition: str
    datetime: str
    precipitation: float


@dataclass
class _HomeAssistantCurrentForecast(_HomeAssistantForecastCommon, _HomeAssistantForecastMeta):
    dew_point: float
    cloud_coverage: float
    pressure: float


@dataclass
class _HomeAssistantHourlyForecast(_HomeAssistantForecastCommon, _HomeAssistantFutureForecast):
    cloud_coverage: float


@dataclass
class _HomeAssistantDailyForecast(_HomeAssistantForecastCommon, _HomeAssistantFutureForecast):
    templow: float
    uv_index: Union[float, None] = None


@dataclass
class HomeAssistantForecast:
    current: _HomeAssistantCurrentForecast
    hourly: List[_HomeAssistantHourlyForecast]
    daily: List[_HomeAssistantDailyForecast]
