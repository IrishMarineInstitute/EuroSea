''' 
    
(C) Copyright EuroSea H2020 project under Grant No. 862626. All rights reserved.

 Copyright notice
   --------------------------------------------------------------------
   Copyright (C) 2022 Marine Institute
       Diego Pereiro Rodriguez, Oleg Belyaev Korolev

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

      This is the main script of the RS container. This application is set
   to run once a day to download the Remote Sensing products, namely SST and
   chlorophyll. SST anomalies, Marine Heat Waves and chlorophyll anomalies 
   are determined. This data is wrapped in an RS.pkl file updated daily and
   later accessed by the WEBAPP container using a shared volume.

   The files in this container are:

       config : Plain text file with important configuration options for your
                application, such as the CMEMS credentials and products to 
                download as remote-sensing data or the geographical boundaries
                of your area of interest.

       crontab : A cron file to set this job to run once a day.

       coastline-1.pkl : Coastline file to draw the shoreline in maps. You
                         should produce a new one for your application
                         using the same format.
 
       MUR-Climatology.nc : A spatial (2-D) SST climatology for calculation of
                            SST anomalies and for determining the occurrence of
                            Marine Heat Waves. This is a heavy NetCDF file that
                            has to be produced for your application and is not
                            available on GitHub. Details on how to produce it
                            can be read in the User's Manual. 
                            
       log.py : Logging script. Useful messages are sent to a file /log/app.log

       mhw.py : Script to detect Marine Heat Wave occurrence in SST data.

       motu.py : Script using the motuclient to download CMEMS data.

       oceancolour.py : Script downloading chlorophyll data and calculating 
                        anomalies. 

       output.pt : Script that finally wraps all the model data in MODEL.pkl
                   and in a format that can be understood by the website.

       requirements.txt : Python packages needed to run this container.

       rs.py : This script. It is the main file calling the other methods.

       SST.py : Script downloading SST data and calculating anomalies.

'''

from datetime import datetime, timedelta
from oceancolour import oceancolour, get_boundaries
from output import send_output
import numpy as np
from netCDF4 import Dataset
from SST import SST
from pickle import load
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

def climatology(file):
    ''' Read climatology from NetCDF file '''
       
    with Dataset(file, 'r') as nc:
        # Read longitude
        lon = nc.variables['longitude'][:]
        # Read latitude
        lat = nc.variables['latitude'][:]
        # Read time
        time = nc.variables['time'][:]
        # Read seasonal cycle (climatology)
        seas = nc.variables['seas'][:]
        # Read 90-th percentile (MHW threshold)
        pc90 = nc.variables['thresh'][:]

    return lon, lat, time, seas, pc90

def RS(date=datetime.now()):
    
    root = os.path.abspath('.')
    
    try:
        
        logger.info(f'{now()} Reading config file...')
        try:
            config = configuration()
        except FileNotFoundError:
            raise FileNotFoundError(f'config file not found at root directory {root}')

        
        # Read coastline
        logger.info(f'{now()} Reading coastline...')
        with open(config['coastfile'], 'rb') as f:
            coast = load(f)

        # Read climatology
        f = config['clim']
        logger.info(f'{now()} Retrieving climatology from file {f}')
        clim = climatology(f)
        lon_c, lat_c, time_c, seas, pc90 = clim

        # SST
        logger.info(f'{now()} Getting SST...')
        boundaries = get_boundaries(config)
        sst_out = SST(time_c, seas, pc90, date.strftime('%Y-%m-%d'), boundaries)

        # Oceancolour
        logger.info(f'{now()} Downloading oceancolour...')
        colour = oceancolour(date, config)

        # Site coordinates
        logger.info(f'{now()} Getting site longitude and latitude from config...')
        lon, lat = float(config['lon']), float(config['lat'])
        logger.info(f'{now()} Coordinates are {str(lat)}, {str(lon)}')
        
        send_output(lon, lat, sst_out, colour, coast)        
            
        return 0, ''

       
    except Exception as err:
        
        return -1, str(err)

if __name__ == '__main__':

    delay = 1 # days
    my_date = datetime.now() - timedelta(days=delay)
    my_datestr = my_date.strftime('%d-%b-%Y %H:%M')
    logger.info(f'{now()} Starting site operations for date {my_datestr}')
    status, err = RS(date=my_date)
    if status:
        logger.exception(f'Exception in RS: {err}')
