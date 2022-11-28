from netCDF4 import MFDataset, num2date
from datetime import datetime, timedelta
import numpy as np
from motu import motu
import os

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

def oceancolour(date, config):
    ''' Download requested OCEANCOLOUR data '''
    
    localpath = '/netcdf'   
    
    # Username and password
    username, password = config['USERNAME'], config['PASSWORD']
    
    # Get geographical boundaries from configuration file
    xmin, xmax, ymin, ymax = get_boundaries(config)    
    
    ''' Multi-Year '''
    # CMEMS SERVICE and PRODUCT
    service, product = config['OCEANCOLOUR_MY_SERVICE'], config['OCEANCOLOUR_MY_PRODUCT']
    my = download_chlorophyll(service, product, username, password, localpath,
        'CHL-MY.nc', xmin, xmax, ymin, ymax, date)
    
    ''' Near-Real-Time '''
    # CMEMS SERVICE and PRODUCT
    service, product = config['OCEANCOLOUR_NRT_SERVICE'], config['OCEANCOLOUR_NRT_PRODUCT']
    nrt = download_chlorophyll(service, product, username, password, localpath,
        'CHL-NRT.nc', xmin, xmax, ymin, ymax, date)
   
    ''' Open MY and NRT files together '''
    with MFDataset([my, nrt], aggdim='time') as nc:
        # Read coordinates
        lon, lat = nc.variables['lon'][:], nc.variables['lat'][:]        
        # Read time
        time = num2date(nc.variables['time'][-1], nc.variables['time'].units)
        # Read chlorophyll
        data = np.squeeze(nc.variables['CHL'][:])

    # Convert to Python datetime
    time = datetime(time.year, time.month, time.day, time.hour)
        
    # Get chlorophyll anomaly
    anom = get_anom(data)
    
    return lon, lat, time, data[-1, :, :], anom

def download_chlorophyll(service, product, username, password, localpath,
                         file, xmin, xmax, ymin, ymax, date):
    ''' Download chlorophyll data from Copernicus using motu client '''
    
    # Set product type, either Multi-Year or Near-Real-Time
    mode = 'my' if 'my' in service else 'nrt'
    while 1:
        # Send request to motu client
        f = motu(username, password, product, service, localpath, file, 
             xmin, xmax, ymin, ymax, date - timedelta(days=73), date,
             'CHL', mode)
        # Exit only if download has been successful
        if os.path.isfile(f): break
    return f 

def get_anom(data):
    ''' Get chlorophyll anomaly as the difference between present values and 
    the median of the 60-day period from 73 days to 14 days before present '''
    
    # Current values
    now = data[-1, :, :]
    # Array of 60-day past values
    past = data[0:-14, :, :]
    # Median
    med = np.nanmedian(past, axis=0)
    # Return difference (anomaly)
    return now - med  

