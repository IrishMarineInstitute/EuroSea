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

from oceancolour import oceancolour
import pickle
from slider import Slider
import numpy as np
import json
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
            # Save to dictionary
            config[key] = val
    return config

def RS():
    
    root = os.path.abspath('.')
    
    try:
        
        logger.info(f'{now()} Reading config file...')
        try:
            config = configuration()
        except FileNotFoundError:
            raise FileNotFoundError(f'config file not found at root directory {root}')

        # Get buoy locations
        x_buoy, y_buoy = json.loads(config['lon']), json.loads(config['lat'])

        # Read coastline
        with open(config['coastfile'], 'rb') as f:
            coast = pickle.load(f)
            x_coast, y_coast = coast['longitude'], coast['latitude']

        # Oceancolour
        logger.info(f'{now()} Downloading oceancolour...')
        lon, lat, time, CHL, ANM = oceancolour(config)

        # Fix data type
        CHL = np.round(CHL.astype(np.float64), 1)
        ANM = np.round(ANM.astype(np.float64), 1)

        # Create figure
        logger.info(f'{now()} CREATING CHLOROPHYLL-a FIGURE...')
        colorscale = 'Greens'
        tickvals = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        contours=dict(start=0, end=10, size=1)
        try:
            chl = Slider((lon, lat, time, CHL), (x_coast, y_coast), (x_buoy, y_buoy),
                colorscale, tickvals, contours)
        except Exception as e:
            logging.critical(e, exc_info=True)

        # Create anomalies figure
        logger.info(f'{now()} CREATING CHLOROPHYLL-a ANOMALIES FIGURE...')
        colorscale = 'RdBu_r'
        tickvals = [-3, -2, -1, 0, 1, 2, 3]
        contours=dict(start=-3, end=3, size=.5)
        try:
            anm = Slider((lon, lat, time, ANM), (x_coast, y_coast), (x_buoy, y_buoy),
                colorscale, tickvals, contours)
        except Exception as e:
            logging.critical(e, exc_info=True)

        # Export figure to file
        logger.info(f'{now()} EXPORTING FIGURES TO FILE...')
        with open('/data/pkl/CHL.pkl', 'wb') as f:
            pickle.dump({'CHL': chl, 'CHLANM': anm}, f)

        logger.info(f'{now()} FINISHED...')

        return 0, ''

    except Exception as err:
           
        return -1, str(err)

if __name__ == '__main__':

    status, err = RS()
    if status:
        logger.exception(f'Exception in RS: {err}')
