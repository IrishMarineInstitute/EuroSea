from datetime import datetime, timedelta
from wind_rose import wind_rose
from output import send_output
from pytz import timezone
from pickle import load
import numpy as np
import to_csv
import json

def prepare_wind_rose(r, D):
    
    r, D = np.array(r), np.array(D)

    return np.vstack((r, D)).T

def address_request(start, end, uv, language='en'):
    ''' Subset in-situ data for the requested dates '''

    config = configuration()

    # DCPS depths (m)
    DCPS = config['DCPS']

    # Load historical buoy data
    f = '/data/HISTORY/El-Campello-in-situ/El-Campello-in-situ.pkl'
    with open(f, 'rb') as f:
        var = load(f)

    # Subset for the requested time period
    t0 = timezone('UTC').localize(datetime.strptime(start, '%Y-%m-%d'))
    t1 = timezone('UTC').localize(datetime.strptime(end,   '%Y-%m-%d'))
    if t0 > t1: 
        t0, t1 = t1, t0
        start, end = end, start
    t1 += timedelta(days=1)
    
    sub = subset(var, t0, t1)
    #quiverfig = quiver(sub)

    ''' Apparently, we need to transpose ADCP speed to get a proper visualization in the historical portal. '''
    # Convert speed to NumPy array to prepare matrix transposition
    DCP = sub['DCP speed']
    DCP = np.array(DCP)
    # Convert direction to NumPy array 
    DCPdir = sub['DCP dir']
    DCPdir = np.array(DCPdir)

    # Subset surface current speed and direction for wind rose histogram
    surface_r = DCP[:, 0]
    surface_D = DCPdir[:, 0]

    # Subset 15-meter depth current speed and direction for wind rose histogram
    seabed_r = DCP[:, 11]
    seabed_D = DCPdir[:, 11]

    # Transpose ADCP speed array (for proper visualization in the historical portal)
    DCP = DCP.T
    # Convert to list
    DCP = DCP.tolist()
    # Add to historical dictionary
    sub['DCP speed'] = DCP

    # Surface currents rose
    r, D = surface_r, surface_D
    idate_surf_rose, edate_surf_rose, surf_rose_fig = wind_rose(sub['time'], prepare_wind_rose(r, D), 'currents')
    surf_rose_fig = surf_rose_fig.replace("strength", "speed")

    # Seabed currents rose
    r, D = seabed_r, seabed_D
    idate_seab_rose, edate_seab_rose, seab_rose_fig = wind_rose(sub['time'], prepare_wind_rose(r, D), 'currents')
    seab_rose_fig = seab_rose_fig.replace("strength", "speed")

    # Wave wind rose
    r, D = sub['Wave Peak Period'], sub['Wave Peak Direction']
    idate_wave_rose, edate_wave_rose, wave_rose_fig = wind_rose(sub['time'], prepare_wind_rose(r, D), 'wave')
    wave_rose_fig = wave_rose_fig.replace("strength", "period")

    # Wind rose
    r, D = sub['Wind Speed'], sub['Wind Direction']
    idate_wind_rose, edate_wind_rose, wind_rose_fig = wind_rose(sub['time'], prepare_wind_rose(r, D), 'wind')
    wind_rose_fig = wind_rose_fig.replace("strength", "speed")

    ''' Output dictionary '''
    data = send_output(sub)        

    ''' Generate CSV files '''
    # Adapt HISTORY data to the shape expected by the CSV functions
    csvdata = csvformat(data, surface_r, surface_D, seabed_r, seabed_D, DCP, DCPS)
    # Make CSV's for water quality variables
    for i in ('temp', 'tur', 'O2'):
        to_csv.to_csv(csvdata, i, language, write_forecast=False)
    # Make CSV for Significant Wave Height
    to_csv.to_csv_swh(csvdata, language, write_forecast=False)
    # Make CSV for wave period and direction
    to_csv.to_csv_wave_rose(csvdata, language, write_forecast=False)
    # Make CSV for wind
    to_csv.to_csv_wind(csvdata, language, write_forecast=False)
    # Make CSV for surface and seabed currents
    to_csv.to_csv_currents_rose(csvdata, language)
    # Make CSV for ADCP 
    to_csv.to_csv_current_profile(csvdata, language)

    data['DCPS'] = DCPS
    data['idate_surf_rose']=idate_surf_rose.strftime('%Y-%b-%d')
    data['edate_surf_rose']=edate_surf_rose.strftime('%Y-%b-%d')
    data['idate_seab_rose']=idate_seab_rose.strftime('%Y-%b-%d')
    data['edate_seab_rose']=edate_seab_rose.strftime('%Y-%b-%d')
    data['surf_rose_fig']=surf_rose_fig
    data['seab_rose_fig']=seab_rose_fig
    data['idate_wave_rose']=idate_wave_rose.strftime('%Y-%b-%d')
    data['edate_wave_rose']=edate_wave_rose.strftime('%Y-%b-%d')
    data['idate_wind_rose']=idate_wind_rose.strftime('%Y-%b-%d')
    data['edate_wind_rose']=edate_wind_rose.strftime('%Y-%b-%d')
    data['wave_rose_fig']=wave_rose_fig
    data['wind_rose_fig']=wind_rose_fig

    return data 

def configuration():
    ''' Read secrets (configuration) file '''
    config = {}
    with open('config', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save as environment variable
            config[key] = val
    return config

def csvformat(data, surface_r, surface_D, seabed_r, seabed_D, DCP, DCPS):
    ''' The CSV generating functions are not prepared to handle
        the historical data, since different variable names have
        been used. This function adapts the historical dataset
        to the format expected by the CSV generating functions. '''

    new = dict(data)

    # Temperature
    new['temp'] = new.pop('Temperature')

    # Oxygen saturation
    new['O2'] = new.pop('Oxygen_Saturation')

    # Wind speed
    new['wind_speed_csv_export'] = new.pop('Wind_Speed')

    # Wind direction
    new['wind_direction_csv_export'] = new.pop('Wind_Direction')

    # Wave period
    new['wave_rose_period'] = new.pop('Wave_Peak_Period')

    # Wave direction
    new['wave_rose_direction'] = new.pop('Wave_Peak_Direction')

    # Wave time
    new['wave_rose_time'] = new['time'] 

    # Currents time
    new['DCP_rose_time_surface'] = new['time']

    # Surface currents
    new['DCP_rose_speed_surface']     = json.dumps(surface_r.tolist())
    new['DCP_rose_direction_surface'] = json.dumps(surface_D.tolist())

    # Seabed currents
    new['DCP_rose_speed_seabed']     = json.dumps(seabed_r.tolist())
    new['DCP_rose_direction_seabed'] = json.dumps(seabed_D.tolist())

    # ADCP time
    new['DCP_time'] = new['time']

    # ADCP speed
    new['DCP_speed'] = json.dumps(DCP) 

    # ADCP depths
    new['DCPS'] = DCPS

    return new

def subset(buoy, t0, t1):
    ''' Subset buoy data for the requested time period '''
    
    # List of available times in the buoy dataset
    time = np.array(buoy['time'])
    
    # Find appropriate time indexes
    i0, i1 = np.argmin(abs(time - t0)), np.argmin(abs(time - t1)) + 1
    
    sub = {'time': buoy['time'][i0 : i1]}
    for i in buoy.keys():        
        # Subset each parameter for the requested time period
        sub[i] = buoy[i][i0 : i1]
        
    return sub
