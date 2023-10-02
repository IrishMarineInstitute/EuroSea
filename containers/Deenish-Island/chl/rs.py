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
 
       log.py : Logging script. Useful messages are sent to a file /log/app.log

       motu.py : Script using the motuclient to download CMEMS data.

       oceancolour.py : Script downloading chlorophyll data and calculating 
                        anomalies. 

       output.py : Script that finally wraps all the model data in MODEL.pkl
                   and in a format that can be understood by the website.

       requirements.txt : Python packages needed to run this container.

       rs.py : This script. It is the main file calling the other methods.

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
