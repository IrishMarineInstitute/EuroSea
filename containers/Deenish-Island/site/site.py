''' 
    
(C) Copyright EuroSea H2020 project under Grant No. 862626. All rights reserved.

 Copyright notice
   --------------------------------------------------------------------
   Copyright (C) 2022 Marine Institute
       Diego Pereiro Rodriguez

       diego.pereiro@marine.ie

   This library is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this library.  If not, see <http://www.gnu.org/licenses/>.
   --------------------------------------------------------------------

'''

from datetime import datetime, timedelta
from output import send_output
from pytz import timezone as tz
import numpy as np
import pickle
from wind_rose import wind_rose
from buoy import Buoy
from log import set_logger, now
import os

logger = set_logger()

def configuration():
    ''' Read secrets (configuration) file '''
    config = {}
    with open('config', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save as environment variable
            config[key] = val
    return config

def subset(buoy, t0, t1):
    ''' Subset buoy data for the requested time period '''
    
    time = buoy.index 
  
    i0, i1 = np.argmin(abs(time - t0)), np.argmin(abs(time - t1)) + 1
    
    sub = buoy[i0 : i1]

    return sub

def site_climatology(infile, time):
    ''' Reads site climatology from local PICKLE file '''
    
    with open(infile, 'rb') as f:
        clim = pickle.load(f)
    
    t0, t1 = time[0] - timedelta(days=1), time[-1] + timedelta(days=8)
    
    time = []
    while t0 < t1:
        time.append(t0); t0 += timedelta(minutes=10)
    # Data from local climatology file    
    day_of_year, seasonal_cycle, PC90 = clim['time'], clim['seas'], clim['pc90']
    
    # Output initialization
    Time, Seas, Pc90 = [], [], []
    
    for t in time:        
        H, M = t.hour, t.minute            
        if H == 12 and not M:
            # Get day of year
            Day_Of_Year = t.timetuple().tm_yday
            # Find time index in local climatology file
            i = np.where(day_of_year == Day_Of_Year)[0][0]
            # Append to output arrays
            Time.append(t)
            Seas.append(seasonal_cycle[i])
            Pc90.append(PC90[i])
    
    return Time, Seas, Pc90

def prepare_wind_rose(r, D):
    
    r, D = np.array(r), np.array(D)

    return np.vstack((r, D)).T

def windrose(sub, level='surface'):
    ''' Create wind rose figure and associated time series '''
    series = dict(time=sub.index,
            speed=sub.get(f's-{level}'),
            direction=sub.get(f'd-{level}'))

    # Subset for the last 24 hours
    time, r, D = sub.index[-144::], sub.get(f's-{level}')[-144::], sub.get(f'd-{level}')[-144::]
    # Create figure
    idate, edate, wind_rose_fig = wind_rose(time, prepare_wind_rose(r, D), 'currents')
    # Fix legend
    wind_rose_fig = wind_rose_fig.replace("strength", "speed")
    # Wrap 
    fig = {'idate': idate, 'edate': edate, 'fig': wind_rose_fig}

    return series, fig


def SITE(date=datetime.now()):
    
    root = os.path.abspath('.')
    
    try:
        
        try:
            config = configuration()
        except FileNotFoundError:
            raise FileNotFoundError(f'config file not found at root directory {root}')
                
        logger.info(f'{now()} Loading buoy data...')
        var = Buoy(config)
    
        # Subset for the latest NDAYS as per config file 
        t1 = tz('UTC').localize(date)
        NDAYS = int(config['ndays'])
        t0 = t1 - timedelta(days=NDAYS)
    
        logger.info(f'{now()} Subsetting...')
        sub = subset(var, t0, t1)

        # Read climatology 
        logger.info(f'{now()} Reading climatology...')
        clim = site_climatology(config.get('clim_site'), sub.index)

        # Make wind rose histogram for surface currents
        surface_series, surface_fig = windrose(sub)

        # Make wind rose histogram for seabed currents
        seabed_series, seabed_fig = windrose(sub, level='seabed')

        # Get time zone
        timezone = config.get('timezone')
                
        logger.info(f'{now()} SEND OUTPUT...')
        # Export output as pickle file
        send_output(sub, clim, surface_series, surface_fig, seabed_series, seabed_fig, timezone)
            
        logger.info(f'{now()} FINISHED')

        return 0, ''
       
    except Exception as err:
        
        return -1, str(err)

if __name__ == '__main__':

    my_date = datetime.utcnow()
    my_datestr = my_date.strftime('%d-%b-%Y %H:%M')
    logger.info(f'{now()} Starting site operations for date {my_datestr}')
    status, err = SITE(date=my_date)
    if status:
        logger.exception(f'Exception in SITE: {err}')
