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

      This is the main script of the IWBN container. This application is set
   to run hourly to download the latest seawater temperature observations
   from the Irish Weather Buoy Network. Data is downloaded from the Marine
   Institute ERDDAP. This application is set to run hourly to make sure that
   the website updates as soon as new data is released on the ERDDAP. This 
   application also creates the figures that are later accessed by the WEBAPP 
   container through the shared volume.

'''

from datetime import datetime, date, timedelta
from netCDF4 import Dataset, num2date
from series import timeSeries
import numpy as np
import pickle
import wget
import shutil
import glob
import os

from log import set_logger, now
logger = set_logger()

def IWBNetwork():
    ''' Download data from the Irish Weather Buoy Network '''
    
    # Read configuration file
    config = configuration()
    
    # Number of days back in time to download
    N = int(config['N'])

    # Date range to download
    idate = (date.today() - timedelta(days=N)).strftime('%Y-%m-%d')
    
    # Buoys
    M = ('M2', 'M3', 'M4', 'M5', 'M6')
    
    if not os.path.isdir('/data/IWBN'):
        os.mkdir('/data/IWBN')
        
    root = "https://erddap.marine.ie/erddap/tabledap/IWBNetwork.nc?"       + \
               "station_id%2Clongitude%2Clatitude%2Ctime%2CSeaTemperature" + \
               "&station_id=%22"
               
    suffix, tail = "%22&time%3E=", "T00%3A00%3A00Z"
        
    for i in M:
        logger.info(f'{now()} Downloading {i}')
        f = root + i + suffix + idate + tail
        # Download
        f = wget.download(f)
        # Move
        shutil.move(f, f'/data/IWBN/{i}.nc')

    # Initialize dictionary
    IWBN = {}

    # Load IWBN SST 
    with open('/data/SST/IWBN-SST.pkl', 'rb') as f:
        SST = pickle.load(f)

    lista = glob.glob('/data/IWBN/M*.nc')
    for f in lista:
        with Dataset(f, 'r') as nc:
            # Read station ID
            ID = np.unique(nc.variables['station_id'][:])[0]
            # Read time
            time = num2date(nc.variables['time'][:], nc.variables['time'].units)
            # Read seawater temperature
            temp = nc.variables['SeaTemperature'][:]

        # Set name of climatology file
        infile = f'{ID}-Climatology.pkl'

        # Get climatology
        climatology = site_climatology(infile, time)
        
        # Convert time to string
        time = [datetime(i.year, i.month, i.day, i.hour, i.minute).strftime('%Y-%m-%d %H:%M') for i in time]

        # Create time series figure
        fig = timeSeries(f'Seawater temperature at {ID}', time, temp, climatology=climatology, SST=(SST['time'], SST[ID]))

        IWBN[ID] = fig

        with open('/data/pkl/IWBN.pkl', 'wb') as f:
            pickle.dump(IWBN, f)

    logger.info(f'{now()} FINISHED!')

    
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

def site_climatology(infile, time):
    ''' Reads site climatology from local PICKLE file '''

    time = [datetime(i.year, i.month, i.day, i.hour, i.minute) for i in time]
    
    with open(infile, 'rb') as f:
        clim = pickle.load(f)
    
    t0, t1 = time[0] - timedelta(days=1), time[-1] + timedelta(days=8)
    
    time = []
    while t0 < t1:
        time.append(t0); t0 += timedelta(minutes=10)
    # Data from local climatology file    
    day_of_year, seasonal_cycle, PC90 = clim['time'], clim['seas'], clim['pc90']

    day_of_year = np.squeeze(day_of_year)
    seasonal_cycle = np.squeeze(seasonal_cycle)
    PC90 = np.squeeze(PC90)
    
    # Output initialization
    Time, Seas, Pc90 = [], [], []
    
    for t in time:        
        H, M = t.hour, t.minute            
        if H == 12 and not M:
            # Get day of year
            Day_Of_Year = t.timetuple().tm_yday
            # Find time index in local climatology file
            i = np.where(day_of_year == Day_Of_Year)[0][0]
            # Append to output arrays
            Time.append(t.strftime('%Y-%m-%d %H:%M'))
            Seas.append(seasonal_cycle[i])
            Pc90.append(PC90[i])

    return Time, Seas, Pc90

if __name__ == '__main__':
    IWBNetwork()