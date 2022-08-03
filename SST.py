''' Functions to download SST data, either OSTIA or MUR '''

from datetime import datetime
from netCDF4 import Dataset, num2date
import numpy as np
from pydap.cas.get_cookies import setup_session
from pydap.client import open_url
from webob import exc
import xarray as xr

# Set boundaries (W, E, S, N)
xmin, xmax, ymin, ymax = -11.6, -8, 50, 52.8

def read_mur(url):
    ''' Reads from Multi-scale Ultra-high Resolution Sea Surface Temperature '''
    
    print('\nOpening dataset MUR-JPL-L4-GLOB-v4.1...')
    with Dataset(url) as nc:
        
        while True:
        
            try:
                                
                lon = nc.variables['lon'][:]
                x0, x1 = nearest(lon, xmin), nearest(lon, xmax) + 1
                
                lat = nc.variables['lat'][:]
                y0, y1 = nearest(lat, ymin), nearest(lat, ymax) + 1
                
                # Read latest time
                time = num2date(nc.variables['time'][-24:], nc.variables['time'].units)
                
                # Read SST
                SST = nc.variables['analysed_sst'][-24:, y0 : y1, x0 : x1] - 273.15
                
                break
            
            except RuntimeError: continue
        
            except exc.HTTPError: continue
        
    time = [datetime(i.year, i.month, i.day, i.hour) for i in time]
            
    return lon[x0 : x1], lat[y0 : y1], time, SST

def read_ostia(dataset, username, password, variable):
    ''' Reads coordinates and variable "variable" from the Copernicus dataset 
    specified by "dataset", using credentials determined by "username" and "password" '''
    
    offset = 360 if 'ANOM' in dataset else 0
    
    while True:
        
        try:            
            
            data_store = copernicusmarine_datastore(dataset, username, password)
            print(f'\nOpening dataset {dataset}...')
            with xr.open_dataset(data_store) as DS:                
                
                lon = DS.lon.data - offset
                x0, x1 = nearest(lon, xmin), nearest(lon, xmax) + 1
                
                lat = DS.lat.data 
                y0, y1 = nearest(lat, ymin), nearest(lat, ymax) + 1
                
                # Read latest time
                time = DS.time.data[-1]
                
                # Read SST
                SST = DS[variable][-1, y0 : y1, x0 : x1] - 273.15; break
                                    
        except RuntimeError: continue
    
        except exc.HTTPError: continue
    
    return lon[x0 : x1], lat[y0 : y1], time, SST

def copernicusmarine_datastore(dataset, username, password):    
    cas_url = 'https://cmems-cas.cls.fr/cas/login'
    session = setup_session(cas_url, username, password)
    session.cookies.set("CASTGC", session.cookies.get_dict()['CASTGC'])
    database = ['my', 'nrt']
    url = f'https://{database[0]}.cmems-du.eu/thredds/dodsC/{dataset}'
    try:
        data_store = xr.backends.PydapDataStore(open_url(url, session=session))
    except:
        url = f'https://{database[1]}.cmems-du.eu/thredds/dodsC/{dataset}'
        data_store = xr.backends.PydapDataStore(open_url(url, session=session))
    return data_store    

def nearest(lista, valor):
    return np.argmin(abs(lista - valor))