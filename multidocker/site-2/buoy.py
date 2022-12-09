from datetime import datetime, timedelta
from dateutil.parser import parse
import paramiko
import pysftp
from numpy import nan as NaN
from pytz import timezone
import numpy as np
import pickle
import os
from math import sin, cos, pi
from log import set_logger, now

logger = set_logger()


DEG2RAD = pi/180 # Conversion factor from degrees to radians

def Buoy(conf):
    
    # Puertos del Estado INSTAC SFTP hostname and credentials    
    host, user, pswd, folder = conf['host'], conf['user'], conf['pswd'], conf['folder']
    logger.info(f'{now()} BUOY: Credentials are {host}, {user}, {pswd}, {folder}')
    
    localpath = '/xml-2'
    logger.info(f'{now()} BUOY: Localpath is {localpath}')
      
    # Retrieve names of *.xml files already downloaded and save to list
    local = update_local_directory(localpath, '.xml')
    logger.info(f'{now()} Local directory inspected. Number of files is {len(local)}')
   
    # Download files
    try:
        xml_file_download(local, localpath, host, user, pswd, folder)         
    except paramiko.SSHException:
        pass
    
    # Update list of names of *.xml files already downloaded
    local = update_local_directory(localpath, '.xml')
   
    pickle_file = '/data/buoy-2.pkl'
    if os.path.isfile(pickle_file):
        # Load buoy data from older download        
        with open(pickle_file, 'rb') as file:
            var = pickle.load(file)
        # Get latest time
        latest = var['time'][-1].strftime('%Y%m%dT%H%M')
        # Find index of file matching latest time
        i = -1 # ... in case local directory is empty
        for i, file in enumerate(local):
            if file[0:13] == latest: 
                break
        local = local[i+1:]
    else:       
        # Initialize dictionary of output variables    
        var = vardict() 
    
    for file in local:
        tempo = datetime.strptime(file[0:13], '%Y%m%dT%H%M')
        if not tempo.hour and not tempo.minute:
            logger.info(f'{now()}: Reading ' + tempo.strftime('%d-%b-%Y %H:%M'))        
        read_xml_file(localpath + '/' + file, var, conf)
        
    # Apply a quality control (mask missing data)
    var = quality_control(var)    
        
    # Update pickle file
    with open(pickle_file, 'wb') as file:
        pickle.dump(var, file)
    logger.info(f'{now()}: Quitting BUOY')  
    return var 

def quality_control(var):
    ''' This function makes sure that the time array is evenly-spaced with a
    constant time step of 10 minutes until present. If data is not available,
    missing data is marked as NaN. '''
    
    # Mask missing data
    for key in var.keys():
        var[key] = [i if ( i != 68. and i != 81. ) else NaN for i in var[key]]
        
    # Initialize dictionary of output variables    
    new = vardict()
    
    # Get original time array
    time = np.array(var['time'])
    # Set latest date (today, if no data available until today)
    today = datetime.now()
    # Add timezone information
    today = timezone('UTC').localize(today)
    
    #  Set start and end date
    idate, edate = time[0], max(time[-1], today)
    while idate <= edate:
        # Make sure all times between idate and edate are in the new dictionary
        new['time'].append(idate)
        try: 
            i = np.where(idate == time)[0][0] # If time exists in dataset...
            for key in new.keys():
                if key != 'time':
                    new[key].append(var[key][i]) # ... append existing data, of course
        except IndexError: # If time does not exist in dataset...
            for key in new.keys():
                if key != 'time':
                    new[key].append(NaN) # ... append NaN
        idate += timedelta(minutes=10)
            
    return new
    

