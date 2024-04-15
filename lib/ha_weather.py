import os
import sys
import urllib

import xbmcgui
import xbmcplugin
import xbmcaddon

import requests
import json
import yaml

import time
from datetime import datetime
import iso8601

from xbmc import log as xbmc_log

from .util import *
from .conversions import convert_datetime,WIND_DIR

from simpleplugin import translate_path

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonversion__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon')
__addonid__ = __addon__.getAddonInfo('id')

# get settings...
ha_key = __addon__.getSettingString('ha_key')
ha_server = __addon__.getSettingString('ha_server')
ha_weather_url = __addon__.getSettingString('ha_weather_url')
ha_weather_url_data = __addon__.getSettingString('ha_weather_url_data')
ha_weather_daily_url = __addon__.getSettingString('ha_weather_daily_url')
ha_weather_daily_url_data = __addon__.getSettingString('ha_weather_daily_url_data')
# ... and fix them if necessary
if ha_server and ha_server.endswith('/'):
    ha_server = ha_server[:-1]
if ha_weather_url and (not ha_weather_url.startswith('/')):
    ha_weather_url = '/' + ha_weather_url
if ha_weather_daily_url and (not ha_weather_daily_url.startswith('/')):
    ha_weather_daily_url = '/' + ha_weather_daily_url
ha_api_base = ha_server + '/api'
settings_provided = ha_key and ha_server and ha_weather_url and ha_weather_daily_url

headers = {'Authorization': 'Bearer ' + ha_key, 'Content-Type': 'application/json'}

WND = None

