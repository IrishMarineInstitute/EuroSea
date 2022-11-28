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

      This is the main script of the MODEL container. This application is set
   to run once a day to download the model forecasts and temperature profile
   from CMEMS. This data is wrapped in a MODEL.pkl file that is updated daily,
   and later accessed by the WEBAPP container using a shared volume.

   The files in this container are:

       config : Plain text file with important configuration options for your
                application, such as the CMEMS credentials and products to 
                download as forecasts.

       crontab : A cron file to set this job to run once a day.

       log.py : Logging script. Useful messages are sent to a file /log/app.log

       model.py : This script. It is the main file calling the other methods.

       motu.py : Script using the motuclient to download CMEMS data.

       output.pt : Script that finally wraps all the model data in MODEL.pkl
                   and in a format that can be understood by the website.

       requirements.txt : Python packages needed to run this container.

'''

from datetime import datetime, timedelta
from pytz import timezone
from output import send_output
import numpy as np
from netCDF4 import Dataset, num2date
from motu import motu
from glob import glob
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

def read_cmems(f, variable):
    ''' Read CMEMS forecast '''
    
    with Dataset(f) as nc:
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        fc = np.squeeze(nc.variables[variable][:])
    time = [datetime(i.year, i.month, i.day, i.hour) for i in time]
    return time, fc

def MODEL(date=datetime.now()):
    
    root = os.path.abspath('.')
    
    try:
        
        logger.info(f'{now()} Reading config file...')
        try:
            config = configuration()
        except FileNotFoundError:
            raise FileNotFoundError(f'config file not found at root directory {root}')

        # Subset for the latest NDAYS as per config file 
        t1 = timezone('UTC').localize(date)
        NDAYS = int(config['ndays'])
        t0 = t1 - timedelta(days=NDAYS)
        tf = t1 + timedelta(hours=132) # 5-day forecast

        logger.info(f'{now()} Getting CMEMS credentials from config...')
        USER, PSWD = config['USERNAME'], config['PASSWORD']
        logger.info(f'{now()} Username is {USER}, password is {PSWD}')
        
        # Site coordinates
        logger.info(f'{now()} Getting site longitude and latitude from config...')
        lon, lat = float(config['lon']), float(config['lat'])
        logger.info(f'{now()} Coordinates are {str(lat)}, {str(lon)}')
        
        # Dictionary to save forecasts
        FC = {}
        
        # CMEMS PHYSICS PRODUCT
        PRODUCT = config['phy']; logger.info(f'{now()} CMEMS PHYSICS from {PRODUCT}')
        # Download path
        localpath = '/netcdf'    
        
        ''' Download seawater temperature forecast '''      
        # CMEMS SERVICE
        SERVICE = config['sst']
        # Download NetCDF
        for i in range(5):
            logger.info(f'{now()} Trial {i} to download local temperature forecast')
            f = motu(USER, PSWD, PRODUCT, SERVICE, localpath, 'SST-forecast.nc', 
                 lon - 1e-6, lon + 1e-6, 
                 lat - 1e-6, lat + 1e-6, 
                 t1, tf, 'thetao', 'nrt')
            if os.path.isfile(f): 
                logger.info(f'{now()}   Successfully downloaded file {f}'); break
            else:
                logger.info(f'{now()}   Download failed!'); continue
        if os.path.isfile(f):
            logger.info(f'{now()} Reading local temperature forecast...') 
            # Read NetCDF and save to forecast dictionary
            time, fc = read_cmems(f, 'thetao'); FC['sst'] = (time, fc)    
        else:
            logger.info(f'{now()} Unable to download temperature forecast!')
            FC['sst'] = (np.nan, np.nan)
        
        ''' Download seawater salinity forecast '''
        # CMEMS SERVICE
        SERVICE = config['sss']
        # Download NetCDF
        for i in range(5):
            logger.info(f'{now()} Trial {i} to download local salinity forecast')
            f = motu(USER, PSWD, PRODUCT, SERVICE, localpath, 'SSS-forecast.nc', 
                 lon - 1e-6, lon + 1e-6, 
                 lat - 1e-6, lat + 1e-6, 
                 t1, tf, 'so', 'nrt')
            if os.path.isfile(f): 
                logger.info(f'{now()}   Successfully downloaded file {f}'); break
            else:
                logger.info(f'{now()}   Download failed!'); continue
        if os.path.isfile(f):
            logger.info(f'{now()} Reading local salinity forecast...') 
            # Read NetCDF and save to forecast dictionary
            time, fc = read_cmems(f, 'so'); FC['sss'] = (time, fc)  
        else:
            logger.info(f'{now()} Unable to download salinity forecast!')
            FC['sss'] = (np.nan, np.nan)

        ''' Download temperature profile (operational) '''
        # CMEMS SERVICE
        SERVICE = config['temp3d']
        # Download NetCDF
        for i in range(5):
            logger.info(f'{now()} Trial {i} to download temperature profile')
            f = motu(USER, PSWD, PRODUCT, SERVICE, localpath, 'TEMP3D-profile.nc',
                 lon - 1e-6, lon + 1e-6,
                 lat - 1e-6, lat + 1e-6,
                 t0, tf, 'thetao', 'nrt', zmin=0, zmax=30) 
            if os.path.isfile(f): 
                logger.info(f'{now()}   Successfully downloaded file {f}'); break
            else:
                logger.info(f'{now()}   Download failed!'); continue
        if os.path.isfile(f):
            logger.info(f'{now()} Reading temperature profile...') 
            # Read NetCDF and save to forecast dictionary
            time, fc = read_cmems(f, 'thetao'); FC['temp3d'] = (time, fc)  
        else:
            logger.info(f'{now()} Unable to download temperature profile!')
            FC['temp3d'] = (np.nan, np.nan)

        send_output(FC)        

        ''' Download temperature profile (history) '''
        # CMEMS SERVICE
        SERVICE = config['temp3d']
        # Start date to download temperature profiles
        datestart = config['datestart']
        time = datetime.strptime(datestart, '%Y-%m-%d')
        # Get list of currently available TEMP3d files
        lista = glob('/data/pkl/TEMP3D-*.nc')
       
        while time <= date: 
            filename = f'/data/pkl/TEMP3D-{time.strftime("%Y%m%d")}.nc'
            if not os.path.isfile(filename):
                logger.info(f'{now()} Downloading profile for {time.strftime("%Y%m%d")}')
                # Download NetCDF
                for i in range(5):
                    logger.info(f'{now()} Trial {i} to download temperature profile')
                    f = motu(USER, PSWD, PRODUCT, SERVICE, '/data/pkl/', 
                        f'TEMP3D-{time.strftime("%Y%m%d")}.nc',
                        lon - 1e-6, lon + 1e-6,
                        lat - 1e-6, lat + 1e-6,
                        time, time+timedelta(hours=23), 'thetao', 'nrt', zmin=0, zmax=30) 
                    if os.path.isfile(f): 
                        logger.info(f'{now()}   Successfully downloaded file {f}'); break
                    else:
                        logger.info(f'{now()}   Download failed!'); continue
            time += timedelta(days=1)
            
        return 0, ''
       
    except Exception as err:
        
        return -1, str(err)

if __name__ == '__main__':

    delay = 0 # days
    my_date = datetime.now() - timedelta(days=delay)
    my_datestr = my_date.strftime('%d-%b-%Y %H:%M')
    logger.info(f'{now()} Starting site operations for date {my_datestr}')
    status, err = MODEL(date=my_date)
    if status:
        logger.exception(f'Exception in RS: {err}')
