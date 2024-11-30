import logging
import urllib.parse
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import TypeVar, Type

import xbmc
import xbmcaddon
import xbmcgui

_Setting_Type = TypeVar('_Setting_Type', bool, int, float, str)


@dataclass
class _HomeAssistantWeatherPluginSetting:
    setting_id: str
    setting_type: Type[_Setting_Type]


class HomeAssistantWeatherPluginSettings(_HomeAssistantWeatherPluginSetting):
    LOCATION_TITLE = _HomeAssistantWeatherPluginSetting(setting_id="loc_title", setting_type=str)
    USE_HOME_ASSISTANT_LOCATION_NAME = _HomeAssistantWeatherPluginSetting(setting_id="useHALocName", setting_type=bool)
    HOME_ASSISTANT_SERVER = _HomeAssistantWeatherPluginSetting(setting_id="ha_server", setting_type=str)
    HOME_ASSISTANT_TOKEN = _HomeAssistantWeatherPluginSetting(setting_id="ha_key", setting_type=str)
    HOME_ASSISTANT_WEATHER_PATH = _HomeAssistantWeatherPluginSetting(setting_id="ha_weather_url", setting_type=str)
    HOME_ASSISTANT_WEATHER_REQ_METHOD = _HomeAssistantWeatherPluginSetting(setting_id="ha_weather_url_method", setting_type=str)
    HOME_ASSISTANT_WEATHER_REQ_DATA = _HomeAssistantWeatherPluginSetting(setting_id="ha_weather_url_data", setting_type=str)
    LOG_ENABLED = _HomeAssistantWeatherPluginSetting(setting_id="logEnabled", setting_type=bool)
    # TODO: Is this necessary?
    LOCATION_1 = _HomeAssistantWeatherPluginSetting(setting_id="location1", setting_type=str)


class _KodiMagicValues:
    WEATHER_WINDOW_ID = 12600  # see https://kodi.wiki/view/Weather_addons at "Required output"
    ADDON_INFO_PATH_ID = "path"
    ADDON_INFO_ADDON_ID = "id"
    ADDON_INFO_NAME_ID = "name"
    REGION_TEMPERATURE_UNIT_ID = "tempunit"
    REGION_WIND_SPEED_UNIT_ID = "windspeedunit"


class KodiAddonStrings(IntEnum):
    SETTINGS_REQUIRED = 30010
    HOMEASSISTANT_UNREACHABLE = 30013


class KodiLogLevel(Enum):
    DEBUG = xbmc.LOGDEBUG
    INFO = xbmc.LOGINFO
    WARNING = xbmc.LOGWARNING
    ERROR = xbmc.LOGERROR
    CRITICAL = xbmc.LOGFATAL


class _NestedProperties:
    def __init__(self, prefix: str):
        self._prefix = prefix

    def __getattribute__(self, item: str):
        return object.__getattribute__(self, "_prefix") + object.__getattribute__(self, item)


class KodiCurrentWeatherProperties(_NestedProperties):
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


class KodiDailyWeatherPropertiesCompat(_NestedProperties):
    Title = "Title"
    HighTemp = "HighTemp"
    LowTemp = "LowTemp"
    Outlook = "Outlook"
    OutlookIcon = "OutlookIcon"
    FanartCode = "FanartCode"


class KodiWeatherProperties:
    CURRENT = KodiCurrentWeatherProperties("Current.")

    DAY0 = KodiDailyWeatherPropertiesCompat("Day0.")
    DAY1 = KodiDailyWeatherPropertiesCompat("Day1.")
    DAY2 = KodiDailyWeatherPropertiesCompat("Day2.")
    DAY3 = KodiDailyWeatherPropertiesCompat("Day3.")
    DAY4 = KodiDailyWeatherPropertiesCompat("Day4.")
    DAY5 = KodiDailyWeatherPropertiesCompat("Day5.")


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
    def home_assistant_forecast_url(self) -> str:
        base_url = self._get_setting(setting=HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_SERVER)
        path = self._get_setting(setting=HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_WEATHER_PATH)
        return urllib.parse.urljoin(base=base_url, url=path)

    @property
    def home_assistant_token(self) -> str:
        return self._get_setting(setting=HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_TOKEN)

    def log(self, message: str, level: KodiLogLevel = KodiLogLevel.DEBUG):
        if self._get_setting(setting=HomeAssistantWeatherPluginSettings.LOG_ENABLED):
            msg = f"[ HOME ASSISTANT WEATHER ]: {self.__addon_id}: {message}"
            xbmc.log(msg=msg, level=level.value)

    @property
    def required_settings_done(self) -> bool:
        return bool(self.home_assistant_token) and bool(self.home_assistant_forecast_url)

    def dialog(self, message_id: KodiAddonStrings) -> bool:
        return xbmcgui.Dialog().ok(
            heading=self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_NAME_ID),
            message=self._kodi_addon.getLocalizedString(id=message_id)
        )

    def clear_weather_properties(self) -> None:
        # TODO: Some enum members may be missing
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.CONDITION, value='N/A')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.TEMPERATURE, value='0')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.WIND, value='0')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.WIND_DIRECTION, value='N/A')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.HUMIDITY, value='0')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.FEELS_LIKE, value='0')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.UV_INDEX, value='0')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.DEW_POINT, value='0')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.OUTLOOK_ICON, value='na.png')
        self._window.setProperty(key=KodiWeatherProperties.CURRENT.FANART_CODE, value='na')
        # END TODO

        # TODO: What about non-compat entries?

        for compat_entry in (
                KodiWeatherProperties.DAY0,
                KodiWeatherProperties.DAY1,
                KodiWeatherProperties.DAY2,
                KodiWeatherProperties.DAY3,
                KodiWeatherProperties.DAY4,
                KodiWeatherProperties.DAY5
        ):
            self._window.setProperty(compat_entry.Title, 'N/A')
            self._window.setProperty(compat_entry.HighTemp, '0')
            self._window.setProperty(compat_entry.LowTemp, '0')
            self._window.setProperty(compat_entry.Outlook, 'N/A')
            self._window.setProperty(compat_entry.OutlookIcon, 'na.png')
            self._window.setProperty(compat_entry.FanartCode, 'na')
