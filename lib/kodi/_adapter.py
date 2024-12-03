import os.path

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from ._forecast import KodiForecastData, KodiHourlyForecastData, KodiDailyForecastData
from ._properties import _KodiWeatherProperties, _KodiHourlyWeatherProperties, _KodiDailyWeatherProperties, \
    _KodiDailyWeatherPropertiesCompat
from ._settings import _HomeAssistantWeatherPluginSetting, _Setting_Type, _HomeAssistantWeatherPluginSettings
from ._values import _KodiMagicValues, KodiLogLevel, KodiAddonStrings


class KodiHomeAssistantWeatherPluginAdapter:

    def __init__(self) -> None:
        self._window = xbmcgui.Window(existingWindowId=_KodiMagicValues.WEATHER_WINDOW_ID)
        self._kodi_addon = xbmcaddon.Addon()
        self.__addon_id = self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_ADDON_ID)

    @property
    def cwd(self) -> str:
        return self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_PATH_ID)

    @property
    def temperature_unit(self):
        return xbmc.getRegion(id=_KodiMagicValues.REGION_TEMPERATURE_UNIT_ID)

    @property
    def wind_speed_unit(self):
        return xbmc.getRegion(id=_KodiMagicValues.REGION_WIND_SPEED_UNIT_ID)

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
            message=self._kodi_addon.getLocalizedString(id=message_id)
        )

    def clear_weather_properties(self) -> None:
        for key in (
                *_KodiWeatherProperties.GENERAL.values,
                *_KodiWeatherProperties.CURRENT.values,
                *_KodiWeatherProperties.HOURLY_1.values,
                *_KodiWeatherProperties.HOURLY_2.values,
                *_KodiWeatherProperties.HOURLY_3.values,
                *_KodiWeatherProperties.HOURLY_4.values,
                *_KodiWeatherProperties.HOURLY_5.values,
                *_KodiWeatherProperties.HOURLY_6.values,
                *_KodiWeatherProperties.HOURLY_7.values,
                *_KodiWeatherProperties.HOURLY_8.values,
                *_KodiWeatherProperties.HOURLY_9.values,
                *_KodiWeatherProperties.HOURLY_10.values,
                *_KodiWeatherProperties.HOURLY_11.values,
                *_KodiWeatherProperties.HOURLY_12.values,
                *_KodiWeatherProperties.HOURLY_13.values,
                *_KodiWeatherProperties.HOURLY_14.values,
                *_KodiWeatherProperties.HOURLY_15.values,
                *_KodiWeatherProperties.HOURLY_16.values,
                *_KodiWeatherProperties.HOURLY_17.values,
                *_KodiWeatherProperties.HOURLY_18.values,
                *_KodiWeatherProperties.HOURLY_19.values,
                *_KodiWeatherProperties.HOURLY_20.values,
                *_KodiWeatherProperties.HOURLY_21.values,
                *_KodiWeatherProperties.HOURLY_22.values,
                *_KodiWeatherProperties.HOURLY_23.values,
                *_KodiWeatherProperties.HOURLY_24.values,
                *_KodiWeatherProperties.DAILY_1.values,
                *_KodiWeatherProperties.DAILY_2.values,
                *_KodiWeatherProperties.DAILY_3.values,
                *_KodiWeatherProperties.DAILY_4.values,
                *_KodiWeatherProperties.DAILY_5.values,
                *_KodiWeatherProperties.DAILY_6.values,
                *_KodiWeatherProperties.DAILY_7.values,
                *_KodiWeatherProperties.DAY0.values,
                *_KodiWeatherProperties.DAY1.values,
                *_KodiWeatherProperties.DAY2.values,
                *_KodiWeatherProperties.DAY3.values,
                *_KodiWeatherProperties.DAY4.values,
                *_KodiWeatherProperties.DAY5.values,
                *_KodiWeatherProperties.DAY6.values,
        ):
            self._window.setProperty(key=key, value="")

    def set_weather_properties(self, forecast: KodiForecastData) -> None:
        whole_number = "{:.0f}".format
        true = "true"
        # general
        # TODO: Override location from settings
        self._window.setProperty(
            key=_KodiWeatherProperties.GENERAL.LOCATION,
            value=forecast.General.location
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.GENERAL.CURRENT_LOCATION,
            value=forecast.General.location
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.GENERAL.WEATHER_PROVIDER,
            value=self._kodi_addon.getLocalizedString(id=KodiAddonStrings.ADDON_SHORT_NAME)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.GENERAL.WEATHER_PROVIDER_LOGO,
            value=xbmcvfs.translatePath(os.path.join(self.cwd, "resources", "banner.jpg"))
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.GENERAL.WEATHER_IS_FETCHED,
            value=true
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.GENERAL.CURRENT_IS_FETCHED,
            value=true
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.GENERAL.HOURLY_IS_FETCHED,
            value=true
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.GENERAL.DAILY_IS_FETCHED,
            value=true
        )
        # current
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.CONDITION,
            value=forecast.Current.condition_str
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.TEMPERATURE,
            value=whole_number(forecast.Current.temperature)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.WIND,
            value=whole_number(forecast.Current.wind_speed)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.WIND_DIRECTION,
            value=self._kodi_addon.getLocalizedString(id=forecast.Current.wind_direction.value)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.HUMIDITY,
            value=whole_number(forecast.Current.humidity)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.FEELS_LIKE,
            value=whole_number(forecast.Current.feels_like)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.UV_INDEX,
            value=whole_number(forecast.Current.uv_index)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.DEW_POINT,
            value=whole_number(forecast.Current.dew_point)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.PRECIPITATION,
            value=whole_number(forecast.Current.precipitation)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.CLOUDINESS,
            value=whole_number(forecast.Current.cloudiness)
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.OUTLOOK_ICON,
            value=forecast.Current.outlook_icon
        )
        self._window.setProperty(
            key=_KodiWeatherProperties.CURRENT.FANART_CODE,
            value=whole_number(forecast.Current.fanart_code)
        )

        # hourly
        for hourly_forecast, hourly_properties in zip(
                forecast.HourlyForecasts,
                (
                        _KodiWeatherProperties.HOURLY_1,
                        _KodiWeatherProperties.HOURLY_2,
                        _KodiWeatherProperties.HOURLY_3,
                        _KodiWeatherProperties.HOURLY_4,
                        _KodiWeatherProperties.HOURLY_5,
                        _KodiWeatherProperties.HOURLY_6,
                        _KodiWeatherProperties.HOURLY_7,
                        _KodiWeatherProperties.HOURLY_8,
                        _KodiWeatherProperties.HOURLY_9,
                        _KodiWeatherProperties.HOURLY_10,
                        _KodiWeatherProperties.HOURLY_11,
                        _KodiWeatherProperties.HOURLY_12,
                        _KodiWeatherProperties.HOURLY_13,
                        _KodiWeatherProperties.HOURLY_14,
                        _KodiWeatherProperties.HOURLY_15,
                        _KodiWeatherProperties.HOURLY_16,
                        _KodiWeatherProperties.HOURLY_17,
                        _KodiWeatherProperties.HOURLY_18,
                        _KodiWeatherProperties.HOURLY_19,
                        _KodiWeatherProperties.HOURLY_20,
                        _KodiWeatherProperties.HOURLY_21,
                        _KodiWeatherProperties.HOURLY_22,
                        _KodiWeatherProperties.HOURLY_23,
                )
        ):
            hourly_forecast: KodiHourlyForecastData
            hourly_properties: _KodiHourlyWeatherProperties
            self._window.setProperty(
                key=hourly_properties.TIME,
                value=hourly_forecast.timestamp.strftime("%H:%M")
            )
            self._window.setProperty(
                key=hourly_properties.LONG_DATE,
                value=hourly_forecast.timestamp.strftime("%Y-%m-%d")
            )
            self._window.setProperty(
                key=hourly_properties.SHORT_DATE,
                value=hourly_forecast.timestamp.strftime("%Y-%m-%d")
            )
            self._window.setProperty(
                key=hourly_properties.OUTLOOK,
                value=hourly_forecast.condition_str
            )
            self._window.setProperty(
                key=hourly_properties.OUTLOOK_ICON,
                value=hourly_forecast.outlook_icon
            )
            self._window.setProperty(
                key=hourly_properties.FANART_CODE,
                value=whole_number(hourly_forecast.fanart_code)
            )
            self._window.setProperty(
                key=hourly_properties.WIND_SPEED,
                value=whole_number(hourly_forecast.wind_speed)
            )
            self._window.setProperty(
                key=hourly_properties.WIND_DIRECTION,
                value=self._kodi_addon.getLocalizedString(id=hourly_forecast.wind_direction.value)
            )
            self._window.setProperty(
                key=hourly_properties.HUMIDITY,
                value=whole_number(hourly_forecast.humidity)
            )
            self._window.setProperty(
                key=hourly_properties.TEMPERATURE,
                value=whole_number(hourly_forecast.temperature)
            )
            self._window.setProperty(
                key=hourly_properties.DEW_POINT,
                value=whole_number(hourly_forecast.dew_point)
            )
            self._window.setProperty(
                key=hourly_properties.FEELS_LIKE,
                value=whole_number(hourly_forecast.feels_like)
            )
            self._window.setProperty(
                key=hourly_properties.PRESSURE,
                value=hourly_forecast.pressure
            )
            self._window.setProperty(
                key=hourly_properties.PRECIPITATION,
                value=whole_number(hourly_forecast.precipitation)
            )

        # daily
        for daily_forecast, daily_properties, daily_properties_compat in zip(
            forecast.DailyForecasts,
                (
                    _KodiWeatherProperties.DAILY_1,
                    _KodiWeatherProperties.DAILY_2,
                    _KodiWeatherProperties.DAILY_3,
                    _KodiWeatherProperties.DAILY_4,
                    _KodiWeatherProperties.DAILY_5,
                    _KodiWeatherProperties.DAILY_6,
                    _KodiWeatherProperties.DAILY_7,
                ),
                (
                    _KodiWeatherProperties.DAY0,
                    _KodiWeatherProperties.DAY1,
                    _KodiWeatherProperties.DAY2,
                    _KodiWeatherProperties.DAY3,
                    _KodiWeatherProperties.DAY4,
                    _KodiWeatherProperties.DAY5,
                    _KodiWeatherProperties.DAY6,
                )
        ):
            daily_forecast: KodiDailyForecastData
            daily_properties: _KodiDailyWeatherProperties
            daily_properties_compat: _KodiDailyWeatherPropertiesCompat
            self._window.setProperty(
                key=daily_properties.SHORT_DATE,
                value=daily_forecast.timestamp.strftime("%Y-%m-%d")
            )
            self._window.setProperty(
                key=daily_properties.SHORT_DAY,
                value=self._kodi_addon.getLocalizedString(id=daily_forecast.timestamp.isoweekday() + 40)
            )
            self._window.setProperty(
                key=daily_properties.HIGH_TEMPERATURE,
                value=whole_number(daily_forecast.temperature)
            )
            self._window.setProperty(
                key=daily_properties.LOW_TEMPERATURE,
                value=whole_number(daily_forecast.low_temperature)
            )
            self._window.setProperty(
                key=daily_properties.OUTLOOK,
                value=daily_forecast.condition_str
            )
            self._window.setProperty(
                key=daily_properties.FANART_CODE,
                value=whole_number(daily_forecast.fanart_code)
            )
            self._window.setProperty(
                key=daily_properties.WIND_SPEED,
                value=whole_number(daily_forecast.wind_speed)
            )
            self._window.setProperty(
                key=daily_properties.WIND_DIRECTION,
                value=self._kodi_addon.getLocalizedString(id=daily_forecast.wind_direction.value)
            )
            self._window.setProperty(
                key=daily_properties.PRECIPITATION,
                value=whole_number(daily_forecast.precipitation)
            )
            self._window.setProperty(
                key=daily_properties_compat.TITLE,
                value=self._kodi_addon.getLocalizedString(id=daily_forecast.timestamp.isoweekday() + 10)
            )
            self._window.setProperty(
                key=daily_properties_compat.HIGH_TEMP,
                value=whole_number(daily_forecast.temperature)
            )
            self._window.setProperty(
                key=daily_properties_compat.LOW_TEMP,
                value=whole_number(daily_forecast.low_temperature)
            )
            self._window.setProperty(
                key=daily_properties_compat.OUTLOOK,
                value=daily_forecast.condition_str
            )
            self._window.setProperty(
                key=daily_properties_compat.OUTLOOK_ICON,
                value=daily_forecast.outlook_icon
            )
            self._window.setProperty(
                key=daily_properties_compat.FANART_CODE,
                value=whole_number(daily_forecast.fanart_code)
            )
























