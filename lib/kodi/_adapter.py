import os.path
from datetime import datetime, UTC
from typing import Type, Union

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from ._forecast import KodiForecastData, KodiHourlyForecastData, KodiDailyForecastData
from ._properties import _KodiWeatherProperties, _KodiHourlyWeatherProperties, _KodiDailyWeatherProperties, \
    _KodiDailyWeatherPropertiesCompat
from ._settings import _HomeAssistantWeatherPluginSetting, _Setting_Type, _HomeAssistantWeatherPluginSettings
from ._values import _KodiMagicValues, KodiLogLevel, KodiAddonStrings
from ..unit.speed import Speed, SpeedUnits, SpeedKph
from ..unit.temperature import Temperature, TemperatureUnits, TemperatureCelsius


class KodiHomeAssistantWeatherPluginAdapter:

    def __init__(self) -> None:
        self._window = xbmcgui.Window(_KodiMagicValues.WEATHER_WINDOW_ID)   # kwargs unsupported
        self._kodi_addon = xbmcaddon.Addon()
        self.__addon_id = self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_ADDON_ID)

    @property
    def cwd(self) -> str:
        return self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_PATH_ID)

    @property
    def temperature_unit(self) -> Type[Temperature]:
        return TemperatureUnits[xbmc.getRegion(id=_KodiMagicValues.REGION_TEMPERATURE_UNIT_ID)]

    @property
    def wind_speed_unit(self) -> Type[Speed]:
        return SpeedUnits[xbmc.getRegion(id=_KodiMagicValues.REGION_WIND_SPEED_UNIT_ID)]

    def _get_localized_string(self, id: int):
        return self._kodi_addon.getLocalizedString(id=id) or xbmc.getLocalizedString(id=id)

    def _get_setting(self, setting: _HomeAssistantWeatherPluginSetting) -> _Setting_Type:
        if setting.setting_type == bool:
            return self._kodi_addon.getSettingBool(id=setting.setting_id)
        elif setting.setting_type == int:
            return self._kodi_addon.getSettingInt(id=setting.setting_id)
        elif setting.setting_type == float:
            return self._kodi_addon.getSettingNumber(id=setting.setting_id)
        elif setting.setting_type == str:
            return self._kodi_addon.getSettingString(id=setting.setting_id)
        else:
            return self._kodi_addon.getSetting(id=setting.setting_id)

    @property
    def home_assistant_url(self) -> str:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_SERVER)

    @property
    def home_assistant_entity(self) -> str:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_WEATHER_FORECAST_ENTITY_ID)

    @property
    def home_assistant_token(self) -> str:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_TOKEN)

    def log(self, message: str, level: KodiLogLevel = KodiLogLevel.DEBUG):
        if self._get_setting(setting=_HomeAssistantWeatherPluginSettings.LOG_ENABLED):
            msg = f"[ HOME ASSISTANT WEATHER ]: {self.__addon_id}: {message}"
            xbmc.log(msg=msg, level=level.value)

    @property
    def required_settings_done(self) -> bool:
        return bool(self.home_assistant_token) and bool(self.home_assistant_url) and bool(self.home_assistant_entity)

    def dialog(self, message_id: KodiAddonStrings) -> bool:
        return xbmcgui.Dialog().ok(
            heading=self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_NAME_ID),
            message=self._get_localized_string(id=message_id)
        )
    
    def _set_window_property(self, key: str, value: str) -> None:
        self._window.setProperty(
            key=key,
            value=value
        )
        self.log(message=f"{key} := {value}", level=KodiLogLevel.DEBUG)

    def clear_weather_properties(self) -> None:
        for property_set in _KodiWeatherProperties.all():
            for key in property_set.values:
                self._set_window_property(key=key, value="")

    @staticmethod
    def format_unit(unit: Union[Temperature, Speed], value_format: str = "{:.0f}") -> str:
        return (value_format + " {}").format(unit.value, unit.unit)

    def set_weather_properties(self, forecast: KodiForecastData) -> None:
        # TODO: Sunrise, Sunset (Aeon Nox)
        # TODO: Fanart icon partly-cloudy at night
        # TODO: Format dates and times as per Kodi's locale
        percent = "{:.0f} %".format
        true = "true"
        self._set_window_property(key=_KodiWeatherProperties.GENERAL.LOCATION_1, value=forecast.General.location)
        self._set_window_property(key=_KodiWeatherProperties.GENERAL.LOCATIONS, value="1")
        # current
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.CONDITION,
            value=forecast.Current.condition_str
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.TEMPERATURE,
            value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                TemperatureCelsius.from_si_value(forecast.Current.temperature.si_value())
            )   # converted by Kodi from °C
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.UV_INDEX,
            value=str(forecast.Current.uv_index)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.OUTLOOK_ICON,
            value=forecast.Current.outlook_icon
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.FANART_CODE,
            value=str(forecast.Current.fanart_code)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.WIND,
            value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                SpeedKph.from_si_value(forecast.Current.wind_speed.si_value())
            )   # converted by Kodi from km/h
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.WIND_DIRECTION,
            value=self._get_localized_string(id=forecast.Current.wind_direction.value)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.HUMIDITY,
            value=str(forecast.Current.humidity)    # % is added by Kodi
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.DEW_POINT,
            value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                TemperatureCelsius.from_si_value(forecast.Current.dew_point.si_value())
            )     # converted by Kodi from °C
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.FEELS_LIKE,
            value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                TemperatureCelsius.from_si_value(forecast.Current.feels_like.si_value())
            )   # converted by Kodi from °C
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.WIND_CHILL,
            value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                self.temperature_unit.from_si_value(forecast.Current.feels_like.si_value())
            )
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.PRECIPITATION,
            value=forecast.Current.precipitation
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.CLOUDINESS,
            value=percent(forecast.Current.cloudiness)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.PRESSURE,
            value=forecast.Current.pressure
        )

        # hourly
        for hourly_forecast, hourly_properties in zip(
                forecast.HourlyForecasts,
                _KodiWeatherProperties.hourlies()
        ):
            hourly_forecast: KodiHourlyForecastData
            hourly_properties: _KodiHourlyWeatherProperties
            self._set_window_property(
                key=hourly_properties.TIME,
                value=hourly_forecast.timestamp.strftime("%H:%M")
            )
            self._set_window_property(
                key=hourly_properties.LONG_DATE,
                value=hourly_forecast.timestamp.strftime("%Y-%m-%d")
            )
            self._set_window_property(
                key=hourly_properties.SHORT_DATE,
                value=hourly_forecast.timestamp.strftime("%Y-%m-%d")
            )
            self._set_window_property(
                key=hourly_properties.OUTLOOK,
                value=hourly_forecast.condition_str
            )
            self._set_window_property(
                key=hourly_properties.OUTLOOK_ICON,
                value=hourly_forecast.outlook_icon
            )
            self._set_window_property(
                key=hourly_properties.FANART_CODE,
                value=str(hourly_forecast.fanart_code)
            )
            self._set_window_property(
                key=hourly_properties.WIND_SPEED,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    self.wind_speed_unit.from_si_value(hourly_forecast.wind_speed.si_value())
                )
            )
            self._set_window_property(
                key=hourly_properties.WIND_DIRECTION,
                value=self._get_localized_string(id=hourly_forecast.wind_direction.value)
            )
            self._set_window_property(
                key=hourly_properties.HUMIDITY,
                value=percent(hourly_forecast.humidity)
            )
            self._set_window_property(
                key=hourly_properties.TEMPERATURE,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    self.temperature_unit.from_si_value(hourly_forecast.temperature.si_value())
                )
            )
            self._set_window_property(
                key=hourly_properties.DEW_POINT,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    self.temperature_unit.from_si_value(hourly_forecast.dew_point.si_value())
                )
            )
            self._set_window_property(
                key=hourly_properties.FEELS_LIKE,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    self.temperature_unit.from_si_value(hourly_forecast.feels_like.si_value())
                )
            )
            self._set_window_property(
                key=hourly_properties.PRESSURE,
                value=hourly_forecast.pressure
            )
            self._set_window_property(
                key=hourly_properties.PRECIPITATION,
                value=hourly_forecast.precipitation
            )

        # daily
        for daily_forecast, daily_properties, daily_properties_compat in zip(
            forecast.DailyForecasts,
            _KodiWeatherProperties.dailies(),
            _KodiWeatherProperties.dailies_compat(),
        ):
            daily_forecast: KodiDailyForecastData
            daily_properties: _KodiDailyWeatherProperties
            daily_properties_compat: _KodiDailyWeatherPropertiesCompat
            self._set_window_property(
                key=daily_properties.SHORT_DATE,
                value=daily_forecast.timestamp.strftime("%Y-%m-%d")
            )
            self._set_window_property(
                key=daily_properties.SHORT_DAY,
                value=self._get_localized_string(id=daily_forecast.timestamp.isoweekday() + 40)
            )
            self._set_window_property(
                key=daily_properties.HIGH_TEMPERATURE,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    self.temperature_unit.from_si_value(daily_forecast.temperature.si_value())
                )
            )
            self._set_window_property(
                key=daily_properties.LOW_TEMPERATURE,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    self.temperature_unit.from_si_value(daily_forecast.low_temperature.si_value())
                )
            )
            self._set_window_property(
                key=daily_properties.OUTLOOK,
                value=daily_forecast.condition_str
            )
            self._set_window_property(
                key=daily_properties.OUTLOOK_ICON,
                value=daily_forecast.outlook_icon
            )
            self._set_window_property(
                key=daily_properties.FANART_CODE,
                value=str(daily_forecast.fanart_code)
            )
            self._set_window_property(
                key=daily_properties.WIND_SPEED,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    self.wind_speed_unit.from_si_value(daily_forecast.wind_speed.si_value())
                )
            )
            self._set_window_property(
                key=daily_properties.WIND_DIRECTION,
                value=self._get_localized_string(id=daily_forecast.wind_direction.value)
            )
            self._set_window_property(
                key=daily_properties.PRECIPITATION,
                value=daily_forecast.precipitation
            )
            self._set_window_property(
                key=daily_properties_compat.TITLE,
                value=self._get_localized_string(id=daily_forecast.timestamp.isoweekday() + 10)
            )
            self._set_window_property(
                key=daily_properties_compat.HIGH_TEMP,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    TemperatureCelsius.from_si_value(daily_forecast.temperature.si_value())
                )   # converted by skins from °C
            )
            self._set_window_property(
                key=daily_properties_compat.LOW_TEMP,
                value=KodiHomeAssistantWeatherPluginAdapter.format_unit(
                    TemperatureCelsius.from_si_value(daily_forecast.low_temperature.si_value())
                )   # converted by skins from °C
            )
            self._set_window_property(
                key=daily_properties_compat.OUTLOOK,
                value=daily_forecast.condition_str
            )
            self._set_window_property(
                key=daily_properties_compat.OUTLOOK_ICON,
                value=daily_forecast.outlook_icon
            )
            self._set_window_property(
                key=daily_properties_compat.FANART_CODE,
                value=str(daily_forecast.fanart_code)
            )
        # general
        # TODO: Override location from settings
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.LOCATION,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.CURRENT_LOCATION,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_LOCATION,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.REGIONAL_LOCATION,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_CITY,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_COUNTRY,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_LATITUDE,
            value="0"
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_LONGITUDE,
            value="0"
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_FETCHED,
            value=true
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_UPDATED,
            value=datetime.now(tz=UTC).isoformat()
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.UPDATED,
            value=datetime.now(tz=UTC).isoformat()
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.WEATHER_PROVIDER,
            value=self._get_localized_string(id=KodiAddonStrings.ADDON_SHORT_NAME)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.WEATHER_PROVIDER_LOGO,
            value=xbmcvfs.translatePath(os.path.join(self.cwd, "resources", "banner.jpg"))
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.WEATHER_IS_FETCHED,
            value=true
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.CURRENT_IS_FETCHED,
            value=true
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.HOURLY_IS_FETCHED,
            value=true
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.DAILY_IS_FETCHED,
            value=true
        )
