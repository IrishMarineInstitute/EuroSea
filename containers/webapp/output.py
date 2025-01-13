from datetime import datetime
import numpy as np
from json import dumps
import pandas as pd
import pytz

def jsonize(data):
    for k, v in data.items():
        if isinstance(v, str): continue
        if isinstance(v, tuple): v = v[0]
        try:
            data[k] = dumps(v) 
        except TypeError as ERR:
            if str(ERR) == 'Object of type datetime is not JSON serializable':
                value = [i.strftime('%Y-%m-%d %H:%M') for i in v]
                data[k] = dumps(value)   
            elif str(ERR) == 'Object of type ndarray is not JSON serializable':
                data[k] = dumps(v.tolist())
            elif str(ERR) == 'Object of type MaskedArray is not JSON serializable':
                data[k] = dumps(v.tolist())
    return data

def utc_to_local(time, tz):
    ''' Convert UTC time to local time '''

    time = datetime(time.year, time.month, time.day, time.hour, time.minute, 0, 0, pytz.UTC)
    return time.astimezone(pytz.timezone(tz))

def send_output(sub, boya):
    ''' Produce output PICKLE file to be sent to web app '''

    if boya == 'Campello':
        timezone = 'Europe/Madrid'
    elif boya == 'Deenish':
        timezone = 'Europe/Dublin'

    # Convert UTC time to local time 
    time = [utc_to_local(i, timezone) for i in sub.index]

    # Get time range
    t0, t1 = time[0], time[-1]

    # Determine first x-axis tick
    for i in time:
        if not i.hour and not i.minute:
            break
    tick0 = i.strftime('%Y-%m-%d')

    BUOY = {
        # Buoy time
        'time': time,
        'tick0': tick0,
        't0': t0.strftime('%Y-%m-%d %H:%M'),
        'tf': t1.strftime('%Y-%m-%d %H:%M'),
        }

    if boya == 'Campello':
        BUOY['maxTUR'] = np.nanmax(np.array(sub['tur'])) + 1

    for key, val in sub.items():
        key = key.replace(' ', '_').replace('-', '_')
        if isinstance(val, pd.Series):
            val = np.array(val)
        BUOY[key] = val

    return jsonize(BUOY)
