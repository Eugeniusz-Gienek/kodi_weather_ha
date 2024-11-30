from dataclasses import dataclass


@dataclass
class HomeAssistantForecast:
    ...


class RequestError(Exception):
    error_code: int


class HomeAssistantAdapter:
    @staticmethod
    def get_forecast(forecast_url: str, token: str) -> HomeAssistantForecast:
        ...
