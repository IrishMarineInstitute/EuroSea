from netCDF4 import Dataset, num2date
from datetime import date, datetime, timedelta
from log import set_logger, now
import numpy as np
from motu import motu
from math import nan
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

def oceancolour(config):
    ''' Download requested OCEANCOLOUR data '''

    hoy = date.today()
    
    localpath = '/data/CHL'   
    if not os.path.isdir(localpath):
        os.makedirs(localpath)
    
    # Username and password
    username, password = config['USERNAME'], config['PASSWORD']
    
    # Get geographical boundaries from configuration file
    xmin, xmax, ymin, ymax = get_boundaries(config)    
    
    ''' Near-Real-Time '''
    # CMEMS SERVICE and PRODUCT
    service, product = config['OCEANCOLOUR_NRT_SERVICE'], config['OCEANCOLOUR_NRT_PRODUCT']
    nrt = download_chlorophyll(service, product, username, password, localpath,
        'CHL.nc', xmin, xmax, ymin, ymax, hoy)
   
    with Dataset(nrt, 'r') as nc:
        # Read coordinates
        lon, lat = nc.variables['lon'][:], nc.variables['lat'][:]        
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        # Read chlorophyll
        data = np.squeeze(nc.variables['CHL'][:])

    # Mask missing values
    data = data.filled(nan)

    ''' Multi-Year (ANOMALY CALCULATION FOLLOWING TOMLINSON ET. AL (2004) '''
    # CMEMS SERVICE and PRODUCT
    service, product = config['OCEANCOLOUR_MY_SERVICE'], config['OCEANCOLOUR_MY_PRODUCT']
    my = download_chlorophyll(service, product, username, password, localpath,
        'CHL-MY.nc', xmin, xmax, ymin, ymax, hoy)

    with Dataset(my, 'r') as nc:
        # Read time
        mytime = num2date(nc.variables['time'][:], nc.variables['time'].units)
        # Read chlorophyll
        mydata = np.squeeze(nc.variables['CHL'][:])

    # Initialize array for chlorophyll anomalies, same shape as chlorophyll
    anomalies = np.empty_like(data)

    logger.info(f'{now()} Calculating Chlorophyll-a anomalies following Tomlinson et al. (2004)')
    for index, t in enumerate(time):
        logger.info(f'   {now()} Processing time {t}...')

        # Start time to subset
        minus73days = t - timedelta(days=73)
        # End time to subset
        minus14days = t - timedelta(days=14)

        logger.info(f'   {now()} Subsetting from {minus73days} to {minus14days}')

        # Start time index to subset
        id0 = np.where(mytime == minus73days)[0][0]
        # End time index to subset
        id1 = np.where(mytime == minus14days)[0][0] + 1

        logger.info(f'   {now()} Subsetting from indexes {id0} to {id1}')

        # Array of 60-day past values
        past = mydata[id0 : id1, :, :]
        # Check shape
        T, M, L = past.shape
        if T != 60:
            raise ValueError('Length of time coordinate MUST be 60 days to calculate anomalies')

        # Median
        logger.info(f'   {now()} Calculating median...')
        median = np.nanmedian(past, axis=0)

        # Get chlorophyll-a anomaly 
        logger.info(f'   {now()} Calculating anomalies...')
        anomalies[index, :, :] = data[index, :, :] - median

    return lon, lat, time, data, anomalies

def download_chlorophyll(service, product, username, password, localpath,
                         file, xmin, xmax, ymin, ymax, date):
    ''' Download chlorophyll data from Copernicus using motu client '''
    
    # Set product type, either Multi-Year or Near-Real-Time
    mode = 'my' if 'my' in service else 'nrt'
    while 1:
        # Send request to motu client
        f = motu(username, password, product, service, localpath, file, 
             xmin, xmax, ymin, ymax, date - timedelta(days=90), date,
             'CHL', mode)
        # Exit only if download has been successful
        if os.path.isfile(f): break
    return f 
