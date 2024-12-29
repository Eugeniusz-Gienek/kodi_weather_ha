import math
from datetime import datetime
from typing import Union, Tuple

from lib.homeassistant import (
    HomeAssistantAdapter, RequestError, HomeAssistantForecast, HomeAssistantHourlyForecast, HomeAssistantDailyForecast,
    HomeAssistantWeatherCondition, HomeAssistantForecastMeta, HomeAssistantSunInfo
)
from lib.kodi import (
    KodiHomeAssistantWeatherPluginAdapter, KodiAddonStrings, KodiLogLevel, KodiGeneralForecastData, KodiForecastData,
    KodiCurrentForecastData, KodiWindDirectionCode, KodiConditionCode, KodiHourlyForecastData, KodiDailyForecastData
)
from lib.unit.speed import SpeedKph, SpeedUnits, Speed
from lib.unit.temperature import TemperatureUnits, TemperatureCelsius, Temperature

# get settings...
MAX_REQUEST_RETRIES = 6
RETRY_DELAY_S = 10


class KodiHomeAssistantWeatherPlugin:
    def __init__(self):
        self._kodi_adapter = KodiHomeAssistantWeatherPluginAdapter()
        self._kodi_adapter.log("Home Assistant Weather started.")

        if not self._kodi_adapter.required_settings_done:
            self._kodi_adapter.dialog(message_id=KodiAddonStrings.SETTINGS_REQUIRED)
            self._kodi_adapter.log("Settings for Home Assistant Weather not yet provided. Plugin will not work.")
        else:
            self.apply_forecast()
        self._kodi_adapter.log("Home Assistant Weather init finished.")

    def _get_forecast_handling_errors(self) -> Tuple[HomeAssistantForecast, HomeAssistantSunInfo]:
        try:
            return (
                HomeAssistantAdapter.get_forecast(
                    server_url=self._kodi_adapter.home_assistant_url,
                    entity_id=self._kodi_adapter.home_assistant_entity_forecast,
                    token=self._kodi_adapter.home_assistant_token
                ),
                HomeAssistantAdapter.get_sun_info(
                    server_url=self._kodi_adapter.home_assistant_url,
                    entity_id=self._kodi_adapter.home_assistant_entity_sun,
                    token=self._kodi_adapter.home_assistant_token
                )
            )
        except RequestError as e:
            self._kodi_adapter.log(
                message=f"Could not retrieve forecast from Home Assistant: {e.error_code}", level=KodiLogLevel.ERROR
            )
            if e.error_code == 401:
                message = KodiAddonStrings.HOMEASSISTANT_UNAUTHORIZED
            elif e.error_code == -1:
                message = KodiAddonStrings.HOMEASSISTANT_UNREACHABLE
            else:
                message = KodiAddonStrings.HOMEASSISTANT_UNEXPECTED_RESPONSE
            self._kodi_adapter.dialog(message_id=message)

    @staticmethod
    def __translate_hourly_ha_forecast_to_kodi_forecast(
            ha_forecast: HomeAssistantHourlyForecast, forecast_meta: HomeAssistantForecastMeta,
            sunset: datetime, sunrise: datetime
    ) -> KodiHourlyForecastData:
        temperature = TemperatureUnits[forecast_meta.temperature_unit](ha_forecast.temperature)
        wind_speed = SpeedUnits[forecast_meta.wind_speed_unit](ha_forecast.wind_speed)
        timestamp = KodiHomeAssistantWeatherPlugin.__parse_homeassistant_datetime(datetime_str=ha_forecast.datetime)
        return KodiHourlyForecastData(
            temperature=temperature,
            wind_speed=wind_speed,
            wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.wind_bearing),
            precipitation=KodiHomeAssistantWeatherPlugin.__format_precipitation(
                precipitation=ha_forecast.precipitation, precipitation_unit=forecast_meta.precipitation_unit
            ),
            humidity=ha_forecast.humidity,
            feels_like=KodiHomeAssistantWeatherPlugin.__calculate_feels_like(
                temperature=temperature,
                wind_speed=wind_speed
            ),
            dew_point=KodiHomeAssistantWeatherPlugin.__calculate_dew_point(
                temperature=temperature,
                humidity_percent=ha_forecast.humidity
            ),
            condition=KodiHomeAssistantWeatherPlugin.__translate_condition(
                ha_condition=ha_forecast.condition, is_night=not (sunrise.time() < timestamp.time() < sunset.time())
            ),
            timestamp=timestamp,
            pressure="",
        )

    @staticmethod
    def __translate_daily_ha_forecast_to_kodi_forecast(
            ha_forecast: HomeAssistantDailyForecast, forecast_meta: HomeAssistantForecastMeta) -> KodiDailyForecastData:
        temperature = TemperatureUnits[forecast_meta.temperature_unit](ha_forecast.temperature)
        low_temperature = TemperatureUnits[forecast_meta.temperature_unit](ha_forecast.templow)
        wind_speed = SpeedUnits[forecast_meta.wind_speed_unit](ha_forecast.wind_speed)
        return KodiDailyForecastData(
            temperature=temperature,
            wind_speed=wind_speed,
            wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.wind_bearing),
            precipitation=KodiHomeAssistantWeatherPlugin.__format_precipitation(
                precipitation=ha_forecast.precipitation, precipitation_unit=forecast_meta.precipitation_unit
            ),
            condition=KodiHomeAssistantWeatherPlugin.__translate_condition(ha_condition=ha_forecast.condition),
            timestamp=KodiHomeAssistantWeatherPlugin.__parse_homeassistant_datetime(datetime_str=ha_forecast.datetime),
            low_temperature=low_temperature,
        )

    def __translate_ha_forecast_to_kodi_forecast(
            self, ha_forecast: HomeAssistantForecast, ha_sun_info: HomeAssistantSunInfo) -> KodiForecastData:
        temperature = TemperatureUnits[ha_forecast.current.temperature_unit](ha_forecast.current.temperature)
        wind_speed = SpeedUnits[ha_forecast.current.wind_speed_unit](ha_forecast.current.wind_speed)
        sunrise = KodiHomeAssistantWeatherPlugin.__parse_homeassistant_datetime(ha_sun_info.next_rising)
        sunset = KodiHomeAssistantWeatherPlugin.__parse_homeassistant_datetime(ha_sun_info.next_setting)
        return KodiForecastData(
            General=KodiGeneralForecastData(
                location=ha_forecast.current.friendly_name
            ),
            Current=KodiCurrentForecastData(
                temperature=temperature,
                wind_speed=wind_speed,
                wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.current.wind_bearing),
                precipitation=KodiHomeAssistantWeatherPlugin.__format_precipitation(
                    precipitation=ha_forecast.hourly[0].precipitation if len(ha_forecast.hourly) > 0 else None,
                    precipitation_unit=ha_forecast.current.precipitation_unit
                ),                                              # conversion not implemented in Kodi
                condition=KodiHomeAssistantWeatherPlugin.__translate_condition(
                    ha_condition=ha_forecast.hourly[0].condition if len(ha_forecast.hourly) > 0 else None,
                    is_night=not (sunrise.time() < datetime.now().time() < sunset.time())
                ),
                humidity=ha_forecast.current.humidity,
                feels_like=KodiHomeAssistantWeatherPlugin.__calculate_feels_like(
                    temperature=temperature,
                    wind_speed=wind_speed,
                ),
                dew_point=KodiHomeAssistantWeatherPlugin.__calculate_dew_point(
                    temperature=temperature,
                    humidity_percent=ha_forecast.current.humidity
                ),
                uv_index=int(ha_forecast.current.uv_index),
                cloudiness=int(ha_forecast.current.cloud_coverage),
                pressure=KodiHomeAssistantWeatherPlugin.__format_pressure(
                    pressure=ha_forecast.current.pressure, pressure_unit=ha_forecast.current.pressure_unit
                ),
                sunrise=sunrise,
                sunset=sunset,
            ),
            HourlyForecasts=[
                self.__translate_hourly_ha_forecast_to_kodi_forecast(
                    ha_forecast=hourly_forecast,
                    forecast_meta=ha_forecast.current,
                    sunrise=sunrise,
                    sunset=sunset,
                )
                for hourly_forecast in ha_forecast.hourly
            ],
            DailyForecasts=[
                self.__translate_daily_ha_forecast_to_kodi_forecast(
                    ha_forecast=daily_forecast,
                    forecast_meta=ha_forecast.current
                )
                for daily_forecast in ha_forecast.daily
            ]
        )

    @staticmethod
    def __calculate_dew_point(temperature: Temperature, humidity_percent: float) -> TemperatureCelsius:
        temperature_celsius = TemperatureCelsius.from_si_value(temperature.si_value())
        # obtain saturation vapor pressure (pressure at which water in air will condensate)
        vapor_pressure_sat = 6.11 * 10.0 ** (7.5 * temperature_celsius.value / (237.7 + temperature_celsius.value))
        # we set a minimum of .075 % to make the math defined
        humidity_percent = max(humidity_percent, 0.075)
        # calculate actual vapor pressure (water in air will condensate at approx. 100 % humidity), linear correlation
        vapor_pressure_act = (humidity_percent * vapor_pressure_sat) / 100
        # Now you are ready to use the following formula to obtain the dewpoint temperature.
        return TemperatureCelsius(
            (-430.22 + 237.7 * math.log(vapor_pressure_act)) / (-math.log(vapor_pressure_act) + 19.08)
        )

    @staticmethod
    def __calculate_feels_like(temperature: Temperature, wind_speed: Speed) -> TemperatureCelsius:
        temperature_celsius = TemperatureCelsius.from_si_value(temperature.si_value())
        wind_speed_kph = SpeedKph.from_si_value(wind_speed.si_value())
        # Model: Wind Chill JAG/TI Environment Canada
        # see https://en.wikipedia.org/wiki/Wind_chill#North_American_and_United_Kingdom_wind_chill_index
        return TemperatureCelsius(
                + 13.12
                + 0.6215 * temperature_celsius.value
                - 11.37 * wind_speed_kph.value ** 0.16
                + 0.3965 * temperature_celsius.value * wind_speed_kph.value ** 0.16
        )

    @staticmethod
    def __translate_condition(
            ha_condition: Union[HomeAssistantWeatherCondition, None], is_night: bool = False
    ) -> Union[KodiConditionCode, None]:
        if ha_condition is None:
            return None
        elif ha_condition == HomeAssistantWeatherCondition.CLEAR_NIGHT.value:
            return KodiConditionCode.CLEAR_NIGHT
        elif ha_condition == HomeAssistantWeatherCondition.CLOUDY.value:
            return KodiConditionCode.CLOUDY if not is_night else KodiConditionCode.MOSTLY_CLOUDY_NIGHT
        elif ha_condition == HomeAssistantWeatherCondition.FOG.value:
            return KodiConditionCode.FOGGY
        elif ha_condition == HomeAssistantWeatherCondition.HAIL.value:
            return KodiConditionCode.HAIL
        elif ha_condition == HomeAssistantWeatherCondition.LIGHTNING.value:
            return KodiConditionCode.THUNDERSTORMS
        elif ha_condition == HomeAssistantWeatherCondition.LIGHTNING_RAINY.value:
            return KodiConditionCode.THUNDERSHOWERS
        elif ha_condition == HomeAssistantWeatherCondition.PARTLY_CLOUDY.value:
            return KodiConditionCode.PARTLY_CLOUDY if not is_night else KodiConditionCode.PARTLY_CLOUDY_NIGHT
        elif ha_condition == HomeAssistantWeatherCondition.POURING.value:
            return KodiConditionCode.SHOWERS_2
        elif ha_condition == HomeAssistantWeatherCondition.RAINY.value:
            return KodiConditionCode.SHOWERS
        elif ha_condition == HomeAssistantWeatherCondition.SNOWY.value:
            return KodiConditionCode.SNOW
        elif ha_condition == HomeAssistantWeatherCondition.SNOWY_RAINY.value:
            return KodiConditionCode.MIXED_RAIN_AND_SNOW
        elif ha_condition == HomeAssistantWeatherCondition.SUNNY.value:
            return KodiConditionCode.SUNNY
        elif ha_condition == HomeAssistantWeatherCondition.WINDY.value:
            return KodiConditionCode.WINDY
        elif ha_condition == HomeAssistantWeatherCondition.WINDY_CLOUDY.value:
            return KodiConditionCode.WINDY
        elif ha_condition == HomeAssistantWeatherCondition.EXCEPTIONAL.value:
            return KodiConditionCode.SEVERE_THUNDERSTORMS
        else:
            raise ValueError(f"Unknown condition: {ha_condition}")

    @staticmethod
    def __format_precipitation(precipitation: Union[float, None], precipitation_unit: str) -> Union[str, None]:
        if precipitation is None:
            return None
        # scientific rounding to 0 or 1 significant decimal
        if precipitation > 3:
            fmt = "{:.0f} {}"
        else:
            fmt = "{:.1f} {}"
        return fmt.format(precipitation, precipitation_unit)

    @staticmethod
    def __format_pressure(pressure: Union[float, None], pressure_unit: str) -> str:
        if pressure is None:
            return ""
        return "{:.0f} {}".format(pressure, pressure_unit)

    @staticmethod
    def __parse_homeassistant_datetime(datetime_str: str) -> datetime:
        # tz=None adds time offset to match Kodi's set time
        return datetime.fromisoformat(datetime_str).astimezone(tz=None)

    def apply_forecast(self):
        forecast, sun_info = self._get_forecast_handling_errors()
        if forecast is None:
            self._kodi_adapter.log(message="No forecasts were found.", level=KodiLogLevel.WARNING)
            self._kodi_adapter.clear_weather_properties()
            return
        if sun_info is None:
            self._kodi_adapter.log(message="No sun info was found.", level=KodiLogLevel.WARNING)
            self._kodi_adapter.clear_weather_properties()
            return
        kodi_forecast = self.__translate_ha_forecast_to_kodi_forecast(
            ha_forecast=forecast,
            ha_sun_info=sun_info,
        )
        self._kodi_adapter.set_weather_properties(forecast=kodi_forecast)
        self._kodi_adapter.log(message="Weather updated successfully.", level=KodiLogLevel.INFO)
