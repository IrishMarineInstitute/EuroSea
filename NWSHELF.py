from datetime import date, datetime, timedelta
from netCDF4 import Dataset, num2date
from pandas import Timestamp
import motuclient
import numpy as np
import os
import xarray as xr

# Set CMEMS credentials
USERNAME, PASSWORD = 'dpereiro1', 'Marciano7!'

# Set boundaries (W, E, S, N)
xmin, xmax, ymin, ymax = -11.6, -8, 50, 52.8

class MotuOptions:
    def __init__(self, attrs: dict):
        super(MotuOptions, self).__setattr__("attrs", attrs)

    def __setattr__(self, k, v):
        self.attrs[k] = v

    def __getattr__(self, k):
        try:
            return self.attrs[k]
        except KeyError:
            return None
        
#! /usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Copernicus Marine User Support Team"
__copyright__ = "(C) 2021 E.U. Copernicus Marine Service Information"
__credits__ = ["E.U. Copernicus Marine Service Information"]
__license__ = "MIT License - You must cite this source"
__version__ = "202105"
__maintainer__ = "D. Bazin, E. DiMedio, J. Cedillovalcarce, C. Giordan"
__email__ = "servicedesk dot cmems at mercator hyphen ocean dot eu"

def motu_option_parser(script_template, usr, pwd, output_directory, output_filename):
    dictionary = dict(
        [e.strip().partition(" ")[::2] for e in script_template.split('--')])
    dictionary['variable'] = [value for (var, value) in [e.strip().partition(" ")[::2] for e in script_template.split('--')] if var == 'variable']  # pylint: disable=line-too-long
    for k, v in list(dictionary.items()):
        if v == '<OUTPUT_DIRECTORY>':
            dictionary[k] = output_directory
        if v == '<OUTPUT_FILENAME>':
            dictionary[k] = output_filename
        if v == '<USERNAME>':
            dictionary[k] = usr
        if v == '<PASSWORD>':
            dictionary[k] = pwd
        if k in ['longitude-min', 'longitude-max', 'latitude-min', 
                 'latitude-max', 'depth-min', 'depth-max']:
            dictionary[k] = float(v)
        if k in ['date-min', 'date-max']:
            dictionary[k] = v[1:-1]
        dictionary[k.replace('-','_')] = dictionary.pop(k)
    dictionary.pop('python')
    dictionary['auth_mode'] = 'cas'
    return dictionary

def read_nwshelf(DBO, PRODUCT, USERNAME, PASSWORD):
   
    prefix = 'NWSHELF-TEMP-2D-'
    
    OUTPUT_DIRECTORY = 'NWSHELF'
    
    print('\n')
    
    # Set forecast period (from today to five days ahead)
    times = np.array([date.today() + timedelta(days=i) for i in range(6)])
    # Append forecast period to remote-sensing period
    times = np.append(DBO.sst_time, times)
    
    for i in times: # Download Northwest Shelf data for each day in SST + forecast
        
        Y, M, D = i.year, i.month, i.day
        
        # MUR-SST data is referred to 9 a.m.
        fecha = datetime(Y, M, D, 9).strftime("%Y-%m-%d %H:%M:%S")
        
        OUTPUT_FILENAME = prefix + datetime(Y, M, D).strftime('%Y%m%d') + '.nc'        
        if os.path.exists(OUTPUT_DIRECTORY + '/' + OUTPUT_FILENAME):
            continue
        
        print(f'Downloading Northwest Shelf temperature for date {fecha}')
        
        # Set template
        script_template = ('python -m motuclient '
                           '--motu https://nrt.cmems-du.eu/motu-web/Motu '
                           '--service-id NORTHWESTSHELF_ANALYSIS_FORECAST_PHY_004_013-TDS '
                           f'--product-id {PRODUCT} '
                           f'--longitude-min {xmin} --longitude-max {xmax} '
                           f'--latitude-min {ymin} --latitude-max {ymax} '
                           f'--date-min "{fecha}" --date-max "{fecha}" ' 
                           '--out-dir <OUTPUT_DIRECTORY> '
                           '--out-name <OUTPUT_FILENAME> '
                           '--user <USERNAME> --pwd <PASSWORD>'
                           )
        # Prepare request
        data_request = motu_option_parser(script_template, 
            USERNAME, PASSWORD, OUTPUT_DIRECTORY, OUTPUT_FILENAME)
        
        # while 1: 
            # Download
        motuclient.motu_api.execute_request(MotuOptions(data_request))
        
            # # Check that file exists
            # if not os.path.exists(OUTPUT_DIRECTORY + '/' + OUTPUT_FILENAME):
            #     continue # try again...
            # else:
            #     break
    
    with xr.open_mfdataset('NWSHELF/' + prefix + '*.nc') as nc:
        # Read time
        time = nc.time.data
        if 'SST' in PRODUCT:
            # Read temperature
            var = nc.thetao.data
        elif 'SSS' in PRODUCT:
            # Read salinity
            var = nc.so.data
            
    time = [Timestamp(i) for i in time]
   
    return time, var

