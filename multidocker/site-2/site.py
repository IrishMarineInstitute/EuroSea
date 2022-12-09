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
   to run every ten minutes to download the in-situ data from an EuroSea 
   monitoring station. In addition, it subsets the latest data for the number
   of days specified in the configuration file (e.g. 14 days). It reads the
   local SST climatology needed to determine the occurrence of marine heat 
   waves. Regardless of whatever has been specified in the configuration file,
   directional information (e.g. oceanic currents) are subset for the last 24
   hours only. All this data is wrapped in a BUOY.pkl file that is updated
   every ten minutes, and later accessed by the WEBAPP container using a shared
   volume.  

   The files in this container are:

       config : Plain text file with important configuration options for your
                application, such as the SFTP credentials for the server where
                the .xml files with in-situ data are delivered. This information
                has been hidden here.

       crontab : A cron file to set this job to run every ten minutes.

       Deenish_Climatology.pkl : Local SST climatology data for MHW warnings.
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

       output.pt : Script that finally wraps all the in-situ data in BUOY.pkl
                   and in a format that can be understood by the website.

       requirements.txt : Python packages needed to run this container.

       site.py : This script. It is the main file calling the other methods.

       vectors.py : Script subsetting directional information for the last 24
                    hours and calculating water displacements.

'''

from datetime import datetime, timedelta
from output import send_output
from pytz import timezone
import numpy as np
import pickle
from buoy import Buoy
from log import set_logger, now
import vectors
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
    
    # List of available times in the buoy dataset
    time = np.array(buoy['time'])
    
    # Find appropriate time indexes
    i0, i1 = np.argmin(abs(time - t0)), np.argmin(abs(time - t1)) + 1
    
    sub = {'time': buoy['time'][i0 : i1]}
    for i in buoy.keys():        
        # Subset each parameter for the requested time period
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
        t1 = timezone('UTC').localize(date)
        NDAYS = int(config['ndays'])
        t0 = t1 - timedelta(days=NDAYS)
        t0str, t1str = t0.strftime('%Y-%m-%d %H:%M'), t1.strftime('%Y-%m-%d %H:%M')
        logger.info(f'{now()} Subsetting from {t0str} to {t1str}...')
        sub = subset(var, t0, t1)

        ''' Read climatology '''
        f = config['clim_site']
        logger.info(f'{now()} Retrieving local climatology from file {f}')
        clim = site_climatology(f, sub['time'])

        ''' Vectors '''
        vector =    {'Surface currents'   : 'surf',
                     'Mid-water currents' : 'midw',
                     'Seabed currents'    : 'seab',
                     'Winds'              : 'winds'}
        
        D = {}
        
        for i in vector.keys():
            # Get vector data  
            sub, u, v, t = vectors.vector_request(sub, i) 
            # Get displacements
            logger.info(f'{now()} Calculating displacements from {i}')
            D[vector[i] + '-x'], D[vector[i] + '-y'] = vectors.get_displacements(u, v, t, i)

        send_output(sub, D, clim, t)        
            
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
