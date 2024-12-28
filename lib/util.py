import calendar
import time
from abc import abstractmethod
from datetime import datetime, timedelta

import iso8601
import xbmc
import xbmcaddon
import xbmcvfs

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonversion__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon')
__addonid__ = __addon__.getAddonInfo('id')
LANGUAGE = __addon__.getLocalizedString

# WEATHER_WINDOW = xbmcgui.Window(12600)
WEATHER_ICON = xbmcvfs.translatePath('%s.png')
TEMPUNIT = xbmc.getRegion('tempunit')
DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')
SPEEDUNIT = xbmc.getRegion('speedunit')
MAXDAYS = 6








def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def parse_date(event_date):
    datetime_obj = iso8601.parse_date(event_date)
    datetime_obj = utc_to_local(datetime_obj)
    return datetime_obj.strftime(xbmc.getRegion('dateshort'))


def parse_time(event_date):
    datetime_obj = iso8601.parse_date(event_date)
    datetime_obj = utc_to_local(datetime_obj)
    return datetime_obj.strftime(xbmc.getRegion('time'))


def parse_datetime(event_date):
    return parse_date(event_date) + ' ' + parse_time(event_date)


def get_condition_code_by_name(name, is_num=False):
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
        code = -1 if is_num else 'na'
    return str(code)





# convert month numbers to short names (01 = jan)
MONTH_NAME_SHORT = {'01': 51,
                    '02': 52,
                    '03': 53,
                    '04': 54,
                    '05': 55,
                    '06': 56,
                    '07': 57,
                    '08': 58,
                    '09': 59,
                    '10': 60,
                    '11': 61,
                    '12': 62}
# convert month numbers to names (01 = januari)
MONTH_NAME_LONG = {'01': 21,
                   '02': 22,
                   '03': 23,
                   '04': 24,
                   '05': 25,
                   '06': 26,
                   '07': 27,
                   '08': 28,
                   '09': 29,
                   '10': 30,
                   '11': 31,
                   '12': 32}

# convert day numbers to names (0 = sunday)
WEEK_DAY_LONG = {'0': 17,
                 '1': 11,
                 '2': 12,
                 '3': 13,
                 '4': 14,
                 '5': 15,
                 '6': 16}

# convert day numbers to short names (0 = sun)
WEEK_DAY_SHORT = {'0': 47,
                  '1': 41,
                  '2': 42,
                  '3': 43,
                  '4': 44,
                  '5': 45,
                  '6': 46}


# Source: https://github.com/xbmc/repo-scripts/blob/krypton/weather.yahoo/default.py
# convert timestamp to localized time and date
# stamp (input value): either datetime (2020-02-28T22:00:00.000Z), timestamp (1582871381) or daynumber (1)
# inpt (input format) either 'datetime', 'timestamp', 'seconds' (after midnight) or 'day'
# outpt (return value) time+date, month+day, weekday, time
# form (output format) either long or short names 
def convert_datetime(stamp, inpt, outpt, form):
    if inpt == 'date':
        timestruct = time.strptime(stamp, "%d.%m.%Y")
    elif inpt == 'datetime':
        timestruct = time.strptime(stamp, "%Y-%m-%dT%H:%M:%S%z")
    elif inpt == 'timestamp':
        timestruct = time.localtime(stamp)
    elif inpt == 'seconds':
        m, s = divmod(stamp, 60)
        h, m = divmod(m, 60)
        hm = "%02d:%02d" % (h, m)
        timestruct = time.strptime(hm, "%H:%M")
    if outpt == 'timedate':
        if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
            localdate = time.strftime('%d-%m-%Y', timestruct)
        elif DATEFORMAT[1] == 'm' or DATEFORMAT[0] == 'M':
            localdate = time.strftime('%m-%d-%Y', timestruct)
        else:
            localdate = time.strftime('%Y-%m-%d', timestruct)
        if TIMEFORMAT != '/':
            localtime = time.strftime('%I:%M %p', timestruct)
        else:
            localtime = time.strftime('%H:%M', timestruct)
        label = localtime + '  ' + localdate
    elif outpt == 'monthday':
        month = time.strftime('%m', timestruct)
        day = time.strftime('%d', timestruct)
        if form == 'short':
            if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
                label = day + ' ' + xbmc.getLocalizedString(MONTH_NAME_SHORT[month])
            else:
                label = xbmc.getLocalizedString(MONTH_NAME_SHORT[month]) + ' ' + day
        elif form == 'long':
            if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
                label = day + ' ' + xbmc.getLocalizedString(MONTH_NAME_LONG[month])
            else:
                label = xbmc.getLocalizedString(MONTH_NAME_LONG[month]) + ' ' + day
    elif outpt == 'weekday':
        if inpt == 'day':
            weekday = str(stamp)
        else:
            weekday = time.strftime('%w', timestruct)
        if form == 'short':
            label = xbmc.getLocalizedString(WEEK_DAY_SHORT[weekday])
        elif form == 'long':
            label = xbmc.getLocalizedString(WEEK_DAY_LONG[weekday])
    elif outpt == 'time':
        if TIMEFORMAT != '/':
            label = time.strftime('%I:%M %p', timestruct)
        else:
            label = time.strftime('%H:%M', timestruct)
    return label


# Source: https://github.com/xbmc/repo-scripts/blob/krypton/weather.yahoo/default.py
def convert_seconds(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    hm = "%02d:%02d" % (h, m)
    if TIMEFORMAT != '/':
        timestruct = time.strptime(hm, "%H:%M")
        hm = time.strftime('%I:%M %p', timestruct)
    return hm


def fix_condition_translation_codes(s):
    if s == 'rainy':
        s = 'rain'
    elif s == 'partlycloudy':
        s = 'partly cloudy'
    elif s == 'snowy-rainy':
        s = 'snow and rain'
    elif s == 'lightning-rainy':
        s = 'thundershowers'
    elif s == 'clear-night':
        s = 'clear'
    elif s == 'snowy':
        s = 'snow'
    elif s == 'pouring':
        s = 'showers'
    return s
