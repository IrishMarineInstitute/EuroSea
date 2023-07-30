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

      This is the main script of the SITE container. This application is set
   to run every ten minutes to download the in-situ data from the EuroSea 
   monitoring station at El Campello. In addition, it subsets the latest data
   for the number of days specified in the configuration file. It reads the
   local SST climatology needed to determine the occurrence of marine heat 
   waves. All this data is wrapped in a BUOY.pkl file that is updated
   every ten minutes, and later accessed by the WEBAPP container through
   the shared volume. 

   The files in this container are:

       config : Plain text file with important configuration options for your
                application, such as the SFTP credentials for the server where
                the .xml files with in-situ data are delivered. This information
                has been hidden here.

       crontab : A cron file to set this job to run every ten minutes.

       Campello_Climatology.pkl : Local SST climatology data for MHW warnings.
                                 The name of this file must be set in config.

       known_hosts : A known_hosts file with the ECDSA key of the SFTP server
                     for secure connection. This file has not been included in
                     the repository but it is required for establishin a secure
                     connection with the SFTP server delivering .xml files.

       buoy.py : Python script downloading .xml files with in-situ data, and
                 applying a first quality control procedure. It produces a 
                 file with all the historical data delivered by the monitoring
                 station so far. This file is updated every ten minutes.  

       log.py : Logging script. Useful messages are sent to a file /log/app.log

       output.pt : Script that wraps all the in-situ data in BUOY.pkl
                   and in a format that can be understood by the website.

       requirements.txt : Python packages needed to run this container.

       site.py : This script. It is the main file calling the other methods.

       wind_rose.py : Script producing wind rose figures for directional 
                      data: waves, currents and winds.

