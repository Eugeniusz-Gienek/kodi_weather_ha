from dataclasses import dataclass
from typing import Type

_Setting_Type = bool | int | float | str


@dataclass
class _HomeAssistantWeatherPluginSetting:
    setting_id: str
    setting_type: Type[_Setting_Type]


class _HomeAssistantWeatherPluginSettings(_HomeAssistantWeatherPluginSetting):
    LOCATION_TITLE = _HomeAssistantWeatherPluginSetting(setting_id="loc_title", setting_type=str)
    USE_HOME_ASSISTANT_LOCATION_NAME = _HomeAssistantWeatherPluginSetting(setting_id="useHALocName", setting_type=bool)
    HOME_ASSISTANT_SERVER = _HomeAssistantWeatherPluginSetting(setting_id="ha_server", setting_type=str)
    HOME_ASSISTANT_TOKEN = _HomeAssistantWeatherPluginSetting(setting_id="ha_key", setting_type=str)
    HOME_ASSISTANT_WEATHER_FORECAST_ENTITY_ID = _HomeAssistantWeatherPluginSetting(setting_id="ha_weather_forecast_entity_id", setting_type=str)
    LOG_ENABLED = _HomeAssistantWeatherPluginSetting(setting_id="logEnabled", setting_type=bool)
