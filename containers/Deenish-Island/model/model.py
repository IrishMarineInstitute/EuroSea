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

import copernicusmarine as cm
from datetime import datetime, timedelta
from pytz import timezone
from output import send_output
import numpy as np
from netCDF4 import Dataset, num2date
from glob import glob
import os

from log import set_logger, now
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
        tf = t1 + timedelta(days=5) # 5-day forecast

        USER, PSWD = config['USERNAME'], config['PASSWORD']
        
        # Site coordinates
        lon, lat = float(config['lon']), float(config['lat'])
        
        # Dictionary to save forecasts
        FC = {}
        
        # Download path
        localpath = '/data/netcdf/model/Deenish-Island/'    
        if not os.path.isdir(localpath):
            os.makedirs(localpath)

        if os.path.isfile(localpath + 'SST-forecast.nc'):
            os.remove(localpath + 'SST-forecast.nc')
        f = localpath + 'SST-forecast.nc'

        
        ''' Download seawater temperature forecast '''      
        # CMEMS SERVICE
        dataset, version = config['dataset-id'], config['version']
        # Download NetCDF
        for i in range(5):
            logger.info(f'{now()} Trial {i} to download local temperature forecast')
            cm.subset(
                    username=USER, password=PSWD, 
                    dataset_id=dataset, dataset_version=version,
                    output_directory=localpath, output_filename='SST-forecast.nc',
                    variables=['thetao'], 
                    minimum_longitude=lon-1e-6,
                    maximum_longitude=lon+1e-6,
                    minimum_latitude=lat-1e-6,
                    maximum_latitude=lat+1e-6,
                    start_datetime=t1.strftime('%Y-%m-%dT%H:%M:%S'),
                    end_datetime=tf.strftime('%Y-%m-%dT%H:%M:%S'),
                    force_download=True)
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

        send_output(FC)
        
        return 0, ''
       
    except Exception as err:

        return -1, str(err)

if __name__ == '__main__':

    status, err = MODEL()
    if status:
        logger.exception(f'Exception in MODEL: {err}')
