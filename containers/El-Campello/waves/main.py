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
from netCDF4 import Dataset
from pickle import load
from waves import waves
import numpy as np
import json
import os

from log import set_logger, now
logger = set_logger()

def get_coordinate(key, config):
    s = key.upper()
    try:
        v = config[key]
        return float(v)
    except KeyError:
        raise KeyError(f'No value has been provided for {s} in config file. Aborting...')
    except ValueError:
        raise ValueError(f'''Wrong value {v} has been provided for {s} in config file.
            'Please, make sure that the value provded is a valid number''')

def get_boundaries(config):
    keys, vals = ('west', 'east', 'south', 'north'), []    
    for k in keys:
        vals.append(get_coordinate(k, config))
    return vals

def configuration():
    ''' Read configuration file '''
    config = {}
    with open('config', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save to dictionary
            config[key] = val
    return config

def wave(date=datetime.now()):

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
        x_coast, y_coast = coast['lon_coast'], coast['lat_coast']
        x_coast, y_coast = np.array(json.loads(x_coast)), np.array(json.loads(y_coast))
        coast = (x_coast, y_coast)

        # Get buoy longitude/latitude
        buoy = float(config['lon']), float(config['lat'])

        # Read wave history/forecasts
        logger.info(f'{now()} Starting download of wave forecasts...')
        waves(date, config)

        timezone = config['timezone']
                
        send_output(coast, timezone, buoy)        

        logger.info(f'{now()} FINISHED')
            
        return 0, ''

       
    except Exception as err:
        
        return -1, str(err)

if __name__ == '__main__':

    my_date = datetime.now()
    my_datestr = my_date.strftime('%d-%b-%Y %H:%M')
    status, err = wave(date=my_date)
    if status:
        logger.exception(f'Exception in WAVE: {err}')
