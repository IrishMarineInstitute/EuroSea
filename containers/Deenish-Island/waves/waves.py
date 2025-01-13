from datetime import datetime, timedelta
import copernicusmarine as cm
from glob import glob
import os
import re

from log import set_logger, now
logger = set_logger()

def Copernicus_Marine_Service_Download(user, pswd, dataset, version, 
        localpath, filename, lonmin, lonmax, latmin, latmax, idate, edate, var):
    
    '''
            This function downloads, as a NetCDF file, the variable from the
            specified dataset. 
    '''

    f = localpath + filename;
        
    for i in range(5): # Try up to 5 times to download from Copernicus Marine Service
    
        logger.info(f'{now()} Trial {i} to download wave data')
         
        cm.subset(
                username=user,
                password=pswd,
                dataset_id=dataset,
                dataset_version=version,
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

def waves(time, config):
    
    '''
        This function downloads the wave height data for the
        area selected in the configuration file.
    '''

    user, pswd = config['USERNAME'], config['PASSWORD']
        
    logger.info(f'{now()} Getting geographical boundaries of area of interest...')
    lonmin, lonmax = float(config['west']), float(config['east'])
    latmin, latmax = float(config['south']), float(config['north'])
    logger.info(f'{now()} Boundaries are NORTH: {str(latmax)}, SOUTH: {str(latmin)}, WEST: {str(lonmin)}, EAST: {str(lonmax)}')
        
    dataset, version = config['wave-dataset'], config['wave-version']

    ''' Set local directory to download NetCDF files to '''
    FORECAST = '/data/netcdf/waves/'     
    if not os.path.isdir(FORECAST):
        os.makedirs(FORECAST)

    # Set variable to download and mode to Near-Real-Time
    var = 'VHM0'

    ''' Forecast '''      
    year, month, day = time.year, time.month, time.day

    # Date range to download forecast data 
    idate = datetime(year, month, day) - timedelta(days=1)
    edate = idate + timedelta(days=7)
    # Convert dates to strings 
    idate = idate.strftime('%Y-%m-%dT%H:%M:%S')
    edate = edate.strftime('%Y-%m-%dT%H:%M:%S')

    ''' Remove older forecast ''' 
    file = 'Deenish-wave-forecast.nc'
    if os.path.isfile(FORECAST + file):
        os.remove(FORECAST + file)

    logger.info(' '); logger.info(f'{now()} Downloading forecast wave data...')
    Copernicus_Marine_Service_Download(user, pswd, dataset, version, FORECAST, 
        file, lonmin, lonmax, latmin, latmax, idate, edate, var)
