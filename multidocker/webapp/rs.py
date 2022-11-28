from datetime import datetime, timedelta
from oceancolour import oceancolour, get_boundaries
from outputrs import send_output
import numpy as np
from netCDF4 import Dataset
from SST import SST
from pickle import load
import os

def address_request(date):

    config = configuration()

    # Read coastline
    with open(config['coastfile'], 'rb') as f:
        coast = load(f)

    # Read climatology
    clim = climatology(config['clim'])
    lon_c, lat_c, time_c, seas, pc90 = clim

    # SST
    boundaries = get_boundaries(config)
    sst_out = SST(time_c, seas, pc90, date, boundaries)

    # Oceancolour
    #colour = oceancolour(datetime.strptime(date, '%Y-%m-%d'), config)

    # Site coordinates
    lon, lat = float(config['lon']), float(config['lat'])
        
    return send_output(lon, lat, sst_out, coast)        
    
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

def climatology(file):
    ''' Read climatology from NetCDF file '''
       
    with Dataset(file, 'r') as nc:
        # Read longitude
        lon = nc.variables['longitude'][:]
        # Read latitude
        lat = nc.variables['latitude'][:]
        # Read time
        time = nc.variables['time'][:]
        # Read seasonal cycle (climatology)
        seas = nc.variables['seas'][:]
        # Read 90-th percentile (MHW threshold)
        pc90 = nc.variables['thresh'][:]

    return lon, lat, time, seas, pc90
