from datetime import datetime, timedelta
from glob import glob
from motu import motu
import os
import re

from log import set_logger, now
logger = set_logger()

def Copernicus_Marine_Service_Download(USER, PSWD, PRODUCT, SERVICE, 
    localpath, filename, lonmin, lonmax, latmin, latmax, idate, edate, var, mode,
    zmin=None, zmax=None):
    
    '''
            This function downloads, as a NetCDF file, the variable from the
            specified product and service. It uses motu-client
    '''

    logger.info(f'{now()} Download from {PRODUCT} {SERVICE}')
    
    if not os.path.exists(localpath):
        os.makedirs(localpath)

    for i in range(5): # Try up to 5 times to download from Copernicus Marine Service
        # Sometime the service is not available. Trying several times increases
        # the chances that the NetCDF file is downloaded successfully.
    
        logger.info(f'{now()} Trial {i} to download wave data')
        
        # Submit request to the motu client
        f = motu(USER, PSWD, SERVICE, PRODUCT, localpath, filename, 
             lonmin, lonmax, latmin, latmax, idate, edate, var, mode)
        
        if os.path.isfile(f): # File downloaded successfully. Leave loop...
            logger.info(f'{now()}   Successfully downloaded file {f}'); break
        else: # Download failed. Retry...
            logger.info(f'{now()}   Download failed!'); continue
        
    if os.path.isfile(f):
        
        logger.info(f'{now()} Reading local NetCDF file...') 
        
    else: # If, after trying 5 times, file is still unavailable, return NaN
        
        logger.info(f'{now()} Unable to download Copernicus Marine Service file')


def get_date_from_file_name(filename):

    ''' Get date from file name '''

    # Files are named "waves-yyyymmdd.nc"    

    datestr = re.search('-(.*).nc', filename).group(1)

    return datetime.strptime(datestr, '%Y%m%d')


def waves(time, config):
    
    '''
        This function downloads the wave height data for the
        area selected in the configuration file.
    '''

    logger.info(f'{now()} Getting CMEMS credentials from configuration...')
    USER, PSWD = config['USERNAME'], config['PASSWORD']
    logger.info(f'{now()} Username is {USER}, password is {PSWD}')
        
    logger.info(f'{now()} Getting geographical boundaries of area of interest...')
    lonmin, lonmax = float(config['west']), float(config['east'])
    latmin, latmax = float(config['south']), float(config['north'])
    logger.info(f'{now()} Boundaries are NORTH: {str(latmax)}, SOUTH: {str(latmin)}, WEST: {str(lonmin)}, EAST: {str(lonmax)}')
        
    ''' Read Copernicus Marine Service PRODUCT and SERVICE from user's settings. ''' 
    PRODUCT, SERVICE = config['wave-product'], config['wave-service']

    ''' Set local directory to download NetCDF files to '''
    FORECAST = '/netcdf/waves/FORECAST/'     
    if not os.path.isdir(FORECAST):
        os.makedirs(FORECAST)

    # Set variable to download and mode to Near-Real-Time
    var, mode = 'VHM0', 'nrt'

    ''' Forecast '''      
    year, month, day = time.year, time.month, time.day

    # Date range to download forecast data 
    idate = datetime(year, month, day) - timedelta(days=1)
    edate = idate + timedelta(days=7)

    ''' Remove older forecast ''' 
    file = 'wave-forecast.nc'
    if os.path.isfile(FORECAST + file):
        os.remove(FORECAST + file)

    logger.info(' '); logger.info(f'{now()} Downloading forecast wave data...')
    Copernicus_Marine_Service_Download(USER, PSWD, PRODUCT, SERVICE, FORECAST, 
        file, lonmin, lonmax, latmin, latmax, idate, edate, var, mode)
