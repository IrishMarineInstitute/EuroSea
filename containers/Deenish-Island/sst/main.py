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

      This is the main script of the SST container. This application is set
   to run hourly to download the latest sea surface temperature observations
   for the Irish EEZ. The sea surface temperature is provided by the 
   Operational Sea Surface Temperature and Ice Analysis (OSTIA) system run 
   by the UK's Met Office and delivered by IFREMER.

      In addition, sea surface temperature anomalies are calculated using
   a 40-year baseline reference climatology. The occurrence of marine heat
   waves is determined using the Hobday et al. (2016) definition.

      This application is set to run hourly to make sure that the website
   updates as soon as a new daily layer is released by the Copernicus
   Marine Service. This application also creates the figures that are
   later accessed by the WEBAPP container through the shared volume.

'''

from anomalies import Anomalies
from datetime import datetime
from MHW import MarineHeatWaves
from ostia import OSTIA
from slider import Slider
from netCDF4 import Dataset
import numpy as np
import pickle
import json
import re

from log import set_logger, now
logger = set_logger()

def main():
    # Read settings from configuration file
    config = configuration()

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

    # Read climatology. Again, the climatology file is not included in the
    # repository, but has to be provided to determine SST anomalies and 
    # the occurrence of Marine Heat Waves. 
    f = config['clim']
    logger.info(f'{now()} Retrieving climatology from file {f}')
    clim = climatology(f)
    time_c, seas, pc90 = clim

    # Download sea surface temperature
    lon, lat, time, SST = OSTIA(config)

    # Get SST at IWBN sites
    names = ['Deenish', 'M2', 'M3', 'M4', 'M5', 'M6']
    IWBN(x_buoy, y_buoy, names, lon, lat, time, SST) 

    # Calculate SST anomalies
    sst = (time, SST); clm = (time_c, seas, pc90)
    ANM = Anomalies(sst, clm)

    # Get Marine Heat Wave intensity
    marineHeatWaves = MarineHeatWaves(clm)

    # Fix data type. Coordinate data is rounded off to three decimal places, 
    # whereas temperature data is rounded of to one decimal place. This is
    # to reduce the amount of data sent to the web portal.
    lon, lat = np.round(lon.astype(np.float64), 3), np.round(lat.astype(np.float64), 3)
    SST, ANM = np.round(SST.astype(np.float64), 1), np.round(ANM.astype(np.float64), 1)
    marineHeatWaves = np.round(marineHeatWaves.astype(np.float64), 1)

    # Create SST figure
    logger.info(f'{now()} CREATING SEA SURFACE TEMPERATURE FIGURE...')
    colorscale = 'Portland'
    tickvals = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    contours=dict(start=5, end=20, size=1)
    try:
        sst = Slider(lon, lat, time, SST, (x_coast, y_coast), (x_buoy, y_buoy),
            colorscale, tickvals, contours)
    except Exception as e:
        logging.critical(e, exc_info=True)

    # Create anomalies figure
    logger.info(f'{now()} CREATING ANOMALIES FIGURE...')
    colorscale = 'RdBu_r'
    tickvals = [-3, -2, -1, 0, 1, 2, 3]
    contours=dict(start=-3, end=3, size=.25)
    try:
        anm = Slider(lon, lat, time, ANM, (x_coast, y_coast), (x_buoy, y_buoy),
            colorscale, tickvals, contours)
    except Exception as e:
        logging.critical(e, exc_info=True)

    # Create MHW figure
    logger.info(f'{now()} CREATING MHW FIGURE...')
    colorscale = 'Reds'
    tickvals = [0, 1, 2, 3]
    contours=dict(start=0, end=3, size=.25)
    try:
        mhw = Slider(lon, lat, time, marineHeatWaves, (x_coast, y_coast), (x_buoy, y_buoy),
            colorscale, tickvals, contours)
    except Exception as e:
        logging.critical(e, exc_info=True)

    # Export figures to file. This file can be accessed by the web
    # application through the shared volume. 
    logger.info(f'{now()} EXPORTING FIGURE TO FILE...')
    with open('/data/pkl/SST.pkl', 'wb') as f:
        pickle.dump({'SST': sst, 'ANM': anm, 'MHW': mhw}, f)

    logger.info(f'{now()} FINISHED...')

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

def climatology(file):
    ''' Read climatology from NetCDF file '''
    
    # The climatology file should be a NetCDF file with longitude,
    # latitude and day-of-year (time) dimensions. The grid should
    # be the same as the SST grid from the selected product (here,
    # the OSTIA product). For each grid point, and for each day of
    # the year (list of days from 1 to 366), the mean climatological
    # values "seas" and the PCT. 90 "pc90" must be provided. There
    # are useful tools to determine these values using the Hobday et
    # al. (2016) guidelines. Here, the ecjoliver Marine Heat Waves
    # repository (https://github.com/ecjoliver/marineHeatWaves) has
    # been used.
       
    with Dataset(file, 'r') as nc:
        time = nc.variables['time'][:]
        # Read seasonal cycle (climatology)
        seas = nc.variables['seas'][:]
        # Read 90-th percentile (MHW threshold)
        pc90 = nc.variables['thresh'][:]

    return time, seas, pc90

def IWBN(x, y, names, lon, lat, time, SST):
    ''' Get SST at IWBN sites '''

    #    The Irish Weather Buoy Network graphics in the website provides
    # the remote-sensing SST observations at the buoy sites. This code
    # retrieves the SST series at each IWBN site. This data can be later
    # accessed by the IWBN container to produce the graphics in the portal.

    time = [datetime(i.year, i.month, i.day, i.hour).strftime('%Y-%m-%d %H:%M') for i in time]
    
    out = {'time': time}
    for i, j, n in zip(x, y, names):
        # Get index of nearest longitude node
        idx = np.argmin(abs(lon - i))
        # Get index of nearest latitude node
        idy = np.argmin(abs(lat - j))
        # Get SST
        out[n] = SST[:, idy, idx].tolist()
        
    with open('/data/SST/IWBN-SST.pkl', 'wb') as f:
        pickle.dump(out, f)

if __name__ == '__main__':
    main()
