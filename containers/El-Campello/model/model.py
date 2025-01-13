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
from pytz import timezone as tz
from output import send_output
from wind_rose import wind_rose
from windArrow import windArrow
import numpy as np
from netCDF4 import Dataset, num2date
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

def prepare_wind_rose(r, D):
    
    r, D = np.array(r), np.array(D)

    return np.vstack((r, D)).T

def Copernicus_Marine_Service_Download(user, pswd, dataset, version, 
        localpath, filename, lonmin, lonmax, latmin, latmax, idate, edate, var,
        minimum_depth=None, maximum_depth=None):
    
    '''
            This function downloads, as a NetCDF file, the variable from the
            specified dataset. 
    '''

    f = localpath + filename;

    # Convert dates to strings
    idate = idate.strftime('%Y-%m-%dT%H:%M:%S')
    edate = edate.strftime('%Y-%m-%dT%H:%M:%S')
        
    for i in range(5): # Try up to 5 times to download from Copernicus Marine Service
    
        logger.info(f'{now()} Trial {i} to download Copernicus data')
         
        cm.subset(
                username=user,
                password=pswd,
                dataset_id=dataset,
                dataset_version=version,
                output_directory=localpath,
                output_filename=filename,
                variables=var,
                minimum_longitude=lonmin,
                maximum_longitude=lonmax,
                minimum_latitude=latmin,
                maximum_latitude=latmax,
                minimum_depth=minimum_depth,
                maximum_depth=maximum_depth,
                start_datetime=idate,
                end_datetime=edate,
                force_download=True
                )

        if os.path.isfile(f): # File downloaded successfully. Leave loop...
            logger.info(f'{now()}   Successfully downloaded file {f}'); break
        else: # Download failed. Retry...
            logger.info(f'{now()}   Download failed!'); continue
        
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

        localpath = '/data/netcdf/model/El-Campello/'
        
        ''' Download Significant Wave Height forecast '''
        # Take Copernicus Marine Service PRODUCT and SERVICE from user's settings.
        dataset, version = config['dataset-id-waves'], config['dataset-version-waves']
        # Set local path and file name within container
        filename = 'Wave-Forecast.nc'
        if os.path.isfile(localpath + filename):
            os.remove(localpath + filename)

        # Set variable to download 
        var = ['VHM0', 'VHM0_SW2', 'VPED', 'VTPK']
        # Download
        Copernicus_Marine_Service_Download(USER, PSWD, dataset, version,  
                localpath, filename, lon-1e-4, lon+1e-4, lat-1e-4, lat+1e-4, 
                t1, t1 + timedelta(days=5), var)

        if os.path.isfile(localpath + filename):
            # Download successful. Read forecast and pass to output dictionary
            FC['Hs_fc'] = read_cmems(localpath + filename, 'VHM0')
            FC['Hs_sw2_fc'] = read_cmems(localpath + filename, 'VHM0_SW2')
            FC['VPED'] = read_cmems(localpath + filename, 'VPED')
            FC['VTPK'] = read_cmems(localpath + filename, 'VTPK')

        else: # Download failed. Use "NaN" for both time and data
            FC['Hs_fc'] = np.nan, np.nan
            FC['Hs_sw2_fc'] = np.nan, np.nan
            FC['VPED'] = np.nan, np.nan
            FC['VTPK'] = np.nan, np.nan

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
      
        timezone = config['timezone']
                
        send_output(FC, wave_rose_figure, wave_rose_series, wind_rose_figure, wind_rose_series, timezone)        
       
        if not os.path.isdir('/data/IMG'):
            os.mkdir('/data/IMG')
        # Create ECMWF winds static image
        windArrow('/data/pkl/MODEL-2.pkl', '/data/IMG/ECMWF-FORECAST.png')
                  
        logger.info(f'{now()} FINISHED!')

        return 0, ''
       
    except Exception as err:
        
        return -1, str(err)

if __name__ == '__main__':

    status, err = MODEL()
    if status:
        logger.exception(f'Exception in MODEL: {err}')
