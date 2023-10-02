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
from pytz import timezone as tz
from output import send_output
from wind_rose import wind_rose
from windArrow import windArrow, windArrowIcons
import numpy as np
from netCDF4 import Dataset, num2date
from motu import motu
from log import set_logger, now
from ECMWF import ECMWF
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

def prepare_wind_rose(r, D):
    
    r, D = np.array(r), np.array(D)

    return np.vstack((r, D)).T

def Copernicus_Marine_Service_Download(USER, PSWD, PRODUCT, SERVICE, 
    localpath, filename, lon, lat, idate, edate, var, mode,
    zmin=None, zmax=None):
    
    '''
            This function downloads, as a NetCDF file, the variable from the
            specified product and service. It uses motu-client
    '''

    logger.info(f'{now()} Download from {PRODUCT} {SERVICE}')
    
    if not os.path.exists(localpath):
        os.makedirs(localpath)

    for i in range(5): # Try up to 5 times to download from Copernicus Marine Service
        # Sometime the service is not available. Trying several times increases
        # the chances that the NetCDF file is downloaded successfully.
    
        logger.info(f'{now()} Trial {i} to download local wave forecast')
        
        # Submit request to the motu client
        f = motu(USER, PSWD, PRODUCT, SERVICE, localpath, filename, 
             lon - 1e-4, lon + 1e-4, lat - 1e-4, lat + 1e-4, idate, edate, var, mode, zmin=zmin, zmax=zmax)
        
        if os.path.isfile(f): # File downloaded successfully. Leave loop...
            logger.info(f'{now()}   Successfully downloaded file {f}'); break
        else: # Download failed. Retry...
            logger.info(f'{now()}   Download failed!'); continue
        
    if os.path.isfile(f):
        
        logger.info(f'{now()} Reading local NetCDF file...') 
        
        return read_cmems(f, var)
                 
    else: # If, after trying 5 times, file is still unavailable, return NaN
        
        logger.info(f'{now()} Unable to download Copernicus Marine Service file!')
        # Flag with missing values (NaN)
        return np.nan, np.nan


