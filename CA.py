from netCDF4 import Dataset, num2date
from datetime import date
from shutil import rmtree, copy
from glob import glob
import platform
import numpy as np
import os

# Set boundaries (W, E, S, N)
xmin, xmax, ymin, ymax = -11.6, -8, 50, 52.8

def CA():
    
    # Clean older files and create new output directory
    if os.path.isdir('CHLA'):
        rmtree('CHLA')   
    os.mkdir('CHLA')
    
    # Get OS
    OS = platform.system()
    
    # Get current year
    YYYY = date.today().year
    
    if OS == 'Windows': # In Windows, connect remotely to Tethys server, 
                        # where chlorophyll data is stored
                        
        from SSHLibrary import SSHLibrary    
            
        ssh = SSHLibrary()
        # Open SSH connection with Tethys
        ssh.open_connection("10.0.5.73")
        # Login
        ssh.login("matlab", "Matlab")
           
        # Download CHLA file 
        CHLA = download(ssh, f'/home/Merged_CHLA/{YYYY}/NETCDF/*.nc', 'analysed_chl_a') 
        os.rename(CHLA, 'CHLA/' + CHLA)
        
        # Download Anomaly file
        ANOM = download(ssh, f'/home/Merged_CHLA/{YYYY}/NETCDF/Anomaly/*.nc', 'chl_anomaly') 
        os.rename(ANOM, 'CHLA/' + ANOM)
        
        # Close SSH connection
        ssh.close_all_connections()
        
    elif OS == 'Linux': # Assume the code is being run in Tethys.
                        # So, chlorophyll files are local, no need to download
        
        # Check CHLA files
        CHLA = check_files(f'/home/Merged_CHLA/{YYYY}/NETCDF/*.nc', 'analysed_chl_a')
        os.rename(CHLA, 'CHLA/' + CHLA)
        
        # Check Anomaly files
        ANOM = check_files(f'/home/Merged_CHLA/{YYYY}/NETCDF/Anomaly/*.nc', 'chl_anomaly')
        os.rename(ANOM, 'CHLA/' + ANOM)
                
    # Read chlorophyll data    
    x_chl, y_chl, time_chl, chl = read_chl('CHLA/' + CHLA)
    
    # Read anomaly data
    time_anom, anom = read_anom('CHLA/' + ANOM)
    
    try:
        assert np.array_equal(time_chl, time_anom)
    except AssertionError:
        print('\nChlorophyll time and Anomaly time do not match! Trying again...')
        return ()
    
    return x_chl, y_chl, time_chl[0], chl, anom
    
    
def nearest(lista, valor):
    return np.argmin(abs(lista - valor))        


def download(ssh, folder, var):
    ''' Downloads the latest available NetCDF file in specified folder '''
    
    while 1:
        # Get "ls" output for folder
        output, code = ssh.execute_command(f'ls {folder}',
            return_rc=True, return_stdout=True)
        if not code:
            break
        else:
            continue
        
    C, nodata = 0, []
    
    while 1:
        C -= 1
        # Get name of latest available file
        filename = output.split('\n')[C]; name = filename.split('/')[-1]
        # Download
        print(f'\nDownloading {name}...')
        ssh.get_file(filename, '.')
        # Check file
        with Dataset(name, 'r') as nc:
            data = nc.variables[var][:]
            if data.mask.all(): 
                print('No data in this file. Trying with the previous one...')
                nodata.append(name); continue
            else:
                break

    # Clean directory
    for f in nodata:
        os.remove(f)
        
    return name

def check_files(folder, var):
    ''' Check chlorophyll files in Tethys to find the one with the latest available data '''
    
    C, nodata = 0, []
    # Get directory NetCDF files list
    lista = glob(folder)
    
    while 1:
        C -= 1
        # Get name of latest available file
        filename = lista[C]; name = filename.split('/')[-1]
        # Copy to working directory
        print(f'\nCopying {name}...')
        copy(filename, '.')
        # Check file
        with Dataset(name, 'r') as nc:
            data = nc.variables[var][:]
            if data.mask.all(): 
                print('No data in this file. Trying with the previous one...')
                nodata.append(name); continue
            else:
                break
            
    # Clean directory
    for f in nodata:
        os.remove(f)
        
    return name    

def read_chl(file):
    ''' Reads chlorophyll-a data '''
    
    with Dataset(file, 'r') as nc:
        
        # Read longitude
        lon = nc.variables['lon'][:]
        x0, x1 = nearest(lon, xmin), nearest(lon, xmax) + 1
        lon = lon[x0 : x1]
        
        # Read latitude
        lat = nc.variables['lat'][:]
        y0, y1 = nearest(lat, ymin), nearest(lat, ymax) + 1
        lat = lat[y0 : y1]
        
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        
        # Read chlorophyll-a
        CHLA = nc.variables['analysed_chl_a'][0, y0 : y1, x0 : x1]
        
        return lon, lat, time, CHLA
    
    
def read_anom(file):
    ''' Reads chlorophyll-a anomaly '''
    
    with Dataset(file, 'r') as nc:
        
        # Read longitude
        lon = nc.variables['longitude'][:]
        x0, x1 = nearest(lon, xmin), nearest(lon, xmax) + 1      
        
        # Read latitude
        lat = nc.variables['latitude'][:]
        y0, y1 = nearest(lat, ymin), nearest(lat, ymax) + 1       
        
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        
        # Read chlorophyll-a
        ANOM = nc.variables['chl_anomaly'][0, y0 : y1, x0 : x1]
        
        return time, ANOM