def gregorian_to_datetime(time):
    return [datetime(i.year, i.month, i.day, i.hour) for i in time]

def read_nwshelf_farm(DBO, PRODUCT, USERNAME, PASSWORD):
    
    # Deenish Island farm coordinates
    lonmin, lonmax, latmin, latmax = -10.2122, -10.2120, 51.7431, 51.7433
    
    t0 = DBO.buoy['time'][0].strftime("%Y-%m-%d 00:00:00")
    t1 = (date.today() + timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S")
    
    OUTPUT_DIRECTORY = 'NWSHELF'
    
    if 'SST' in PRODUCT:
        print('\nDownloading temperature from Northwest Shelf model for Deenish Island...\n')
        OUTPUT_FILENAME = 'NWSHELF-TEMP-Deenish.nc'
    elif 'SSS' in PRODUCT:
        print('\nDownloading salinity from Northwest Shelf model for Deenish Island...\n')
        OUTPUT_FILENAME = 'NWSHELF-SALT-Deenish.nc'
    # Set template
    script_template = ('python -m motuclient '
                       '--motu https://nrt.cmems-du.eu/motu-web/Motu '
                       '--service-id NORTHWESTSHELF_ANALYSIS_FORECAST_PHY_004_013-TDS '
                       f'--product-id {PRODUCT} '
                       f'--longitude-min {lonmin} --longitude-max {lonmax} '
                       f'--latitude-min {latmin} --latitude-max {latmax} '
                       f'--date-min "{t0}" --date-max "{t1}" '
                       '--out-dir <OUTPUT_DIRECTORY> '
                       '--out-name <OUTPUT_FILENAME> '
                       '--user <USERNAME> --pwd <PASSWORD>'
                       )
    
    data_request_options_dict_automated = motu_option_parser(script_template, 
        USERNAME, PASSWORD, OUTPUT_DIRECTORY, OUTPUT_FILENAME)
    # Download 
    motuclient.motu_api.execute_request(MotuOptions(data_request_options_dict_automated))
    
    with Dataset('NWSHELF/' + OUTPUT_FILENAME) as nc:
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        if 'SST' in PRODUCT:
            # Read temperature
            var = np.squeeze(nc.variables['thetao'][:])
        elif 'SSS' in PRODUCT:
            # Read salinity
            var = np.squeeze(nc.variables['so'][:])
   
    return time, var

def download_nws(DBO, suffix, variable, pid):
    
    # Check if there is need to download file
    if os.path.exists('NWSHELF/' + f'NWSHELF-{suffix}.nc'):
        
        # If file exists, open it
        with Dataset('NWSHELF/' + f'NWSHELF-{suffix}.nc') as nc:
            
            # Read latest time step...
            latest = num2date(nc.variables['time'][-1], nc.variables['time'].units)
            # ... and convert to datetime
            latest = date(latest.year, latest.month, latest.day)
            
            # Latest time step should be 6 days ahead of today
            if latest == date.today() + timedelta(days=6): 
                # Read time
                time = num2date(nc.variables['time'][:], nc.variables['time'].units)
                # Read temperature
                data = np.squeeze(nc.variables[variable][:])
                
                return time, data        
   
    if '2D' in suffix:
        time, data = read_nwshelf(DBO, f'MetO-NWS-PHY-{pid}', USERNAME, PASSWORD)
    else:
        time, data = read_nwshelf_farm(DBO, f'MetO-NWS-PHY-{pid}', USERNAME, PASSWORD)     
    
    time = np.asarray([datetime(i.year, i.month, i.day, i.hour) for i in time])
    
    return time, data
    

def read_nws(DBO, var):
    ''' Download Norhtwest Shelf model temperature and salinity '''
    
    # Prepare output directory
    if not os.path.isdir('NWSHELF'):
        os.mkdir('NWSHELF')
        
    if var == 'T':
        suffix, variable, pid = 'TEMP', 'thetao', 'hi-SST'
    elif var == 'S':
        suffix, variable, pid = 'SALT', 'so', 'hi-SSS'
        
    # Download model temperature (var = 'T') or salinity (var = 'S') forecast at Deenish Island
    time, data = download_nws(DBO, suffix + '-Deenish', variable, pid)
    
    time2d, data2d = None, None
    if var == 'T': # For temperature, download the whole domain too
        time2d, data2d = download_nws(DBO, suffix + '-2D', variable, pid)
        
    time = gregorian_to_datetime(time)
        
    return time, time2d, data, data2d