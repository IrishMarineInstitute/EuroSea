from datetime import datetime, timedelta
from pickle import dump
import json
from dateutil.parser import parse
from get_uv import get_uv
from glob import glob
import paramiko
import pysftp
import pandas as pd
import numpy as np
from pytz import timezone
import os
from log import set_logger, now

logger = set_logger()

def Buoy(conf):
    
    # Puertos del Estado INSTAC SFTP hostname and credentials    
    host, user, pswd, folder = conf['host'], conf['user'], conf['pswd'], conf['folder']
    logger.info(f'{now()} BUOY: Credentials are {host}, {user}, {pswd}, {folder}')
    
    localpath = '/xml'
    logger.info(f'{now()} BUOY: Localpath is {localpath}')
      
    # Retrieve names of *.xml files already downloaded and save to list
    local = update_local_directory(localpath, '.xml')
    logger.info(f'{now()} Local directory inspected. Number of files is {len(local)}')

    # Remove empty (corrupted) files
    files = sorted(glob(localpath + '/*.xml'))
    for file in files:        
        if is_empty(file):
            os.remove(file)
   
    # Download files
    try:
        xml_file_download(local, localpath, host, user, pswd, folder)         
    except paramiko.SSHException:
        pass
    
    # Remove empty (corrupted) files
    files = sorted(glob(localpath + '/*.xml'))
    for file in files:
        if is_empty(file):
            os.remove(file)
   
    # Update list of names of *.xml files already downloaded
    local = update_local_directory(localpath, '.xml')
   
    # Initialize dictionary of output variables    
    var = vardict() 

    logger.info(f'{now()} Reading files...')
    for f in local:
        read_xml_file(localpath + '/' + f, var)

    # Find u- and v- components of wind from wind speed and direction
    var['u-wind'], var['v-wind'] = get_uv(var['s-wind'], var['d-wind'], 'FROM') 

    # Apply a quality control (mask missing data)
    var = quality_control(var)    

    var = pd.DataFrame(var)
    # Resample at 10 minutes to ensure continuous time series
    var = var.resample('10T', on='time').mean()

    outdir = '/data/his/El-Campello/'
    if not ( os.path.isdir(outdir) ):
        os.makedirs(outdir)

    logger.info(f'{now()}: Saving historical records...')        
    with open(f'{outdir}El-Campello.pkl', 'wb') as f:
        dump(var, f)

    logger.info(f'{now()}: Quitting BUOY')  
    return var 

def is_empty(file):
    ''' Check if downloaded file is empty (silent, failed download) '''
    f = open(file, 'r')
    lines = f.readlines()
    if not lines:
        return True
    else:
        return False

def quality_control(var):

    for key in var.keys():
        var[key] = [i if ( i != 68. and i != 81. ) else np.nan for i in var[key]]

    return var

