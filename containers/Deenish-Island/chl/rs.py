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

      This is the main script of the CHL container. This application is set
   to run hourly to download the latest seawater chlorophyll-a concentration
   observations in the Southwest of Ireland waters. The chlorophyll-a 
   concentration is provided by the Atlantic Ocean Colour Bio-Geo-Chemical 
   L4 Satellite Observations (https://doi.org/10.48670/moi-00288).
   
      In addition, chlorophyll-a anomaly is determined as the difference 
   between the actual chlorophyll-a concentration and a 60-day running median, 
   ending two weeks before the current image (Tomlinson et al., 2004).

      This application is set to run hourly to make sure that the website
   updates as soon as a new daily layer is released by the Copernicus
   Marine Service. This application also creates the figures that are later
   accessed by the WEBAPP container through the shared volume.

'''

from oceancolour import oceancolour
from output import send_output
import pickle
from log import set_logger, now
from slider import Slider
import numpy as np
import json
import os

logger = set_logger()

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

def RS():
    
    root = os.path.abspath('.')
    
    try:
        
        logger.info(f'{now()} Reading config file...')
        try:
            config = configuration()
        except FileNotFoundError:
            raise FileNotFoundError(f'config file not found at root directory {root}')

        # Get buoy locations from configuration file. This is needed
        # to display the buoy locations (Deenish, IWBN) on the maps. 
        x_buoy, y_buoy = json.loads(config['lon']), json.loads(config['lat'])

        # Read coastline. The coastline file is not included in the repository,
        # but has to be provided to show the coastline on the maps. It should be
        # a pickle file with a dictionary providing the longitude and the 
        # latitude of the coastline points. 
        with open(config['coastfile'], 'rb') as f:
            coast = pickle.load(f)
            x_coast, y_coast = coast['longitude'], coast['latitude']

        # Oceancolour
        logger.info(f'{now()} Downloading oceancolour...')
        lon, lat, time, CHL, ANM = oceancolour(config)

        # Fix data type. Chlorophyll-a data is rounded of to one decimal place.
        # This is to reduce the amount of data sent to the web portal.
        CHL = np.round(CHL.astype(np.float64), 1)
        ANM = np.round(ANM.astype(np.float64), 1)

        # Create SST figure
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

        # Export figure to file. This file can be accessed by the web
        # application through the shared volume. 
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
