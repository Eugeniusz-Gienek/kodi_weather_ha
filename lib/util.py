import os
import sys
import socket
import requests
import _strptime
import math
import re
import codecs
import xbmc
import calendar
import time
from datetime import datetime
import iso8601

import urllib

import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
from xbmc import log as xbmc_log

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonversion__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon')
__addonid__ = __addon__.getAddonInfo('id')
LANGUAGE = __addon__.getLocalizedString

#WEATHER_WINDOW = xbmcgui.Window(12600)
WEATHER_ICON = xbmcvfs.translatePath('%s.png')
TEMPUNIT   = xbmc.getRegion('tempunit')
DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')
SPEEDUNIT = xbmc.getRegion('speedunit')
MAXDAYS = 6


def build_url(base_url, query):
    return base_url + '?' + urllib.urlencode(query)

def show_dialog(message):
    xbmcgui.Dialog().ok(__addonname__, message)


def log(txt, loglevel=xbmc.LOGDEBUG): #https://forum.kodi.tv/showthread.php?tid=196442
    if __addon__.getSetting( "logEnabled" ) == "true":
        message = u'[ HOME ASSISTANT WEATHER ]: %s: %s' % (__addonid__, txt)
        xbmc.log(msg=message, level=loglevel)

def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= datetime.timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

def parse_date(event_date):
    datetime_obj = iso8601.parse_date(event_date)
    datetime_obj = utc_to_local(datetime_obj)
    dateString = datetime_obj.strftime(xbmc.getRegion('dateshort'))
    return dateString

def parse_time(event_date):
    datetime_obj = iso8601.parse_date(event_date)
    datetime_obj = utc_to_local(datetime_obj)
    timeString = datetime_obj.strftime(xbmc.getRegion('time'))
    return timeString

def parse_dateTime(event_date):
    return parse_date(event_date) + ' ' + parse_time(event_date)

# set weather window property
def set_property(name, value, WINDOW1):
    WINDOW1.setProperty(name, value)

def get_condition_code_by_name(name):
    code_to_name_map = ['tornado',
        'tropical-storm',
        'hurricane',
        'lightning-rainy',
        'lightning',
        'snowy-rainy',
        'mixed-rain-and-sleet',
        'mixed-snow-and-sleet',
        'freezing-drizzle',
        'drizzle',
        'freezing-rain',
        'pouring',
        'rainy',
        'snow-flurries',
        'light-snow-showers',
        'blowing-snow',
        'snowy',
        'hail',
        'sleet',
        'dust',
        'fog',
        'haze',
        'smoky',
        'blustery',
        'windy',
        'cold',
        'cloudy',
        'mostly-cloudy-night',
        'mostly-cloudy-day',
        'partly-cloudy-night',
        'partly-cloudy-day',
        'clear-night',
        'sunny',
        'fair-night',
        'fair-day',
        'mixed-rain-and-hail',
        'hot',
        'isolated-thunderstorms',
        'scattered-thunderstorms',
        'scattered-thunderstorms',
        'scattered-showers',
        'heavy-snow',
        'scattered-snow-showers',
        'heavy-snow',
        'partlycloudy',
        'thundershowers',
        'snow-showers',
        'isolated-thundershowers'
    ]
    try:
        code = code_to_name_map.index(name)
    except ValueError:
        code = 'na'
    return str(code)
