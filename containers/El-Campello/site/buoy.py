from datetime import datetime, timedelta
from pickle import dump
import json
from dateutil.parser import parse
from get_uv import get_uv
from glob import glob
import paramiko
import pysftp
from numpy import nan as NaN
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

    # Get number of levels for Doppler Current Profiler
    N = len(json.loads(conf['DCPS']))

    # Remove empty (corrupted) files
    files = sorted(glob(localpath + '/*.xml'))
    for file in files:
        logger.info(file)
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

    ''' This section is meant to guarantee that:

        1 - A constant time step (10 minutes) exists

        2 - Files are processed in the right order '''

    # Start reading from the first file. Take date from first file.

    idate = timezone('UTC').localize(datetime.strptime(local[0][0:12] + '0', '%Y%m%dT%H%M'))

    logger.info(f'{now()} Start time is {idate.strftime("%Y-%b-%d %H:%M")}')


     # Next, determine the end time, matching the latest downloaded file

    edate = timezone('UTC').localize(datetime.strptime(local[-1][0:12] + '0', '%Y%m%dT%H%M'))

    logger.info(f'{now()} End time is {edate.strftime("%Y-%b-%d %H:%M")}')


     # Now, create time list from "idate" to "edate" with 10-minute intervals

    tiempo = []
    
    while idate <= edate:
    
         # Add a new time to the list of times to be processed
         tiempo.append(idate)
    
         # Update (add +10 minutes)
         idate += timedelta(minutes=10)
     
    
    for i in tiempo: 
    
        if not i.hour and not i.minute:
            logger.info(f'{now()}: Reading ' + i.strftime('%d-%b-%Y %H:%M'))        
    
        file = ''
    
        # Convert time to string. The time string defines the XML file name 
    
        dateString = i.strftime('%Y%m%dT%H%M')         
    
        # Search for file names containing the above date string.
    
        for f in local:
    
            if dateString in f:
    
                file = f; break
    
        if file:
    
            read_xml_file(localpath + '/' + file, var)
    
        else:
    
            # There is a missing file, not transmitted by the buoy
    
            logger.info(f'{now()}: WARNING! Missing file for {dateString}. Appending NaN...')
    
            for key in var.keys(): 
                var[key].append(NaN) # Append NaN to all the variables in the data structure.

            # For time, append the i-th time
            var['time'][-1] = i

            # For Doppler Current Profile variables (speed and direction) a list of NaN's 
            # must be appended. The length must be "N" number of levels in the DCP sensor.
            var['DCP speed'][-1] = [NaN for k in range(N)]
            var['DCP dir'][-1] = [NaN for k in range(N)]

    # Apply a quality control (mask missing data)
    var = quality_control(var)    
  
    ''' Calculation of derived variables '''
    # Find u- and v- components of wind from wind speed and direction
    var['u-wind'], var['v-wind'] = get_uv(var['Wind Speed'], var['Wind Direction'], 'FROM') 

    outdir = '/data/HISTORY/El-Campello-in-situ'
    if not ( os.path.isdir(outdir) ):
        os.makedirs(outdir)

    logger.info(f'{now()}: Saving historical records...')        
    with open('%s/El-Campello-in-situ.pkl' % outdir, 'wb') as f:
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
        var[key] = [i if ( i != 68. and i != 81. ) else NaN for i in var[key]]

    return var

def read_xml_file(file, var):
    ''' Read an *.xml file and update the fields of interest '''

    # Prepare DCPS lists. For "El Campello", these lists should have
    # 28 values for each time step: 8 (C1) + 20 (C2).  

    speed = []     # DCPS speed [cm/s]
    direction = [] # DCPS direction Deg.M
    
    with open(file, 'r') as f:

        # Discard header
        for i in range(5): f.readline()

        line = f.readline()
        while len(line):

            if '<Time>' in line:
                                     
                var['time'].append(find_time(line))

            elif 'Descr="Water Temperature"' in line:
                 
                var['Temperature'].append(find_value(f.readline()))

            elif 'Descr="Dissolved Oxygen"' in line:

                var['Oxygen Saturation'].append(find_value(f.readline()))

            elif 'Descr="Turbidity"' in line:       

                var['TUR'].append(find_value(f.readline()))

            elif '<Point ID="2">' in line:                             

                speed.append(find_value(f.readline()))

            elif '<Point ID="3">' in line:

                direction.append(find_value(f.readline()))

            elif 'Average Corrected Wind Diretion' in line:

                var['Wind Direction'].append(find_value(f.readline()))

            elif 'Average Corrected Wind Speed' in line:

                var['Wind Speed'].append(3.6*find_value(f.readline()))

            elif 'Descr="Significant Wave Height Hm0"' in line: 
                var['Significant Wave Height Hm0'].append(find_value(f.readline()))

            elif 'Descr="Wave Peak Direction"' in line:
                var['Wave Peak Direction'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Peak Period"' in line:
                var['Wave Peak Period'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Height Wind Hm0"' in line:
                var['Wave Height Wind Hm0'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Height Swell Hm0"' in line:
                var['Wave Height Swell Hm0'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Peak Period Wind"' in line:
                var['Wave Peak Period Wind'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Peak Period Swell"' in line:
                var['Wave Peak Period Swell'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Peak Direction Wind"' in line:
                var['Wave Peak Direction Wind'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Peak Direction Swell"' in line:
                var['Wave Peak Direction Swell'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Mean Direction"' in line:
                var['Wave Mean Direction'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Height Hmax"' in line:
                var['Wave Height Hmax'].append(find_value(f.readline()))
                            
            elif 'Descr="Wave Mean Period T1/3"' in line:
                var['Wave Mean Period T1/3'].append(find_value(f.readline()))
                            
            # Read next line
            line = f.readline()
            
    ''' Add DCPS recordings to in-situ data structure'''
    var['DCP speed'].append(speed)
    var['DCP dir'].append(direction)
                 
def find_value(line):
    ''' Get numeric value from line of text '''
    if '<Value>' not in line:
        return NaN
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
                while 1:
                    try: 
                        sftp.get(file, localpath=localpath + '/' + file); 
                        if is_empty(localpath + '/' + file):
                            continue
                        break
                    except paramiko.SSHException: continue

def vardict():
    ''' Initialize empty dictionary for buoy data '''
    return {
        'time':  [], 

        # YSI EXO3  
        'Temperature': [],
        'TUR':    [],
        'Oxygen Saturation':  [], 

        # Gill MaxiMet 200-2
        'Wind Speed': [],
        'Wind Direction': [],
        'u-wind': [], 
        'v-wind': [],

        # Motus Wave Sensor
        'Significant Wave Height Hm0': [],
        'Wave Peak Direction': [],
        'Wave Peak Period': [],
        'Wave Height Wind Hm0': [],
        'Wave Height Swell Hm0': [],
        'Wave Peak Period Wind': [],
        'Wave Peak Period Swell': [],
        'Wave Peak Direction Wind': [],
        'Wave Peak Direction Swell': [],
        'Wave Mean Direction': [],
        'Wave Height Hmax': [],
        'Wave Mean Period T1/3': [],

        # Doppler Current Profiler Sensor
        'DCP speed': [],
        'DCP dir': []
           }       
