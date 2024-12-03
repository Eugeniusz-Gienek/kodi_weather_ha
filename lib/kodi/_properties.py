from typing import List


class _NestedProperties:
    def __init__(self, prefix: str):
        self._prefix = prefix

    def __getattribute__(self, item: str):
        return object.__getattribute__(self, "_prefix") + object.__getattribute__(self, item)

    @property
    def values(self) -> List[str]:
        return [self.x for x in dir(self) if x.isupper()]


class _KodiGeneralWeatherProperties(_NestedProperties):
    LOCATION = "Location"
    CURRENT_LOCATION = "Current.Location"
    WEATHER_PROVIDER = "WeatherProvider"
    WEATHER_PROVIDER_LOGO = "WeatherProviderLogo"
    WEATHER_IS_FETCHED = "Weather.IsFetched"
    CURRENT_IS_FETCHED = "Current.IsFetched"
    HOURLY_IS_FETCHED = "Hourly.IsFetched"
    DAILY_IS_FETCHED = "Daily.IsFetched"


class _KodiCurrentWeatherProperties(_NestedProperties):
    CONDITION = "Condition"
    TEMPERATURE = "Temperature"
    WIND = "Wind"
    WIND_DIRECTION = "WindDirection"
    HUMIDITY = "Humidity"
    FEELS_LIKE = "FeelsLike"
    UV_INDEX = "UVIndex"
    DEW_POINT = "DewPoint"
    PRECIPITATION = "Precipitation"  # TODO: Is this available
    CLOUDINESS = "Cloudiness"  # TODO: Is this available
    OUTLOOK_ICON = "OutlookIcon"
    FANART_CODE = "FanartCode"


class _KodiHourlyWeatherProperties(_NestedProperties):
    TIME = "Time"
    LONG_DATE = "LongDate"
    SHORT_DATE = "ShortDate"
    OUTLOOK = "Outlook"
    OUTLOOK_ICON = "OutlookIcon"
    FANART_CODE = "FanartCode"
    WIND_SPEED = "WindSpeed"
    WIND_DIRECTION = "WindDirection"
    HUMIDITY = "Humidity"
    TEMPERATURE = "Temperature"
    DEW_POINT = "DewPoint"
    FEELS_LIKE = "FeelsLike"
    PRESSURE = "Pressure"
    PRECIPITATION = "Precipitation"


class _KodiDailyWeatherProperties(_NestedProperties):
    SHORT_DATE = "ShortDate"
    SHORT_DAY = "ShortDay"
    HIGH_TEMPERATURE = "HighTemperature"
    LOW_TEMPERATURE = "LowTemperature"
    OUTLOOK = "Outlook"
    OUTLOOK_ICON = "OutlookIcon"
    FANART_CODE = "FanartCode"
    WIND_SPEED = "WindSpeed"
    WIND_DIRECTION = "WindDirection"
    PRECIPITATION = "Precipitation"


class _KodiDailyWeatherPropertiesCompat(_NestedProperties):
    TITLE = "Title"
    HIGH_TEMP = "HighTemp"
    LOW_TEMP = "LowTemp"
    OUTLOOK = "Outlook"
    OUTLOOK_ICON = "OutlookIcon"
    FANART_CODE = "FanartCode"


class _KodiWeatherProperties:
    GENERAL = _KodiGeneralWeatherProperties("")
    CURRENT = _KodiCurrentWeatherProperties("Current.")

    HOURLY_1 = _KodiHourlyWeatherProperties("Hourly.1.")
    HOURLY_2 = _KodiHourlyWeatherProperties("Hourly.2.")
    HOURLY_3 = _KodiHourlyWeatherProperties("Hourly.3.")
    HOURLY_4 = _KodiHourlyWeatherProperties("Hourly.4.")
    HOURLY_5 = _KodiHourlyWeatherProperties("Hourly.5.")
    HOURLY_6 = _KodiHourlyWeatherProperties("Hourly.6.")
    HOURLY_7 = _KodiHourlyWeatherProperties("Hourly.7.")
    HOURLY_8 = _KodiHourlyWeatherProperties("Hourly.8.")
    HOURLY_9 = _KodiHourlyWeatherProperties("Hourly.9.")
    HOURLY_10 = _KodiHourlyWeatherProperties("Hourly.10.")
    HOURLY_11 = _KodiHourlyWeatherProperties("Hourly.11.")
    HOURLY_12 = _KodiHourlyWeatherProperties("Hourly.12.")
    HOURLY_13 = _KodiHourlyWeatherProperties("Hourly.13.")
    HOURLY_14 = _KodiHourlyWeatherProperties("Hourly.14.")
    HOURLY_15 = _KodiHourlyWeatherProperties("Hourly.15.")
    HOURLY_16 = _KodiHourlyWeatherProperties("Hourly.16.")
    HOURLY_17 = _KodiHourlyWeatherProperties("Hourly.17.")
    HOURLY_18 = _KodiHourlyWeatherProperties("Hourly.18.")
    HOURLY_19 = _KodiHourlyWeatherProperties("Hourly.19.")
    HOURLY_20 = _KodiHourlyWeatherProperties("Hourly.20.")
    HOURLY_21 = _KodiHourlyWeatherProperties("Hourly.21.")
    HOURLY_22 = _KodiHourlyWeatherProperties("Hourly.22.")
    HOURLY_23 = _KodiHourlyWeatherProperties("Hourly.23.")
    HOURLY_24 = _KodiHourlyWeatherProperties("Hourly.24.")

    DAILY_1 = _KodiDailyWeatherProperties("Daily.1.")
    DAILY_2 = _KodiDailyWeatherProperties("Daily.2.")
    DAILY_3 = _KodiDailyWeatherProperties("Daily.3.")
    DAILY_4 = _KodiDailyWeatherProperties("Daily.4.")
    DAILY_5 = _KodiDailyWeatherProperties("Daily.5.")
    DAILY_6 = _KodiDailyWeatherProperties("Daily.6.")
    DAILY_7 = _KodiDailyWeatherProperties("Daily.7.")

    DAY0 = _KodiDailyWeatherPropertiesCompat("Day0.")
    DAY1 = _KodiDailyWeatherPropertiesCompat("Day1.")
    DAY2 = _KodiDailyWeatherPropertiesCompat("Day2.")
    DAY3 = _KodiDailyWeatherPropertiesCompat("Day3.")
    DAY4 = _KodiDailyWeatherPropertiesCompat("Day4.")
    DAY5 = _KodiDailyWeatherPropertiesCompat("Day5.")
    DAY6 = _KodiDailyWeatherPropertiesCompat("Day6.")
