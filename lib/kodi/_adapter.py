import xbmc
import xbmcaddon
import xbmcgui

from ._properties import _KodiWeatherProperties
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
                *_KodiWeatherProperties.DAY0.values,
                *_KodiWeatherProperties.DAY1.values,
                *_KodiWeatherProperties.DAY2.values,
                *_KodiWeatherProperties.DAY3.values,
                *_KodiWeatherProperties.DAY4.values,
                *_KodiWeatherProperties.DAY5.values,
        ):
            self._window.setProperty(key=key, value="")
