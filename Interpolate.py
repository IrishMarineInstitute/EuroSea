from scipy.interpolate import interp2d
from netCDF4 import Dataset
from glob import glob
import numpy as np

def nws2mur(DBO):
    
    # First, read Northwest Shelf grid
    f = glob('NWSHELF/NWSHELF-TEMP-2D-*.nc')[0]
    with Dataset(f, 'r') as nc:
        lon, lat = nc.variables['lon'][:], nc.variables['lat'][:]
        
    # Create regular grid (NWSHELF)
    X, Y = np.meshgrid(lon, lat)

    # Create regular grid (SST)
    Xsat, Ysat = np.meshgrid(DBO.sst_x, DBO.sst_y)

    # Get output dimensions
    _, M, L = DBO.sst.shape # same horizontal dimensions as SST array
    
    T = len(DBO.time2d) # but interpolate for each time in the NWSHELF model
    
    # Create output array
    temp2d = np.empty((T, M, L))
        
    print('\nInterpolating NWSHELF into satellite grid')
    for i, time in enumerate(DBO.time2d):
        
        # Get NWSHELF data for i-th time
        z = np.asarray(DBO.temp2d[i, :, :])
        
        nan_map = np.zeros_like( z )
        # Find where are missing values (land)
        nan_map[ np.isnan(z) ] = 1
        
        filled_z = z.copy()
        # Set missing values to 0
        filled_z[ np.isnan(z) ] = 0
        
        # Create interpolant
        f = interp2d(lon, lat, filled_z, kind='linear')
        # Create mask interpolant
        mask = interp2d(lon, lat, nan_map, kind='linear')     
        
        # Interpolate model temperature to satellite grid
        temp = f(DBO.sst_x, DBO.sst_y)
        # Interpolate mask to satellite grid
        mask = mask(DBO.sst_x, DBO.sst_y )
        # Apply mask
        temp[ mask > 0.1 ] = np.nan
        
        # Write into output array
        temp2d[i, :, :] = temp
    
    return temp2d