def MODEL(date=datetime.now()):
    
    root = os.path.abspath('.')
    
    try:
        
        logger.info(f'{now()} Reading config file...')
        try:
            config = configuration()
        except FileNotFoundError:
            raise FileNotFoundError(f'config file not found at root directory {root}')

        # Dictionary to save forecasts
        FC = {}
                
        # Download ECMWF wind forecast
        logger.info(f'{now()} Downloading ECMWF wind forecast...')
        FC['u_wind_fc'], FC['v_wind_fc'], FC['wind_time_fc'], FC['wind_speed_fc'], FC['wind_direction_fc'] = ECMWF(config)

        # Get wind rose for next 72 hours forecasted wind speed and direction
        logger.info(f'{now()} Preparing 72-hour ECMWF wind histogram...')
        idate, edate, wind_rose_fig = wind_rose(FC['wind_time_fc'], prepare_wind_rose(FC['wind_speed_fc'], FC['wind_direction_fc']), 'wind')
        # Fix legend title
        wind_rose_fig = wind_rose_fig.replace("strength", "speed")
        # Wrap into a dictionary
        wind_rose_figure = {'idate': idate, 'edate': edate, 'fig': wind_rose_fig}
        # Wrap direction/period time series into a dictionary (used for CSV export)
        wind_rose_series = {'time': FC['wind_time_fc'],
                            'speed':    FC['wind_speed_fc'],
                            'direction': FC['wind_direction_fc'],
                           }
      

        # Find shortest wave period and associated direction
        logger.info(f'{now()} Finding maximum wind speed and associated direction in ECMWF forecast...')
        maximum_wind_speed_fc, associated_direction_wind = find_maximum_wind_speed_in_forecast(FC['wind_speed_fc'], FC['wind_direction_fc'])
        # Add to forecast dictionary
        FC['maximum_wind_speed_fc'] = maximum_wind_speed_fc
        FC['associated_direction_wind'] = associated_direction_wind
      
        # Subset for the latest NDAYS as per config file 
        t1 = tz('UTC').localize(date)
      
        logger.info(f'{now()} Getting CMEMS credentials from config...')
        USER, PSWD = config['USERNAME'], config['PASSWORD']
        logger.info(f'{now()} Username is {USER}, password is {PSWD}')
        
        # Site coordinates
        logger.info(f'{now()} Getting site longitude and latitude from config...')
        lon, lat = float(config['lon']), float(config['lat'])
        logger.info(f'{now()} Coordinates are {str(lat)}, {str(lon)}')
        
        ''' Download Significant Wave Height forecast '''
        # Take Copernicus Marine Service PRODUCT and SERVICE from user's settings.
        PRODUCT, SERVICE = config['wav'], config['waves']
        # Set local path and file name within container
        localpath, filename = '/netcdf/waves/Significant-Wave-Height', 'Significant-Wave-Height.nc'
        # Set variable to download and mode to Near-Real-Time
        var, mode = 'VHM0', 'nrt'
        # Download
        FC['Hs_fc'] = Copernicus_Marine_Service_Download(USER, PSWD, PRODUCT, SERVICE,
                localpath, filename, lon, lat, t1, t1 + timedelta(days=5), var, mode)

        ''' Download Secondary Swell Significant Wave Height forecast '''
        # Take Copernicus Marine Service PRODUCT and SERVICE from user's settings.
        PRODUCT, SERVICE = config['wav'], config['waves']
        # Set local path and file name within container
        localpath, filename = '/netcdf/waves/Secondary-Swell-Significant-Wave-Height', 'Secondary-Swell-Significant-Wave-Height.nc'
        # Set variable to download and mode to Near-Real-Time
        var, mode = 'VHM0_SW2', 'nrt'
        # Download
        FC['Hs_sw2_fc'] = Copernicus_Marine_Service_Download(USER, PSWD, PRODUCT, SERVICE,
                localpath, filename, lon, lat, t1, t1 + timedelta(days=5), var, mode)
        
        ''' Download Wave Direction at Variance Spectral Density Maximum forecast '''
        # Take Copernicus Marine Service PRODUCT and SERVICE from user's settings.
        PRODUCT, SERVICE = config['wav'], config['waves']
        # Set local path and file name within container
        localpath, filename = '/netcdf/waves/Direction-at-Variance-Spectral-Density-Maximum', 'Direction-at-Variance-Spectral-Density-Maximum.nc'
        # Set variable to download and mode to Near-Real-Time
        var, mode = 'VPED', 'nrt'
        # Download
        FC['VPED'] = Copernicus_Marine_Service_Download(USER, PSWD, PRODUCT, SERVICE,
                localpath, filename, lon, lat, t1, t1 + timedelta(days=1), var, mode)
        
        ''' Download Wave Period at Variance Spectral Density Maximum forecast '''
        # Take Copernicus Marine Service PRODUCT and SERVICE from user's settings.
        PRODUCT, SERVICE = config['wav'], config['waves']
        # Set local path and file name within container
        localpath, filename = '/netcdf/waves/Period-at-Variance-Spectral-Density-Maximum', 'Period-at-Variance-Spectral-Density-Maximum.nc'
        # Set variable to download and mode to Near-Real-Time
        var, mode = 'VTPK', 'nrt'
        # Download
        FC['VTPK'] = Copernicus_Marine_Service_Download(USER, PSWD, PRODUCT, SERVICE,
                localpath, filename, lon, lat, t1, t1 + timedelta(days=1), var, mode)

        # Get wind rose for next 24 hours forecasted wave peak period and direction
        idate, edate, wind_rose_fig = wind_rose(FC['VTPK'][0], prepare_wind_rose(FC['VTPK'][1], FC['VPED'][1]), 'wave')
        # Fix legend title
        wind_rose_fig = wind_rose_fig.replace("strength", "period")
        # Wrap into a dictionary
        wave_rose_figure = {'idate': idate, 'edate': edate, 'fig': wind_rose_fig}
        # Wrap direction/period time series into a dictionary (used for CSV export)
        wave_rose_series = {'time': FC['VTPK'][0],
                            'period':    FC['VTPK'][1],
                            'direction': FC['VPED'][1],
                           }
      

        # Find shortest wave period and associated direction
        shortest_period, associated_direction = find_shortest_wave_period_in_forecast(FC['VTPK'][1], FC['VPED'][1])
        # Add to forecast dictionary
        FC['shortest_period'] = shortest_period
        FC['associated_direction'] = associated_direction
      

        ''' Download Seawater Temperature forecast '''
        # Take Copernicus Marine Service PRODUCT and SERVICE from user's settings.
        PRODUCT, SERVICE = config['phy'], config['sst']
        # Set local path and file name within container
        localpath, filename = '/netcdf/water-quality/seawater-temperature', 'seawater-temperature.nc'
        # Set variable to download and mode to Near-Real-Time
        var, mode = 'thetao', 'nrt'
        # Download
        FC['sst'] = Copernicus_Marine_Service_Download(USER, PSWD, PRODUCT, SERVICE,
                localpath, filename, lon, lat, t1, t1 + timedelta(days=3), var, mode,
                zmin=1, zmax=2)
     
        # Get time zone
        timezone = config['timezone']
                
        send_output(FC, wave_rose_figure, wave_rose_series, wind_rose_figure, wind_rose_series, timezone)        
       
        if not os.path.isdir('/data/IMG'):
            os.mkdir('/data/IMG')
        windArrow('/data/pkl/MODEL-2.pkl', '/data/IMG/ECMWF-FORECAST.png')
        windArrowIcons('/data/pkl/MODEL-2.pkl')
                  
        return 0, ''
       
    except Exception as err:
        
        return -1, str(err)

def find_shortest_wave_period_in_forecast(period, direction):
    ''' 
        This function identifies the shortest wave period
        and its associated direction, to be displayed in the portal
    '''

    shortest_period = np.min(period)

    index_of_shortest_period = np.argmin(period)

    associated_direction = direction[index_of_shortest_period]

    return shortest_period, associated_direction

def find_maximum_wind_speed_in_forecast(speed, direction):
    ''' 
        This function identifies the maximum wind speed
        and its associated direction, to be displayed in the portal
    '''

    maximum_speed = np.max(speed)

    index_of_maximum_speed = np.argmax(speed)

    associated_direction = direction[index_of_maximum_speed]

    return maximum_speed, associated_direction

if __name__ == '__main__':

    delay = 0 # days
    my_date = datetime.now() - timedelta(days=delay)
    my_datestr = my_date.strftime('%d-%b-%Y %H:%M')
    logger.info(f'{now()} Starting site operations for date {my_datestr}')
    status, err = MODEL(date=my_date)
    if status:
        logger.exception(f'Exception in MODEL: {err}')
