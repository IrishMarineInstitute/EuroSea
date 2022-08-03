from netCDF4 import Dataset, num2date
import numpy as np
from datetime import date, datetime
from webob import exc

# Set boundaries (W, E, S, N)
xmin, xmax, ymin, ymax = -11.6, -8, 50, 52.8

url = 'https://thredds.jpl.nasa.gov/thredds/dodsC/OceanTemperature/MUR-JPL-L4-GLOB-v4.1.nc'

def nearest(lista, valor):
    return np.argmin(abs(lista - valor))

def main():
    ''' Reads from Multi-scale Ultra-high Resolution Sea Surface Temperature '''
    
    print('\nOpening dataset MUR-JPL-L4-GLOB-v4.1...')
    with Dataset(url) as nc:
        
        lon = nc.variables['lon'][:]
        x0, x1 = nearest(lon, xmin), nearest(lon, xmax) + 1
        lon = lon[x0 : x1]
        L = len(lon)
        
        lat = nc.variables['lat'][:]
        y0, y1 = nearest(lat, ymin), nearest(lat, ymax) + 1
        lat = lat[y0 : y1]
        M = len(lat)
        
        # Read latest time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        
    # Convert time to datetime
    tiempo = []
    for i in time:
        yy, mm, dd = i.year, i.month, i.day
        tiempo.append(date(yy, mm, dd))
    time = [(i - tiempo[0]).days for i in tiempo]
        
    with Dataset('MUR.nc', 'w') as f, Dataset(url) as nc:
        
        # Create global attributes 
        f.creation_date = datetime.now().strftime('%d-%b-%Y %H:%M')
        f.dataset_id = 'Multi-scale Ultra-high Resolution Sea Surface Temperature'
          
        # Create dimensions 
        f.createDimension('longitude', L)
        f.createDimension('latitude', M)   
        f.createDimension('time', 0)    
                
        # Create variables 
        londim = f.createVariable('longitude', 'f4', 
            dimensions=('longitude'), zlib=True)
        londim.standard_name = 'longitude'
        londim.units = 'degree_east'
        londim[:] = lon
        #
        latdim = f.createVariable('latitude', 'f4', 
            dimensions=('latitude'), zlib=True)
        latdim.standard_name = 'latitude'
        latdim.units = 'degree_north'
        latdim[:] = lat
        # 
        timedim = f.createVariable('time', 'f8', 
            dimensions=('time'), zlib=True)
        timedim.standard_name = 'time'
        timedim.units = 'days since 2002-06-01'
        #
        sst = f.createVariable('SST', 'f4',
            dimensions=('time', 'latitude', 'longitude'), zlib=True)
        sst.standard_name = 'sea_surface_temperature'
        sst.units = 'Celsius'
                        
        for C, (i, j) in enumerate(zip(time, tiempo)):        
            
            print(j)
            
            timedim[C] = i            
            
            while True:
            
                try:
                    
                    SST = nc.variables['analysed_sst'][C, y0 : y1, x0 : x1] - 273.15
                    
                    sst[C, :, :] = SST
                    
                    break
                
                except RuntimeError: continue
            
                except exc.HTTPError: continue
            
if __name__ == '__main__':
    main()        
    