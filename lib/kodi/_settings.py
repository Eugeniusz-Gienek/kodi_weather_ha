from dataclasses import dataclass
from typing import Type

_Setting_Type = bool | int | float | str


@dataclass
class KodiPluginSetting:
    setting_id: str
    setting_type: Type[_Setting_Type]
