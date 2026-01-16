import copernicusmarine as cm
from netCDF4 import Dataset, num2date
from datetime import date, datetime, timedelta
from log import set_logger, now
import numpy as np
from math import nan
import json
import glob
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
    
    localpath = '/data/CHL/'   
    if not os.path.isdir(localpath):
        os.makedirs(localpath)
    # Clean directory
    files = glob.glob(f'{localpath}*.nc')
    for f in files:
        os.remove(f)
    
    # Username and password
    username, password = config['USERNAME'], config['PASSWORD']
    
    # Get geographical boundaries from configuration file
    xmin, xmax, ymin, ymax = get_boundaries(config)    

    version = config.get('version')
    
    ''' Near-Real-Time '''
    # CMEMS SERVICE and PRODUCT
    service = config['dataset_nrt']
    logger.info(f'{now()} Downloading {service}...')
    Copernicus_Marine_Service_Download(username, password, service, version,
            localpath, 'CHL.nc', xmin, xmax, ymin, ymax, 
        (hoy-timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S'),
                            hoy.strftime('%Y-%m-%dT%H:%M:%S'), 'CHL')
   
    with Dataset(localpath + 'CHL.nc', 'r') as nc:
        # Read coordinates
        lon, lat = nc.variables['longitude'][:], nc.variables['latitude'][:]        
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        # Read chlorophyll
        data = np.squeeze(nc.variables['CHL'][:])

    # Mask missing values
    data = data.filled(nan)

    ''' Multi-Year (ANOMALY CALCULATION FOLLOWING TOMLINSON ET. AL (2004) '''
    # CMEMS SERVICE and PRODUCT
    service = config['dataset_my']
    logger.info(f'{now()} Downloading {service}...')
    Copernicus_Marine_Service_Download(username, password, service, version, 
            localpath, 'CHL_MY.nc', xmin, xmax, ymin, ymax,
        (hoy-timedelta(days=90)).strftime('%Y-%m-%dT%H:%M:%S'),
                             hoy.strftime('%Y-%m-%dT%H:%M:%S'), 'CHL')

    with Dataset(localpath + 'CHL_MY.nc', 'r') as nc:
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

def Copernicus_Marine_Service_Download(user, pswd, dataset, version,
        localpath, filename, lonmin, lonmax, latmin, latmax, idate, edate, var):
    
    '''
            This function downloads, as a NetCDF file, the variable from the
            specified dataset. 
    '''

    f = localpath + filename;
        
    for i in range(5): # Try up to 5 times to download from Copernicus Marine Service
    
        logger.info(f'{now()} Trial {i} to download chlorophyll data')

        cm.subset(
                username=user,
                password=pswd,
                dataset_id=dataset,                
                output_directory=localpath,
                output_filename=filename,
                variables=[var],
                minimum_longitude=lonmin,
                maximum_longitude=lonmax,
                minimum_latitude=latmin,
                maximum_latitude=latmax,
                start_datetime=idate,
                end_datetime=edate,
                force_download=True
                )

        if os.path.isfile(f): # File downloaded successfully. Leave loop...
            logger.info(f'{now()}   Successfully downloaded file {f}'); break
        else: # Download failed. Retry...
            logger.info(f'{now()}   Download failed!'); continue
        
    if os.path.isfile(f):
        
        logger.info(f'{now()} Reading local NetCDF file...') 
        
    else: # If, after trying 5 times, file is still unavailable, return NaN
        
        logger.info(f'{now()} Unable to download Copernicus Marine Service file')

