import urllib.parse
from dataclasses import dataclass
from typing import Dict, Union, List

import requests
from requests import RequestException


@dataclass
class HomeAssistantCurrentForecast:
    temperature: float
    dew_point: float
    temperature_unit: str
    humidity: float
    cloud_coverage: float
    uv_index: float
    pressure: float
    pressure_unit: str
    wind_bearing: float
    wind_speed: float
    wind_speed_unit: str
    visibility_unit: str
    precipitation_unit: str
    attribution: str
    friendly_name: str
    supported_features: int


@dataclass
class HomeAssistantHourlyForecast:
    condition: str
    datetime: str
    wind_bearing: float
    cloud_coverage: float
    uv_index: float
    temperature: float
    wind_speed: float
    precipitation: float
    humidity: float


@dataclass
class HomeAssistantDailyForecast:
    condition: str
    datetime: str
    wind_bearing: float
    temperature: float
    templow: float
    wind_speed: float
    precipitation: float
    humidity: float
    uv_index: Union[float, None] = None


@dataclass
class HomeAssistantForecast:
    current: HomeAssistantCurrentForecast
    hourly: List[HomeAssistantHourlyForecast]
    daily: List[HomeAssistantDailyForecast]


@dataclass
class RequestError(Exception):
    error_code: int
    url: str
    method: str
    body: str


class HomeAssistantAdapter:
    @staticmethod
    def __make_headers_from_token(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @staticmethod
    def __request(url: str, token: str, post: bool = False,
                  data: Union[Dict[str, str], None] = None) -> requests.Response:
        try:
            if post:
                r = requests.post(
                    url=url, headers=HomeAssistantAdapter.__make_headers_from_token(token=token), json=data,
                    params={"return_response": True}
                )
            else:
                r = requests.get(
                    url=url, headers=HomeAssistantAdapter.__make_headers_from_token(token=token), params=data
                )
        except RequestException:
            raise RequestError(error_code=-1, url=url, method="POST" if post else "GET", body="")
        if not r.ok:
            raise RequestError(error_code=r.status_code, url=url, method="POST" if post else "GET", body=r.text)
        return r

    @staticmethod
    def get_forecast(server_url: str, entity_id: str, token: str) -> HomeAssistantForecast:
        current_url = urllib.parse.urljoin(base=server_url, url=f"/api/states/{entity_id}")
        forecast_url = urllib.parse.urljoin(base=server_url, url="/api/services/weather/get_forecasts")
        current = HomeAssistantAdapter.__request(url=current_url, token=token)
        hourly = HomeAssistantAdapter.__request(
            url=forecast_url, token=token, post=True, data={"entity_id": entity_id, "type": "hourly"}
        )
        daily = HomeAssistantAdapter.__request(
            url=forecast_url, token=token, post=True, data={"entity_id": entity_id, "type": "daily"}
        )
        return HomeAssistantForecast(
            current=HomeAssistantCurrentForecast(**current.json()["attributes"]),
            hourly=[
                HomeAssistantHourlyForecast(**hourly_forecast)
                for hourly_forecast in hourly.json()["service_response"][entity_id]["forecast"]
            ],
            daily=[
                HomeAssistantDailyForecast(**daily_forecast)
                for daily_forecast in daily.json()["service_response"][entity_id]["forecast"]
            ],
        )