def read_xml_file(file, var, config):
    ''' Read an *.xml file and updates the fields of interest '''
    
    # SET MID-WATER AND SEABED DCPS CELL INDEXES AS PER CONFIG FILE
    SUR, MID, BOT = int(config['SUR']), int(config['MID']), int(config['BOT'])
    
    with open(file, 'r') as f:
        # Discard header
        for i in range(5): f.readline()
        line = f.readline()
        while len(line):
            if '<Time>' in line:
                var['time'].append(find_time(line))
            elif 'Descr="Water Temperature"' in line:
                var['Temperature'].append(find_value(f.readline()))
            elif 'Descr="Salinity"' in line:
                var['Salinity'].append(find_value(f.readline()))
            elif 'Descr="Dissolved Oxygen"' in line:
                var['Oxygen Saturation'].append(sat_to_c(find_value(f.readline())))
            elif 'Descr="Turbidity"' in line:
                var['pH'].append(find_value(f.readline()))
            elif 'Descr="Chlorophyll"' in line:
                var['RFU'].append(rfu_to_c(find_value(f.readline())))
            elif f'Cell Index="{SUR}"' in line:
                if ( len(var['u0']) == len(var['time']) ): 
                    line = f.readline(); continue
                u, v = get_cartesian(f)
                var['u0'].append(u); var['v0'].append(v);        
            elif f'Cell Index="{MID}"' in line:
                if ( len(var['umid']) == len(var['time']) ):
                    line = f.readline(); continue
                u, v = get_cartesian(f)
                var['umid'].append(u); var['vmid'].append(v);
            elif f'Cell Index="{BOT}"' in line:
                if ( len(var['ubot']) == len(var['time']) ):
                    line = f.readline(); continue
                u, v = get_cartesian(f)
                var['ubot'].append(u); var['vbot'].append(v);
            elif 'Average Corrected Wind Diretion' in line:
                wind_direction = find_value(f.readline())
            elif 'Average Corrected Wind Speed' in line:
                wind_speed = find_value(f.readline())
                var['uwind'].append(wind_speed * cos ( DEG2RAD * ( 90 - wind_direction ) ))
                var['vwind'].append(wind_speed * sin ( DEG2RAD * ( 90 - wind_direction ) ))
                            
            # Read next line
            line = f.readline()
                
def get_cartesian(f):
    ''' Extract u, v components from .xml file '''    
    C = 0
    while 1:
        line = f.readline()
        if 'Value' in line:
            C += 1
            if C == 3:
                r = find_value(line)
            elif C == 4:
                D = find_value(line); break
        if 'Cell Index' in line:
            raise RuntimeError('Could not find velocity components in .xml file')
            
    if ( r == 68 ) and ( D == 68 ): r, D = NaN, NaN
    u = r * cos ( DEG2RAD * ( 90 - D ) ) # Get u-component
    v = r * sin ( DEG2RAD * ( 90 - D ) ) # Get v-component
    return u, v
        
def find_value(line):
    ''' Get numeric value from line of text '''
    i = line.find('e>') + 2
    e = line.find('</') 
    return float(line[i:e])    

def find_time(line):
    ''' Get time from line of text '''
    i = line.find('e>') + 2
    e = line.find('</') 
    return parse(line[i:e])    

def sat_to_c(sat):
    ''' TODO: Convert Dissolved Oxygen Saturation (%) to
            Dissolved Oxygen Concentration '''
    return sat

def rfu_to_c(rfu):
    ''' TODO: Convert Reference Fluorescence Units to
            actual Chlorophyll-a Concentration '''
    return rfu
            
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
                while 1:
                    try: 
                        sftp.get(file, localpath=localpath + '/' + file); break
                    except paramiko.SSHException: continue

def vardict():
    ''' Initialize empty dictionary for buoy data '''
    return {
        'time':  [], 'Temperature': [], 'Salinity':           [], 
        'pH':    [], 'RFU':     [], 'Oxygen Saturation':  [], 
        'u0':    [], 'v0':          [],
        'umid':  [], 'vmid':        [],
        'ubot':  [], 'vbot':        [],
        'uwind': [], 'vwind':       [],
           }       