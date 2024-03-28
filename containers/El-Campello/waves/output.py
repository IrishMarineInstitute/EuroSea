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

def utc_to_local(time, tz):
    ''' Convert UTC time to local time '''

    time = datetime(time.year, time.month, time.day, time.hour, time.minute, 0, 0, pytz.UTC)
    return time.astimezone(pytz.timezone(tz))

def send_output(coast, tz, buoy):
    ''' Produce output PICKLE file to be sent to web app '''

    ''' Read wave forecast ''' 
    with Dataset('/data/netcdf/waves/Campello-wave-forecast.nc', 'r') as nc:

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

    outfile = '/data/pkl/CAMPELLO-WAVES.pkl'
    with open(outfile, 'wb') as f:
        dump(RS, f)
