import urllib.parse
from typing import Dict, Union

import requests
from requests import RequestException

from ._errors import RequestError
from ._forecast import (
    HomeAssistantForecast, HomeAssistantCurrentForecast, HomeAssistantHourlyForecast, HomeAssistantDailyForecast
)
from ._sun import HomeAssistantSunInfo, HomeAssistantSunState


class HomeAssistantAdapter:
    @staticmethod
    def __make_headers_from_token(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @staticmethod
    def __request(url: str, token: str, post: bool = False,
                  data: Union[Dict[str, str], None] = None, check_ssl = True, request_attempts = 5) -> requests.Response:
        err_code_received = -1
        err_msg = "Unknown error"
        default_request_attempts = 5
        try:
            request_attempts = max(1,int(request_attempts))
        except TypeError:
            request_attempts = default_request_attempts
        except ValueError:
            request_attempts = default_request_attempts
        for i in range(request_attempts):
            try:
                if post:
                    r = requests.post(
                        url=url, headers=HomeAssistantAdapter.__make_headers_from_token(token=token), json=data,
                        params={"return_response": True}, verify=check_ssl
                    )
                else:
                    r = requests.get(
                        url=url, headers=HomeAssistantAdapter.__make_headers_from_token(token=token), params=data, verify=check_ssl
                    )
                if r.ok:
                    return r
            except RequestException:
                #raise RequestError(error_code=-1, url=url, method="POST" if post else "GET", body="")
                err_code_received = -1
                err_msg = "Unknown error"
            if not r.ok:
                #raise RequestError(error_code=r.status_code, url=url, method="POST" if post else "GET", body=r.text)
                err_code_received = r.status_code
                err_msg = r.text
        raise RequestError(error_code=err_code_received, url=url, method="POST" if post else "GET", body=err_msg)
        #return False

    @staticmethod
    def filter_attributes(attributes_received,forecast_type='current'):
        output_attributes = {}
        allowed_keys = [
            'temperature',
            'dew_point',
            'temperature_unit',
            'humidity',
            'uv_index',
            'pressure',
            'pressure_unit',
            'wind_bearing',
            'wind_speed',
            'wind_speed_unit',
            'precipitation_unit',
            'supported_features',
            'visibility_unit',
            'attribution',
            'friendly_name',
            'cloud_coverage'
        ]
        if forecast_type == 'hourly':
            allowed_keys = [
                'temperature',
                'humidity',
                'uv_index',
                'wind_bearing',
                'wind_speed',
                'cloud_coverage',
                'condition',
                'datetime',
                'precipitation',
            ]
        elif forecast_type == 'daily':
            allowed_keys = [
                'temperature',
                'humidity',
                'uv_index',
                'wind_bearing',
                'wind_speed',
                'condition',
                'datetime',
                'precipitation',
                'templow',
            ]
        for key in attributes_received:
            if key in allowed_keys:
                output_attributes[key] = attributes_received[key]
        for key in allowed_keys:
            if not key in output_attributes:
                output_attributes[key] = None
        return output_attributes

    @staticmethod
    def get_forecast(server_url: str, entity_id: str, token: str, check_ssl: bool, request_attempts: int) -> HomeAssistantForecast:
        # Based on Home Assistant's WeatherEntityFeature IntFlag
        FORECAST_DAILY = 1
        FORECAST_HOURLY = 2

        current_url = urllib.parse.urljoin(base=server_url, url=f"/api/states/{entity_id}")
        forecast_url = urllib.parse.urljoin(base=server_url, url="/api/services/weather/get_forecasts")

        current = HomeAssistantAdapter.__request(url=current_url, token=token, check_ssl=check_ssl, request_attempts=request_attempts)
        current_json = current.json()
        current_forecast_attributes = HomeAssistantAdapter.filter_attributes(current_json["attributes"], 'current')
        current_forecast_attributes['condition'] = current_json['state']
        supported_features = current_json.get("attributes", {}).get("supported_features", 0)
        if supported_features is None:
            supported_features = 0

        hourly_forecast_attributes = []
        if supported_features & FORECAST_HOURLY:
            try:
                hourly = HomeAssistantAdapter.__request(
                    url=forecast_url, token=token, post=True, data={"entity_id": entity_id, "type": "hourly"}, check_ssl=check_ssl, request_attempts=request_attempts
                )
                hourly_forecast_attributes = [HomeAssistantAdapter.filter_attributes(hourly_forecast, 'hourly') for hourly_forecast in hourly.json()["service_response"][entity_id]["forecast"]]
            except RequestError:
                hourly_forecast_attributes = []

        daily_forecast_attributes = []
        if supported_features & FORECAST_DAILY:
            try:
                daily = HomeAssistantAdapter.__request(
                    url=forecast_url, token=token, post=True, data={"entity_id": entity_id, "type": "daily"}, check_ssl=check_ssl, request_attempts=request_attempts
                )
                daily_forecast_attributes = [HomeAssistantAdapter.filter_attributes(daily_forecast, 'daily') for daily_forecast in daily.json()["service_response"][entity_id]["forecast"]]
            except RequestError:
                daily_forecast_attributes = []

        return HomeAssistantForecast(
            current=HomeAssistantCurrentForecast(**current_forecast_attributes),
            hourly=[
                HomeAssistantHourlyForecast(**hourly_forecast)
                for hourly_forecast in hourly_forecast_attributes
            ],
            daily=[
                HomeAssistantDailyForecast(**daily_forecast)
                for daily_forecast in daily_forecast_attributes
            ],
        )

    @staticmethod
    def get_sun_info(server_url: str, entity_id: str, token: str, check_ssl: bool, request_attempts: int) -> HomeAssistantSunInfo:
        sun_url = urllib.parse.urljoin(base=server_url, url=f"/api/states/{entity_id}")
        sun = HomeAssistantAdapter.__request(url=sun_url, token=token, check_ssl=check_ssl, request_attempts=request_attempts)
        sun_data = sun.json()
        return HomeAssistantSunInfo(**sun_data["attributes"], state=HomeAssistantSunState(sun_data["state"]))
