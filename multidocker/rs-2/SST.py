from datetime import datetime
from netCDF4 import Dataset, num2date
from cftime import DatetimeGregorian
from mhw import mhw_processing
from webob import exc
import numpy as np
from log import set_logger, now

logger = set_logger()

def SST(time_c, seas, pc90, mask, dia, boundaries):
    ''' Retrieves SST requested from the web for given date '''
    
    dia = datetime.strptime(dia, '%Y-%m-%d')
    dia = DatetimeGregorian(dia.year, dia.month, dia.day, 9)
    
    xmin, xmax, ymin, ymax = boundaries
    
    url = 'https://thredds.jpl.nasa.gov/thredds/dodsC/OceanTemperature/MUR-JPL-L4-GLOB-v4.1.nc'

    with Dataset(url) as nc:
         
         while True:
         
             try:
                                 
                 lon = nc.variables['lon'][:]
                 x0, x1 = nearest(lon, xmin), nearest(lon, xmax) + 1
                 
                 lat = nc.variables['lat'][:]
                 y0, y1 = nearest(lat, ymin), nearest(lat, ymax) + 1
                 
                 # Read latest time
                 time = num2date(nc.variables['time'][:], nc.variables['time'].units)
                 
                 i = np.where(time == dia)[0][0]
                 
                 # Read SST
                 SST = nc.variables['analysed_sst'][i - 4 : i + 1, y0 : y1, x0 : x1] - 273.15
                 
                 break
             
             except RuntimeError: continue
         
             except exc.HTTPError: continue
         
    # Subset time for 5 days before selected date
    time = time[i - 4 : i + 1]
    # Convert to Python datetime
    time = [datetime(i.year, i.month, i.day, i.hour) for i in time]
        
    # Get day of year of selected date
    latest = time[-1].timetuple().tm_yday
    # Find time index in climatology
    i = np.where(time_c == latest)[0][0]
    # Get climatology SST distribution for selected day of the year    
    seas = seas[i, :, :]
    # Get 90-th percentile SST distribution for selected day of the year
    pc90 = pc90[i - 4 : i + 1, :, :]
    # Get SST anomaly as the difference between actual SST and climatology
    ANOM = SST[-1, :, :] - seas
    
    # Marine Heat Waves
    MHS, MHW, MHT = mhw_processing(lon[x0 : x1], lat[y0 : y1], np.array(time), SST, pc90)

    # Apply mask 

    logger.info('SST shape is: ' + str(SST.shape))
    logger.info('ANOM shape is: ' + str(ANOM.shape))
    logger.info('MHW shape is: ' + str(MHW.shape))
    ANOM = maska(ANOM, mask); MHW = maska(MHW, mask) 
                 
    return lon[x0 : x1], lat[y0 : y1], time[-1], SST[-1, :, :], ANOM, MHW

def nearest(lista, valor):
    return np.argmin(abs(lista - valor))

def maska(A, mask):
    A[mask==1] = np.nan
    return A
