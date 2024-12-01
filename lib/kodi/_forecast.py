from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import List


class KodiConditionCode(IntEnum):
    TORNADO = 0
    TROPICAL_STORM = 1
    HURRICANE = 2
    SEVERE_THUNDERSTORMS = 3
    THUNDERSTORMS = 4
    MIXED_RAIN_AND_SNOW = 5
    MIXED_RAIN_AND_SLEET = 6
    MIXED_SNOW_AND_SLEET = 7
    FREEZING_DRIZZLE = 8
    DRIZZLE = 9
    FREEZING_RAIN = 10
    SHOWERS = 11
    SHOWERS_2 = 12
    SNOW_FLURRIES = 13
    LIGHT_SNOW_SHOWERS = 14
    BLOWING_SNOW = 15
    SNOW = 16
    HAIL = 17
    SLEET = 18
    DUST = 19
    FOGGY = 20
    HAZE = 21
    SMOKY = 22
    BLUSTERY = 23
    WINDY = 24
    COLD = 25
    CLOUDY = 26
    MOSTLY_CLOUDY_NIGHT = 27
    MOSTLY_CLOUDY = 28
    PARTLY_CLOUDY_NIGHT = 29
    PARTLY_CLOUDY = 30
    CLEAR_NIGHT = 31
    SUNNY = 32
    FAIR_NIGHT = 33
    FAIR_DAY = 34
    MIXED_RAIN_AND_HAIL = 35
    HOT = 36
    ISOLATED_THUNDERSTORMS = 37
    SCATTERED_THUNDERSTORMS = 38
    SCATTERED_THUNDERSTORMS_2 = 39
    SCATTERED_SHOWERS = 40
    HEAVY_SNOW = 41
    SCATTERED_SNOW_SHOWERS = 42
    HEAVY_SNOW_2 = 43
    PARTLY_CLOUDY_2 = 44
    THUNDERSHOWERS = 45
    SNOW_SHOWERS = 46
    ISOLATED_THUNDERSHOWERS = 47

    def __str__(self):
        return self.name.lower().replace('_', ' ')


@dataclass
class _KodiForecastCommon:
    temperature: float              # unit: °C
    wind_speed: float               # unit: kph
    wind_direction: str             # eg: NNE
    precipitation: int              # unit: %
    condition: KodiConditionCode


@dataclass
class _KodiDetailedForecastCommon:
    humidity: float     # unit: %
    feels_like: float   # unit: °C
    dew_point: float    # unit: °C


@dataclass
class _KodiConditionedForecastCommon:
    condition: KodiConditionCode

    @property
    def condition_str(self) -> str:
        return str(self.condition)

    @property
    def fanart_code(self) -> int:
        return self.condition.value

    def outlook_icon(self) -> str:
        return f"{self.condition.value}.png"


@dataclass
class _KodiFutureForecastCommon:
    timestamp: datetime


@dataclass
class KodiCurrentForecastData(_KodiForecastCommon, _KodiDetailedForecastCommon, _KodiConditionedForecastCommon):
    uv_index: int
    cloudiness: int     # unit: %


@dataclass
class KodiHourlyForecastData(
    _KodiForecastCommon, _KodiDetailedForecastCommon, _KodiConditionedForecastCommon, _KodiFutureForecastCommon
):
    pressure: str       # with unit


@dataclass
class KodiDailyForecastData(_KodiForecastCommon, _KodiConditionedForecastCommon, _KodiFutureForecastCommon):
    low_temperature: float  # unit: °C


@dataclass
class KodiForecastData:
    Current: KodiCurrentForecastData
    HourlyForecasts: List[KodiHourlyForecastData]
    DailyForecasts: List[KodiDailyForecastData]