'''

from datetime import datetime, timedelta
from output import send_output
from pytz import timezone as tz
import numpy as np
import pickle
from get_uv import get_uv
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
    
    logger.info(f'{now()} Getting list of available times in the buoy dataset...')
    time = np.array(buoy['time'])
  
    logger.info(f'{now()} Finding start and end time indexes...')
    i0, i1 = np.argmin(abs(time - t0)), np.argmin(abs(time - t1)) + 1
    
    logger.info(f'{now()} Subsetting time...')
    sub = {'time': buoy['time'][i0 : i1]}

    logger.info(f'{now()} Subsetting each variable for the requested time period...')
    for i in buoy.keys():        
        logger.info(f'   {now()} ... subsetting {i}')

        sub[i] = buoy[i][i0 : i1]
        
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

def SITE(date=datetime.now()):
    
    root = os.path.abspath('.')
    
    try:
        
        logger.info(f'{now()} Reading config file...')
        try:
            config = configuration()
        except FileNotFoundError:
            raise FileNotFoundError(f'config file not found at root directory {root}')
                
        logger.info(f'{now()} Loading buoy data...')
        var = Buoy(config)
    
        ''' Subset for the latest NDAYS as per config file '''
        t1 = tz('UTC').localize(date)
        NDAYS = int(config['ndays'])
        t0 = t1 - timedelta(days=NDAYS)
        t0str, t1str = t0.strftime('%Y-%m-%d %H:%M'), t1.strftime('%Y-%m-%d %H:%M')
        logger.info(f'{now()} Subsetting from {t0str} to {t1str}...')
        sub = subset(var, t0, t1)

        ''' Wind Roses '''
        logger.info(f'{now()} Getting wind rose for last 24 hours observed wind speed and direction...')

        logger.info(f'{now()} Subset time, speed and direction for the last 24 hours...')
        time, r, D = sub['time'][-144::], sub['Wind Speed'][-144::], sub['Wind Direction'][-144::]

        logger.info(f'{now()} Creating wind rose figure for wind...')
        idate, edate, wind_rose_fig = wind_rose(time, prepare_wind_rose(r, D), 'wind')

        logger.info(f'{now()} Fix legend title ("speed" instead of "strength")')
        wind_rose_fig = wind_rose_fig.replace("strength", "speed")

        logger.info(f'{now()} Wrap into a dictionary to send to shared volume')
        wind_rose_figure = {'idate': idate, 'edate': edate, 'fig': wind_rose_fig}



        logger.info(f'{now()} Getting wind rose for last 24 hours observed wave peak period and direction...')

        logger.info(f'{now()} Wrap time series into a dictionary for CSV export') # (full, 14-day time series for CSV download)
        time, r, D = sub['time'], sub['Wave Peak Period'], sub['Wave Peak Direction']
        wave_rose_series = {'time': time, 'period': r, 'direction': D}
      
        logger.info(f'{now()} Subset time, period and direction for the last 24 hours...')
        time, r, D = sub['time'][-144::], sub['Wave Peak Period'][-144::], sub['Wave Peak Direction'][-144::]

        logger.info(f'{now()} Creating wind rose figure for waves...')
        idate, edate, wind_rose_fig = wind_rose(time, prepare_wind_rose(r, D), 'wave')

        logger.info(f'{now()} Fix legend title ("period" instead of "strength")')
        wind_rose_fig = wind_rose_fig.replace("strength", "period")

        logger.info(f'{now()} Wrap into a dictionary to send to shared volume')
        wave_rose_figure = {'idate': idate, 'edate': edate, 'fig': wind_rose_fig}



        logger.info(f'{now()} Getting wind rose for last 24 hours observed surface currents and direction...')
      
        logger.info(f'{now()} Getting surface level ADCP measurements...')
        r, D = [i[0] for i in sub['DCP speed']], [j[0] for j in sub['DCP dir']]

        logger.info(f'{now()} Wrap time series into a dictionary for CSV export')
        DCP_rose_series_surface = dict(time = sub['time'], speed = r, direction = D)

        logger.info(f'{now()} Subset time, speed and direction for the last 24 hours...')
        time, r, D = sub['time'][-144::], r[-144::], D[-144::]

        logger.info(f'{now()} Creating wind rose figure for ADCP surface...')
        logger.info(f'{now()} Length of "r" is {len(r)}')
        logger.info(f'{now()} Length of "D" is {len(D)}')
        idate, edate, wind_rose_fig = wind_rose(time, prepare_wind_rose(r, D), 'currents')

        logger.info(f'{now()} Fix legend title ("speed" instead of "strength")')
        wind_rose_fig = wind_rose_fig.replace("strength", "speed")

        logger.info(f'{now()} Wrap into a dictionary to send to shared volume')
        DCP_rose_figure_surface = {'idate': idate, 'edate': edate, 'fig': wind_rose_fig}


        logger.info(f'{now()} Getting wind rose for last 24 hours observed 15-meter depth currents and direction...')

        logger.info(f'{now()} Getting 15-meter depth ADCP measurements...')
        r, D = [i[11] for i in sub['DCP speed']], [j[11] for j in sub['DCP dir']] # Users requested 15-meter depth instead of seabed

        logger.info(f'{now()} Wrap time series into a dictionary for CSV export')
        DCP_rose_series_seabed = dict(time = sub['time'], speed = r, direction = D)
      
        logger.info(f'{now()} Subset time, speed and direction for the last 24 hours...')
        time, r, D = sub['time'][-144::], r[-144::], D[-144::]

        logger.info(f'{now()} Creating wind rose figure for ADCP seabed...')
        idate, edate, wind_rose_fig = wind_rose(time, prepare_wind_rose(r, D), 'currents')

        logger.info(f'{now()} Fix legend title ("speed" instead of "strength")')
        wind_rose_fig = wind_rose_fig.replace("strength", "speed")

        logger.info(f'{now()} Wrap into a dictionary to send to shared volume')
        DCP_rose_figure_seabed = {'idate': idate, 'edate': edate, 'fig': wind_rose_fig}



        ''' Read climatology '''
        f = config['clim_site']
        logger.info(f'{now()} Retrieving local climatology from file {f}')
        clim = site_climatology(f, sub['time'])

        ''' DCPS depths from configuration file '''
        DCPS = config['DCPS']

        ''' Add wind series for time series plot (subset every 3 hours) (23/06/2023) '''
        sub['time_3h_series']       = sub['time'][0::18]
        sub['wind_speed_3h_series'] = sub['Wind Speed'][0::18] 
        sub['wind_direction_3h_series'] = sub['Wind Direction'][0::18]
        sub['u-wind_3h_series'], sub['v-wind_3h_series'] = get_uv(sub['wind_speed_3h_series'], sub['wind_direction_3h_series'], 'FROM')

        # Get time zone
        timezone = config['timezone']
                
        logger.info(f'{now()} SEND OUTPUT...')
        send_output(sub, clim, DCPS, wind_rose_figure, wave_rose_figure, wave_rose_series,       
            DCP_rose_figure_surface, DCP_rose_figure_seabed, DCP_rose_series_surface, DCP_rose_series_seabed,
            timezone)
            
        return 0, ''

       
    except Exception as err:
        
        return -1, str(err)

if __name__ == '__main__':

    delay = 0 # days
    my_date = datetime.now() - timedelta(days=delay)
    my_datestr = my_date.strftime('%d-%b-%Y %H:%M')
    logger.info(f'{now()} Starting site operations for date {my_datestr}')
    status, err = SITE(date=my_date)
    if status:
        logger.exception(f'Exception in SITE: {err}')
