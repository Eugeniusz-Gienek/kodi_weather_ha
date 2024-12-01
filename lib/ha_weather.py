import json
import os.path

from xbmcvfs import translatePath

from lib.homeassistant_adapter import HomeAssistantAdapter, RequestError
from lib.kodi_adapter import KodiHomeAssistantWeatherPluginAdapter, KodiAddonStrings, KodiLogLevel

# from .util import *


# get settings...
MAX_REQUEST_RETRIES = 6
RETRY_DELAY_S = 10


class KodiHomeAssistantWeatherPlugin:
    def __init__(self, kodi_adapter: KodiHomeAssistantWeatherPluginAdapter):
        self._kodi_adapter = kodi_adapter
        self._kodi_adapter.log("Home Assistant Weather started.")

        if not self._kodi_adapter.required_settings_done:
            self._kodi_adapter.dialog(message_id=KodiAddonStrings.SETTINGS_REQUIRED)
            self._kodi_adapter.log("Settings for Home Assistant Weather not yet provided. Plugin will not work.")
        else:
            self.get_forecast_handling_errors()
        self._kodi_adapter.log("Home Assistant Weather init finished.")

    def get_forecast_handling_errors(self):
        try:
            HomeAssistantAdapter.get_forecast(
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
            self._kodi_adapter.clear_weather_properties()

    def get_forecasts(self):
        global ha_weather_url, ha_weather_daily_url, ha_server, ha_key
        log('Getting forecasts from Home Assistant server.')
        # Current weather
        response = self.get_request(ha_weather_url)
        if response is not None:
            log('Response (weather) from server: ' + str(response.content))
            try:
                parsed_response = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                show_dialog(__addon__.getLocalizedString(30014))
                self._kodi_adapter.clear_weather_properties()
                raise Exception(
                    'Got incorrect response from Home Assistant Weather server (request was to ' + ha_weather_url + ' with data: ' + ha_weather_url_data + ') and response received: ' + response.text)
            if parsed_response.get('attributes') is not None:
                forecast = parsed_response['attributes']
                # HA format
                temperature_unit = forecast['temperature_unit']
                pressure_unit = forecast['pressure_unit']
                wind_speed_unit = forecast['wind_speed_unit']
                precipitation_unit = forecast['precipitation_unit']
                loc_friendly_name = forecast['friendly_name']
                forecast_description = forecast['attribution']
                loc = ha_loc_title
                if ha_use_loc_title == "true":
                    loc = loc_friendly_name
                if 'state' not in parsed_response:
                    parsed_response['state'] = 'n/a'
                if 'last_updated' not in parsed_response:
                    parsed_response['last_updated'] = 'n/a'
                if 'temperature' not in forecast:
                    forecast['temperature'] = 0
                if 'wind_speed' not in forecast:
                    forecast['wind_speed'] = 0
                if 'wind_bearing' not in forecast:
                    forecast['wind_bearing'] = 0
                if 'humidity' not in forecast:
                    forecast['humidity'] = 0
                if 'dew_point' not in forecast:
                    forecast['dew_point'] = 0
                if 'pressure' not in forecast:
                    forecast['pressure'] = 0
                set_property('Location1', loc, WND)
                set_property('Locations', '1', WND)
                set_property('ForecastLocation', loc, WND)
                set_property('RegionalLocation', loc, WND)
                set_property('Updated', parsed_response['last_updated'], WND)
                set_property('Current.Location', loc, WND)
                set_property('Current.Condition', str(fix_condition_translation_codes(parsed_response['state'])), WND)
                set_property('Current.Temperature', str(convert_temp(forecast['temperature'], temperature_unit, 'C')),
                             WND)
                set_property('Current.UVIndex', '0', WND)
                set_property('Current.OutlookIcon', '%s.png' % get_condition_code_by_name(parsed_response['state']),
                             WND)
                set_property('Current.FanartCode', get_condition_code_by_name(parsed_response['state']), WND)
                set_property('Current.Wind', str(convert_speed(forecast['wind_speed'], wind_speed_unit, 'kmh')), WND)
                set_property('Current.WindDirection', xbmc.getLocalizedString(wind_dir(forecast['wind_bearing'])), WND)
                set_property('Current.Humidity', str(forecast['humidity']), WND)
                set_property('Current.DewPoint', str(convert_temp(forecast['dew_point'], temperature_unit, 'C')), WND)
                set_property('Current.FeelsLike',
                             str(calculate_feels_like(convert_temp(forecast['temperature'], temperature_unit, 'C'),
                                                      forecast['humidity'])), WND)
                set_property('Current.WindChill', convert_temp(
                    windchill(int(convert_temp(forecast['temperature'], temperature_unit, 'F')),
                              int(convert_speed(forecast['wind_speed'], wind_speed_unit, 'mph'))), 'F') + TEMPUNIT, WND)
                set_property('Current.Pressure', str(forecast['pressure']), WND)
                set_property('Current.IsFetched', 'true', WND)
                set_property('Forecast.City', loc, WND)
                set_property('Forecast.Country', loc, WND)
                set_property('Forecast.Latitude', '0', WND)
                set_property('Forecast.Longitude', '0', WND)
                set_property('Forecast.IsFetched', 'true', WND)
                set_property('Forecast.Updated', parsed_response['last_updated'], WND)
                set_property('WeatherProvider', 'Home Assistant Weather', WND)
                set_property('WeatherProviderLogo', translatePath(os.path.join(__cwd__, 'resources', 'banner.png')),
                             WND)
            else:
                log('The response dict from get_forecast url does not contain forecast key. This is unexpected.')
                show_dialog(__addon__.getLocalizedString(30014))
                self._kodi_adapter.clear_weather_properties()
                return
        else:
            log('Response (weather current) from server is NONE!')
            show_dialog('Response (weather current) from server is NONE!')
            self._kodi_adapter.clear_weather_properties()
            return
        # Daily
        response = self.get_request(ha_weather_daily_url)
        if response is not None:
            log('Response (weather hourly) from server: ' + str(response.content))
            try:
                parsed_response = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                show_dialog(__addon__.getLocalizedString(30014))
                self._kodi_adapter.clear_weather_properties()
                raise Exception(
                    'Got incorrect response from Home Assistant Weather server (request was to ' + ha_weather_daily_url + ' with data: ' + ha_weather_hourly_url_data + ') and response received: ' + response.text)
            if parsed_response.get('attributes') is not None:
                forecast = parsed_response['attributes']
                for i in range(0, forecast['days_num']):
                    count = str(i)
                    set_property('Day' + count + '.Title',
                                 convert_datetime(forecast['day' + count + '_date'], 'datetime', 'weekday', 'long'),
                                 WND)
                    set_property('Day' + count + '.FanartCode',
                                 get_condition_code_by_name(forecast['day' + count + '_condition']), WND)
                    set_property('Day' + count + '.Outlook',
                                 str(fix_condition_translation_codes(forecast['day' + count + '_condition'])), WND)
                    set_property('Day' + count + '.OutlookIcon',
                                 '%s.png' % str(get_condition_code_by_name(forecast['day' + count + '_condition'])),
                                 WND)
                    set_property('Day' + count + '.HighTemp',
                                 str(convert_temp(forecast['day' + count + '_temperature'], temperature_unit, 'C')),
                                 WND)
                    set_property('Day' + count + '.LowTemp',
                                 str(convert_temp(forecast['day' + count + '_temperature_low'], temperature_unit, 'C')),
                                 WND)
                    set_property('Daily.' + str(i + 1) + '.ShortDay',
                                 convert_datetime(forecast['day' + count + '_date'], 'datetime', 'weekday', 'short'),
                                 WND)
                    set_property('Daily.' + str(i + 1) + '.LongDay',
                                 convert_datetime(forecast['day' + count + '_date'], 'datetime', 'weekday', 'long'),
                                 WND)
                    set_property('Daily.' + str(i + 1) + '.ShortDate',
                                 convert_datetime(forecast['day' + count + '_date'], 'datetime', 'monthday', 'short'),
                                 WND)
                    set_property('Daily.' + str(i + 1) + '.LongDate',
                                 convert_datetime(forecast['day' + count + '_date'], 'datetime', 'monthday', 'long'),
                                 WND)
                    set_property('Daily.' + str(i + 1) + '.HighTemperature',
                                 str(forecast['day' + count + '_temperature']) + TEMPUNIT, WND)
                    set_property('Daily.' + str(i + 1) + '.LowTemperature',
                                 str(forecast['day' + count + '_temperature_low']) + TEMPUNIT, WND)
                    set_property('Daily.' + str(i + 1) + '.Humidity', str(forecast['day' + count + '_humidity']) + '%',
                                 WND)
                    set_property('Daily.' + str(i + 1) + '.Precipitation',
                                 str(forecast['day' + count + '_precipitation']) + precipitation_unit, WND)
                    set_property('Daily.' + str(i + 1) + '.WindDirection',
                                 str(xbmc.getLocalizedString(wind_dir(forecast['day' + count + '_wind_bearing']))), WND)
                    set_property('Daily.' + str(i + 1) + '.WindSpeed',
                                 str(forecast['day' + count + '_wind_speed']) + SPEEDUNIT, WND)
                    set_property('Daily.' + str(i + 1) + '.WindDegree',
                                 str(forecast['day' + count + '_wind_bearing']) + u'°', WND)
                    set_property('Daily.' + str(i + 1) + '.DewPoint', convert_temp(
                        dewpoint(int(convert_temp(forecast['day' + count + '_temperature'], temperature_unit, 'C')),
                                 int(forecast['day' + count + '_humidity'])), 'C', None), WND)
                    set_property('Daily.' + str(i + 1) + '.Outlook',
                                 str(fix_condition_translation_codes(forecast['day' + count + '_condition'])), WND)
                    set_property('Daily.' + str(i + 1) + '.OutlookIcon',
                                 '%s.png' % str(get_condition_code_by_name(forecast['day' + count + '_condition'])),
                                 WND)
                    set_property('Daily.' + str(i + 1) + '.FanartCode',
                                 get_condition_code_by_name(forecast['day' + count + '_condition']), WND)
                set_property('Daily.IsFetched', 'true', WND)
            else:
                log('The response dict from get_forecast url does not contain forecast key. This is unexpected.')
                show_dialog(__addon__.getLocalizedString(30014))
                self._kodi_adapter.clear_weather_properties()
                return
        else:
            log('Response (weather daily) from server is NONE!')
            show_dialog('Response (weather daily) from server is NONE')
            self._kodi_adapter.clear_weather_properties()
            return
        # Hourly weather
        response = self.get_request(ha_weather_hourly_url)
        if response is not None:
            log('Response (weather daily) from server: ' + str(response.content))
            try:
                parsed_response = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                show_dialog(__addon__.getLocalizedString(30014))
                self._kodi_adapter.clear_weather_properties()
                raise Exception(
                    'Got incorrect response from Home Assistant Weather server (request was to ' + ha_weather_daily_url + ' with data: ' + ha_weather_daily_url_data + ') and response received: ' + response.text)
            if parsed_response.get('attributes') is not None:
                forecast = parsed_response['attributes']
                for i in range(0, forecast['hours_num']):
                    count = str(i)
                    set_property('Hourly.' + str(i + 1) + '.Time',
                                 convert_datetime(forecast['hour' + count + '_date'], 'datetime', 'time', None), WND)
                    set_property('Hourly.' + str(i + 1) + '.ShortDate',
                                 convert_datetime(forecast['hour' + count + '_date'], 'datetime', 'monthday', 'short'),
                                 WND)
                    set_property('Hourly.' + str(i + 1) + '.LongDate',
                                 convert_datetime(forecast['hour' + count + '_date'], 'datetime', 'monthday', 'long'),
                                 WND)
                    set_property('Hourly.' + str(i + 1) + '.Temperature',
                                 str(forecast['hour' + count + '_temperature']) + TEMPUNIT, WND)
                    set_property('Hourly.' + str(i + 1) + '.Humidity',
                                 str(forecast['hour' + count + '_humidity']) + '%', WND)
                    set_property('Hourly.' + str(i + 1) + '.Precipitation',
                                 str(forecast['hour' + count + '_precipitation']) + precipitation_unit, WND)
                    set_property('Hourly.' + str(i + 1) + '.WindDirection',
                                 str(xbmc.getLocalizedString(wind_dir(forecast['hour' + count + '_wind_bearing']))),
                                 WND)
                    set_property('Hourly.' + str(i + 1) + '.WindSpeed',
                                 str(forecast['hour' + count + '_wind_speed']) + SPEEDUNIT, WND)
                    set_property('Hourly.' + str(i + 1) + '.WindDegree',
                                 str(forecast['hour' + count + '_wind_bearing']) + u'°', WND)
                    set_property('Hourly.' + str(i + 1) + '.DewPoint', convert_temp(
                        dewpoint(convert_temp(forecast['hour' + count + '_temperature'], temperature_unit, 'C'),
                                 forecast['hour' + count + '_humidity']), 'C', None), WND)
                    set_property('Hourly.' + str(i + 1) + '.Outlook',
                                 str(fix_condition_translation_codes(forecast['hour' + count + '_condition'])), WND)
                    set_property('Hourly.' + str(i + 1) + '.OutlookIcon',
                                 '%s.png' % str(get_condition_code_by_name(forecast['hour' + count + '_condition'])),
                                 WND)
                    set_property('Hourly.' + str(i + 1) + '.FanartCode',
                                 get_condition_code_by_name(forecast['hour' + count + '_condition']), WND)
                set_property('Hourly.IsFetched', 'true', WND)
            else:
                log('The response dict from get_forecast url does not contain forecast key. This is unexpected.')
                show_dialog(__addon__.getLocalizedString(30014))
                self._kodi_adapter.clear_weather_properties()
                return
        else:
            log('Response (weather daily) from server is NONE!')
            show_dialog('Response (weather daily) from server is NONE')
            self._kodi_adapter.clear_weather_properties()
            return