def read_xml_file(file, var):
    ''' Read an *.xml file and update the fields of interest '''

    # DCPS speed [cm/s] and direction [Deg.M]
    speed, direction = [], []    

    # Dictionary of new values
    new = {'time': 0, 'temp': 0, 'tur': 0, 'O2': 0,
        's-wind': 0, 'd-wind': 0, 
        'wave-height': 0, 'swell-height': 0,
        's-wave': 0, 'd-wave': 0,
        's-surface': 0, 'd-surface': 0,
        's-15m': 0, 'd-15m': 0}

    # Add some tests (check all variables are read in each file)
    checklist = {'time': False, 'temp': False, 'tur': False, 'O2': False,
            's-wind': False, 'd-wind': False,
            'wave-height': False, 'swell-height': False,
            'wave-period' : False, 'wave-direction': False,
            'speed': False, 'direction': False } 
    
    with open(file, 'r') as f:

        # Discard header
        for i in range(5): f.readline()

        line = f.readline()
        while len(line):

            if '<Time>' in line:
                                     
                new['time'] = find_time(line); checklist['time'] = True

            elif 'Descr="Water Temperature"' in line:
                 
                new['temp'] = find_value(f.readline()); checklist['temp'] = True

            elif 'Descr="Dissolved Oxygen"' in line:

                new['O2'] = find_value(f.readline()); checklist['O2'] = True

            elif 'Descr="Turbidity"' in line:       

                new['tur'] = find_value(f.readline()); checklist['tur'] = True

            elif '<Point ID="2">' in line:                             

                speed.append(find_value(f.readline(), f=f)); checklist['speed'] = True

            elif '<Point ID="3">' in line:

                direction.append(find_value(f.readline(), f=f)); checklist['direction'] = True

            elif 'Average Corrected Wind Diretion' in line:

                new['d-wind'] = find_value(f.readline()); checklist['d-wind'] = True

            elif 'Average Corrected Wind Speed' in line:

                new['s-wind'] = 3.6*find_value(f.readline()); checklist['s-wind'] = True

            elif 'Descr="Significant Wave Height Hm0"' in line: 

                new['wave-height'] = find_value(f.readline()); checklist['wave-height'] = True

            elif 'Descr="Wave Peak Direction"' in line:
                            
                new['d-wave'] = find_value(f.readline()); checklist['wave-direction'] = True

            elif 'Descr="Wave Peak Period"' in line:
                            
                new['s-wave'] = find_value(f.readline()); checklist['wave-period'] = True

            elif 'Descr="Wave Height Swell Hm0"' in line:
                            
                new['swell-height'] = find_value(f.readline()); checklist['swell-height'] = True

            # Read next line
            line = f.readline()
            
    # Check all required variables were successfully found in file
    for key, value in checklist.items():
        if not value:
            logger.debug(f'Variable {key} not found in file {file}'); return

    # Subset surface and 15-meter depth velocities from DCPS
    new['s-surface'], new['d-surface'] = speed[0], direction[0]
    new['s-15m'],     new['d-15m']   = speed[11], direction[11]

    # Append new values to historical structure
    for key, value in new.items():
        var[key].append(value)
    return
                 
def find_value(line, f=None):
    ''' Get numeric value from line of text '''
    if '<Value>' not in line:
        if f:
            line = f.readline()
            if '<Value>' not in line:
                return np.nan 
        else:
            return np.nan 
    i = line.find('e>') + 2
    e = line.find('</') 
    return float(line[i:e])    

def find_time(line):
    ''' Get time from line of text '''
    i = line.find('e>') + 2
    e = line.find('</') 
    return parse(line[i:e])    

def update_local_directory(localpath, extension):
    ''' Get a list with the names of *.xml files already downloaded '''
    local = []
    for file in os.listdir(localpath):
        if file.endswith(extension):
            local.append(file)
    return sorted(local)
         
def xml_file_download(local, localpath, host, user, pswd, folder):
    ''' Download *.xml files to local path using SFTP credentials '''
    logger.info(f'{now()} XML_FILE_DOWNLOAD Setting known hosts')
    cnopts = pysftp.CnOpts(knownhosts='known_hosts')
    # Open SFTP connection and start the download
    logger.info(f'{now()} XML_FILE_DOWNLOAD Opening SFTP connection')
    with pysftp.Connection(host=host, username=user, password=pswd, cnopts=cnopts) as sftp:
        logger.info(f'{now()} XML_FILE_DOWNLOAD Changing SFTP folder')
        sftp.cwd(folder)
        logger.info(f'{now()} XML_FILE_DOWNLOAD Running SFTP.LISTDIR()')
        for file in sftp.listdir():
            if ( file not in local ) and file[-4:] == '.xml':
                logger.info(f'{now()}: Downloading {file}'); 
                count = 0
                while count < 3:
                    try: 
                        sftp.get(file, localpath=localpath + '/' + file); 
                        if is_empty(localpath + '/' + file):
                            count += 1; continue
                        break
                    except paramiko.SSHException: count += 1; continue

def vardict():
    ''' Initialize empty dictionary for buoy data '''
    return {
            'time':  [], 'temp': [], 'tur': [], 'O2': [],

        's-wind': [], 'd-wind': [],

        'wave-height': [], 'swell-height': [],

        's-wave': [], 'd-wave': [],

        's-surface': [], 'd-surface': [], 's-15m': [], 'd-15m': []

           }       
