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
    
    if not os.path.isdir('/data/IWBN-90'):
        os.mkdir('/data/IWBN-90')
        
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
        shutil.move(f, f'/data/IWBN-90/{i}.nc')

    # Initialize dictionary
    IWBN = {}

    # Load IWBN SST 
    with open('/data/SST/IWBN-SST-90.pkl', 'rb') as f:
        SST = pickle.load(f)

    lista = glob.glob('/data/IWBN-90/M*.nc')
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

        with open('/data/pkl/IWBN-90.pkl', 'wb') as f:
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