class MAIN():
    def __init__(self, *args, **kwargs):
        log('Home Assistant Weather started.')
        #self.MONITOR = MyMonitor()
        mode = kwargs['mode']
        global WND, settings_provided
        WND = kwargs['w']
        self.settings_provided = settings_provided
        if not self.settings_provided:
            show_dialog(__addon__.getLocalizedString(30010))
            log('Settings for Home Assistant Weather not yet provided. Plugin will not work.')
        else:
            #Test connection / get version
            response = self.getRequest('/config')
            if response is not None:
                log('Response from server: ' + str(response.content))
                self.getForecasts()
                #parsedResponse = json.loads(response.text)
            else:
                log('Response from server is NONE!')
                show_dialog('Response from server is NONE!')
                self.clearProps()
        log('Home Assistant Weather init finished.')

    def getRequest(self, api_ext):
        global headers, ha_server
        try:
            log('Trying to make a get request to ' + ha_server + api_ext)
            r = requests.get(ha_server + api_ext, headers=headers)
            log('GetRequest status code is: ' + str(r.status_code))
            if r.status_code == 401:
                show_dialog(__addon__.getLocalizedString(30011)) #Error 401: Check your token
            elif r.status_code == 405:
                show_dialog(__addon__.getLocalizedString(30012)) #Error 405: Method not allowed
            elif r.status_code == 200:
                return r
        except:
            log('Status code error is: ' + str(r.raise_for_status()))
            show_dialog(__addon__.getLocalizedString(30013)) #Unknown error: Check IP address or if server is online

    def postRequest(self, api_ext, payload):
        global headers, ha_server
        try:
            log('Trying to make a post request to ' + ha_server + api_ext + ' with payload: ' + payload)
            r = requests.post(ha_server + api_ext, headers=headers, data=payload)
            log('GetRequest status code is: ' + str(r.status_code))
            if r.status_code == 401:
                show_dialog(__addon__.getLocalizedString(30011)) #Error 401: Check your token
            elif r.status_code == 405:
                show_dialog(__addon__.getLocalizedString(30012)) #Error 405: Method not allowed
            else:
                return r
        except:
            show_dialog(__addon__.getLocalizedString(30013)) #Unknown error: Check IP address or if server is online

    def getForecasts(self):
        global ha_weather_url, ha_weather_daily_url, ha_server, ha_key
        log('Getting forecasts from Home Assistant server.')
        response = self.getRequest(ha_weather_url)
        if response is not None:
            log('Response (weather) from server: ' + str(response.content))
            try:
                parsedResponse = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
                raise Exception('Got incorrect response from Home Assistant Weather server (request was to ' + ha_weather_url + ' with data: ' + ha_weather_url_data + ') and response received: ' + response.text)
            if parsedResponse.get('attributes') is not None:
                loc = "Home Assistant"
                forecast = parsedResponse['attributes']
                #set_property('Location'              , loc, WND)
                set_property('Location1'             , loc, WND)
                set_property('Locations'             , '1', WND)
                set_property('ForecastLocation'      , loc, WND)
                set_property('RegionalLocation'      , loc, WND)
                set_property('Updated'               , parsedResponse['last_updated'], WND)
                set_property('Current.Location'      , loc, WND)
                set_property('Current.Condition'     , str(parsedResponse['state']), WND)
                set_property('Current.Temperature'   , str(forecast['temperature']), WND)
                set_property('Current.UVIndex'       , '0', WND)
                set_property('Current.OutlookIcon'   , '%s.png' % get_condition_code_by_name(parsedResponse['state']), WND)
                set_property('Current.FanartCode'    , get_condition_code_by_name(parsedResponse['state']), WND)
                set_property('Current.Wind'          , str(3.6*forecast['wind_speed']), WND)
                set_property('Current.WindDirection' , xbmc.getLocalizedString(WIND_DIR(forecast['wind_bearing'])), WND)
                set_property('Current.Humidity'      , str(forecast['humidity']), WND)
                set_property('Current.DewPoint'      , str(forecast['dew_point']), WND)
                set_property('Current.FeelsLike'     , str(forecast['temperature']), WND)
                set_property('Current.Pressure'      , str(forecast['pressure']), WND)
                set_property('Current.IsFetched'     , 'true', WND)
                set_property('Forecast.City'         , loc, WND)
                set_property('Forecast.Country'      , loc, WND)
                set_property('Forecast.Latitude'     , '0', WND)
                set_property('Forecast.Longitude'    , '0', WND)
                set_property('Forecast.IsFetched'    , 'true', WND)
                set_property('Forecast.Updated'      , parsedResponse['last_updated'], WND)
                set_property('WeatherProvider'       , 'Home Assistant Weather', WND)
                set_property('WeatherProviderLogo'   , translate_path(os.path.join('weather.ha', 'resources', 'banner.png')), WND)
                set_property('Hourly.IsFetched'      , '', WND)
            else:
                log('The response dict from get_forecast url does not contain forecast key. This is unexpected.')
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
        else:
            log('Response (weather hourly) from server is NONE!')
            show_dialog('Response (weather hourly) from server is NONE!')
            self.clearProps()
        response = self.getRequest(ha_weather_daily_url)
        if response is not None:
            log('Response (weather daily) from server: ' + str(response.content))
            try:
                parsedResponse = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
                raise Exception('Got incorrect response from Home Assistant Weather server (request was to ' + ha_weather_daily_url + ' with data: ' + ha_weather_daily_url_data + ') and response received: ' + response.text)
            if parsedResponse.get('attributes') is not None:
                forecast = parsedResponse['attributes']
                for i in range (0, forecast['days_num']):
                    count = str(i)
                    set_property('Day'+count+'.Title'      , convert_datetime(parse_date(forecast['day'+count+'_date']),'date','weekday','long'), WND)
                    set_property('Day'+count+'.FanartCode' , get_condition_code_by_name(forecast['day'+count+'_condition']), WND)
                    set_property('Day'+count+'.Outlook'    , str(forecast['day'+count+'_condition']), WND)
                    set_property('Day'+count+'.OutlookIcon', '%s.png' % str(get_condition_code_by_name(forecast['day'+count+'_condition'])), WND)
                    set_property('Day'+count+'.HighTemp'   , str(forecast['day'+count+'_temperature']), WND)
                    set_property('Day'+count+'.LowTemp'    , str(forecast['day'+count+'_temperature_low']), WND)
                set_property('Daily.IsFetched', 'true', WND)
            else:
                log('The response dict from get_forecast url does not contain forecast key. This is unexpected.')
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
        else:
            log('Response (weather daily) from server is NONE!')
            show_dialog('Response (weather daily) from server is NONE')
            self.clearProps()

    def clearProps(self):
        set_property('Current.Condition'     , 'N/A', WND)
        set_property('Current.Temperature'   , '0', WND)
        set_property('Current.Wind'          , '0', WND)
        set_property('Current.WindDirection' , 'N/A', WND)
        set_property('Current.Humidity'      , '0', WND)
        set_property('Current.FeelsLike'     , '0', WND)
        set_property('Current.UVIndex'       , '0', WND)
        set_property('Current.DewPoint'      , '0', WND)
        set_property('Current.OutlookIcon'   , 'na.png', WND)
        set_property('Current.FanartCode'    , 'na', WND)
        for count in range (0, MAXDAYS):
            set_property('Day%i.Title'       % count, 'N/A', WND)
            set_property('Day%i.HighTemp'    % count, '0', WND)
            set_property('Day%i.LowTemp'     % count, '0', WND)
            set_property('Day%i.Outlook'     % count, 'N/A', WND)
            set_property('Day%i.OutlookIcon' % count, 'na.png', WND)
            set_property('Day%i.FanartCode'  % count, 'na', WND)


class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
