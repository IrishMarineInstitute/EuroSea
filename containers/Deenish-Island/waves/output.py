from pickle import dump
from math import nan
from netCDF4 import Dataset, num2date
import numpy as np
from datetime import datetime, timedelta
from json import dumps
from log import set_logger, now
from waveSlider import waveSlider
import pytz

logger = set_logger()

def jsonize(data):
    logger.info(f'{now()} OUTPUT: Starting JSONization of data dict')
    for k, v in data.items():
        if 'safe' in k: continue
        logger.info(f'   {now()} JSON {k}')
        if isinstance(v, str): continue
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
            else:
                logger.info(f'   {now()} WARNING: Could not jsonize {k} due to {str(ERR)}')
    return data

def utc_to_local(time, tz):
    ''' Convert UTC time to local time '''

    time = datetime(time.year, time.month, time.day, time.hour, time.minute, 0, 0, pytz.UTC)
    return time.astimezone(pytz.timezone(tz))

def send_output(coast, tz, buoy, series):
    ''' Produce output PICKLE file to be sent to web app '''

    ''' Read wave forecast ''' 
    with Dataset('/data/netcdf/waves/Deenish-wave-forecast.nc', 'r') as nc:

        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)    

        # Read latitude and longitude
        latitude, longitude = nc.variables['latitude'][:], nc.variables['longitude'][:]

        # Read wave height 
        waves = nc.variables['VHM0'][:]

    # Replace masked values with NaN
    waves = waves.filled(nan)

    time = [datetime(i.year, i.month, i.day, i.hour) for i in time]
    # Convert UTC time to local time 
    time = [utc_to_local(i, tz) for i in time]

    # This is to ensure that time goes from 12AM today to 12AM in 3 days
    # Find index 'i0' of 12AM today
    today = datetime.today(); y, m, d = today.year, today.month, today.day
    for i, tiempo in enumerate(time):
        yi, mi, di, H = tiempo.year, tiempo.month, tiempo.day, tiempo.hour
        if (yi == y) and (mi == m) and (di == d) and (H==0):
            i0 = i
    
    # Find index 'i1' of 12AM in 5 days
    today = datetime.today() + timedelta(days=5); y, m, d = today.year, today.month, today.day
    for i, tiempo in enumerate(time):
        yi, mi, di, H = tiempo.year, tiempo.month, tiempo.day, tiempo.hour
        if (yi == y) and (mi == m) and (di == d) and (H==0):
            i1 = i

    # Subset
    time = time[i0 : i1 + 1]; waves = waves[i0 : i1 + 1, :, :]

    fig = waveSlider(longitude, latitude, time, waves, coast, buoy)

    RS = {
        'figure': fig,
        }

    outfile = '/data/pkl/DEENISH-WAVES.pkl'
    with open(outfile, 'wb') as f:
        dump(RS, f)

    SERIES = {
            'wave_time': [utc_to_local(i, tz) for i in series[0]], 
            'swh': series[1],
            'wave_max': round(series[2], 1),
            }

    outfile = '/data/pkl/DEENISH-WAVE-SERIES.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(SERIES), f)
