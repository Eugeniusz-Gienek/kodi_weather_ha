import math
from datetime import datetime
from typing import Union

from lib.homeassistant import (
    HomeAssistantAdapter, RequestError, HomeAssistantForecast, HomeAssistantHourlyForecast, HomeAssistantDailyForecast,
    HomeAssistantWeatherCondition
)
from lib.kodi import (
    KodiHomeAssistantWeatherPluginAdapter, KodiAddonStrings, KodiLogLevel, KodiGeneralForecastData, KodiForecastData,
    KodiCurrentForecastData, KodiWindDirectionCode, KodiConditionCode, KodiHourlyForecastData, KodiDailyForecastData
)

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

    def _get_forecast_handling_errors(self) -> HomeAssistantForecast:
        try:
            return HomeAssistantAdapter.get_forecast(
                server_url=self._kodi_adapter.home_assistant_url,
                entity_id=self._kodi_adapter.home_assistant_entity,
                token=self._kodi_adapter.home_assistant_token
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
            ha_forecast: HomeAssistantHourlyForecast) -> KodiHourlyForecastData:
        return KodiHourlyForecastData(
            temperature=ha_forecast.temperature,  # TODO: Ensure °C
            wind_speed=ha_forecast.wind_speed,  # TODO: Ensure kph
            wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.wind_bearing),
            precipitation=int(ha_forecast.precipitation),
            humidity=ha_forecast.humidity,
            feels_like=KodiHomeAssistantWeatherPlugin.__calculate_feels_like(
                temperature_celsius=ha_forecast.temperature,
                wind_speed_kph=ha_forecast.wind_speed,
            ),  # TODO: Ensure °C, Ensure kph
            dew_point=KodiHomeAssistantWeatherPlugin.__calculate_dew_point(
                temperature_celsius=ha_forecast.temperature,
                humidity_percent=ha_forecast.humidity
            ),  # TODO: Ensure °C
            condition=KodiHomeAssistantWeatherPlugin.__translate_condition(
                ha_condition=ha_forecast.condition
            ),
            timestamp=datetime.fromisoformat(ha_forecast.datetime),
            pressure="",        # TODO: NoneType handling
        )

    @staticmethod
    def __translate_daily_ha_forecast_to_kodi_forecast(
            ha_forecast: HomeAssistantDailyForecast) -> KodiDailyForecastData:
        return KodiDailyForecastData(
            temperature=ha_forecast.temperature,  # TODO: Ensure °C
            wind_speed=ha_forecast.wind_speed,  # TODO: Ensure kph
            wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.wind_bearing),
            precipitation=int(ha_forecast.precipitation),
            condition=KodiHomeAssistantWeatherPlugin.__translate_condition(
                ha_condition=ha_forecast.condition
            ),
            timestamp=datetime.fromisoformat(ha_forecast.datetime),
            low_temperature=ha_forecast.templow  # TODO: Ensure °C
        )

    @staticmethod
    def __translate_ha_forecast_to_kodi_forecast(ha_forecast: HomeAssistantForecast) -> KodiForecastData:
        return KodiForecastData(
            General=KodiGeneralForecastData(
                location=ha_forecast.current.friendly_name
            ),
            Current=KodiCurrentForecastData(
                temperature=ha_forecast.current.temperature,  # TODO: Ensure °C
                wind_speed=ha_forecast.current.wind_speed,  # TODO: Ensure kph
                wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.current.wind_bearing),
                precipitation=0,   # TODO: NoneType handling
                condition=KodiHomeAssistantWeatherPlugin.__translate_condition(
                    ha_condition=ha_forecast.hourly[0].condition if len(ha_forecast.hourly) > 0 else None,
                ),
                humidity=ha_forecast.current.humidity,
                feels_like=KodiHomeAssistantWeatherPlugin.__calculate_feels_like(
                    temperature_celsius=ha_forecast.current.temperature,
                    wind_speed_kph=ha_forecast.current.wind_speed,
                ),  # TODO: Ensure °C, Ensure kph
                dew_point=KodiHomeAssistantWeatherPlugin.__calculate_dew_point(
                    temperature_celsius=ha_forecast.current.temperature,
                    humidity_percent=ha_forecast.current.humidity
                ),  # TODO: Ensure °C
                uv_index=int(ha_forecast.current.uv_index),
                cloudiness=int(ha_forecast.current.cloud_coverage),
            ),
            HourlyForecasts=[
                KodiHomeAssistantWeatherPlugin.__translate_hourly_ha_forecast_to_kodi_forecast(
                    ha_forecast=hourly_forecast
                )
                for hourly_forecast in ha_forecast.hourly
            ],
            DailyForecasts=[
                KodiHomeAssistantWeatherPlugin.__translate_daily_ha_forecast_to_kodi_forecast(
                    ha_forecast=daily_forecast
                )
                for daily_forecast in ha_forecast.daily
            ]
        )

    @staticmethod
    def __calculate_dew_point(temperature_celsius: float, humidity_percent: float) -> float:
        # obtain saturation vapor pressure (pressure at which water in air will condensate)
        vapor_pressure_sat = 6.11 * 10.0 ** (7.5 * temperature_celsius / (237.7 + temperature_celsius))
        # we set a minimum of .075 % to make the math defined
        humidity_percent = max(humidity_percent, 0.075)
        # calculate actual vapor pressure (water in air will condensate at approx. 100 % humidity), linear correlation
        vapor_pressure_act = (humidity_percent * vapor_pressure_sat) / 100
        # Now you are ready to use the following formula to obtain the dewpoint temperature.
        return (-430.22 + 237.7 * math.log(vapor_pressure_act)) / (-math.log(vapor_pressure_act) + 19.08)

    @staticmethod
    def __calculate_feels_like(temperature_celsius: float, wind_speed_kph: float) -> float:
        # Model: Wind Chill JAG/TI Environment Canada
        # see https://en.wikipedia.org/wiki/Wind_chill#North_American_and_United_Kingdom_wind_chill_index
        return (
                + 13.12
                + 0.6215 * temperature_celsius
                - 11.37 * wind_speed_kph ** 0.16
                + 0.3965 * temperature_celsius * wind_speed_kph ** 0.16
        )

    @staticmethod
    def __translate_condition(
            ha_condition: Union[HomeAssistantWeatherCondition, None]) -> Union[KodiConditionCode, None]:
        if ha_condition is None:
            return None
        elif ha_condition == HomeAssistantWeatherCondition.CLEAR_NIGHT.value:
            return KodiConditionCode.CLEAR_NIGHT
        elif ha_condition == HomeAssistantWeatherCondition.CLOUDY.value:
            return KodiConditionCode.CLOUDY
        elif ha_condition == HomeAssistantWeatherCondition.FOG.value:
            return KodiConditionCode.FOGGY
        elif ha_condition == HomeAssistantWeatherCondition.HAIL.value:
            return KodiConditionCode.HAIL
        elif ha_condition == HomeAssistantWeatherCondition.LIGHTNING.value:
            return KodiConditionCode.THUNDERSTORMS
        elif ha_condition == HomeAssistantWeatherCondition.LIGHTNING_RAINY.value:
            return KodiConditionCode.THUNDERSHOWERS
        elif ha_condition == HomeAssistantWeatherCondition.PARTLY_CLOUDY.value:
            return KodiConditionCode.PARTLY_CLOUDY
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

    def apply_forecast(self):
        forecast = self._get_forecast_handling_errors()
        if forecast is None:
            self._kodi_adapter.log(message="No forecasts were found.", level=KodiLogLevel.WARNING)
            self._kodi_adapter.clear_weather_properties()
            return
        kodi_forecast = KodiHomeAssistantWeatherPlugin.__translate_ha_forecast_to_kodi_forecast(
            ha_forecast=forecast
        )
        self._kodi_adapter.set_weather_properties(forecast=kodi_forecast)
        self._kodi_adapter.log(message="Weather updated successfully.", level=KodiLogLevel.INFO)
