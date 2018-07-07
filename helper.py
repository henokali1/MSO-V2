import datetime
import time

# Converts given date in to UNIX timestamp.


def toUnix(date):
    date = date.replace(',', '').replace(' ', ',')
    date = date.split(',')
    monthes = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
    return time.mktime(datetime.datetime(int(date[2]), monthes.index(date[1]), int(date[0])).timetuple())

# Converts given UNIX timestamp in to date.


def toDate(unixTimeStamp):
    return datetime.datetime.fromtimestamp(unixTimeStamp).strftime('%Y-%m-%d %H:%M:%S')
