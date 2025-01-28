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

def windrose(sub, level='surface', vartype='currents'):
    ''' Create wind rose figure and associated time series '''
    series = dict(time=sub.index,
            speed=sub.get(f's-{level}'),
            direction=sub.get(f'd-{level}'))

    # Subset for the last 24 hours
    time, r, D = sub.index, sub.get(f's-{level}'), sub.get(f'd-{level}')
    # Create figure
    idate, edate, wind_rose_fig = wind_rose(time, prepare_wind_rose(r, D), vartype)
    # Fix legend
    if 'wave' in level:
        wind_rose_fig = wind_rose_fig.replace("strength", "period")
    else:
        wind_rose_fig = wind_rose_fig.replace("strength", "speed")
    # Wrap 
    fig = {'idate': idate, 'edate': edate, 'fig': wind_rose_fig}

    return series, fig

def address_request(start, end, uv, boya, language='en'):
    ''' Subset in-situ data for the requested dates '''

    # Load historical buoy data
    if boya == 'Campello':
        f = '/data/his/El-Campello/El-Campello.pkl'
    elif boya == 'Deenish':
        f = '/data/his/Deenish-Island/Deenish-Island.pkl'
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

    # Surface currents
    surface_series, surface_fig = windrose(sub)
    # Seabed currents
    if boya == 'Campello':
        seabed_series, seabed_fig = windrose(sub, level='15m')
        # Winds 
        wind_series, wind_fig = windrose(sub, level='wind', vartype='wind')
        # Wave period
        wave_series, wave_fig = windrose(sub, level='wave', vartype='wave')
    elif boya == 'Deenish':
        seabed_series, seabed_fig = windrose(sub, level='seabed')

    ''' Output dictionary '''
    data = send_output(sub, boya)        

    ''' Generate CSV files '''
    # Adapt HISTORY data to the shape expected by the CSV functions
    csvdata = sub ; #csvdata = csvformat(data, boya)
    # Make CSV's 
    if boya == 'Campello':
        buoyvars = ('temp', 'tur', 'O2')
    elif boya == 'Deenish':
        buoyvars = ('temp', 'salt', 'pH', 'O2', 'RFU', 'BGA')

    for i in buoyvars:
        to_csv.to_csv(csvdata, start, end, i, language, write_forecast=False)

    if boya == 'Campello':
        # Make CSV for Significant Wave Height
        to_csv.to_csv_swh(csvdata, start, end, language, write_forecast=False)
        # Make CSV for wave period and direction
        to_csv.to_csv_wave_rose(csvdata, start, end, language, write_forecast=False)
        # Make CSV for wind
        to_csv.to_csv_wind(csvdata, start, end, language, write_forecast=False)
    # Make CSV for surface and seabed currents
    to_csv.to_csv_currents_rose(csvdata, start, end, language, boya)

    # Add surface currents figure
    data['surf_rose_fig']=surface_fig.get('fig')
    data['idate_surf_rose']=surface_fig.get('idate').strftime('%Y-%b-%d')
    data['edate_surf_rose']=surface_fig.get('edate').strftime('%Y-%b-%d')

    # Add seabed currents figure
    data['seab_rose_fig']=seabed_fig.get('fig')
    data['idate_seab_rose']=seabed_fig.get('idate').strftime('%Y-%b-%d')
    data['edate_seab_rose']=seabed_fig.get('edate').strftime('%Y-%b-%d')

    if boya == 'Campello':
        # Add wave figure
        data['wave_rose_fig']=wave_fig.get('fig')
        data['idate_wave_rose']=wave_fig.get('idate').strftime('%Y-%b-%d')
        data['edate_wave_rose']=wave_fig.get('edate').strftime('%Y-%b-%d')

        # Add wind figure
        data['wind_rose_fig']=wind_fig.get('fig')
        data['idate_wind_rose']=wind_fig.get('idate').strftime('%Y-%b-%d')
        data['edate_wind_rose']=wind_fig.get('edate').strftime('%Y-%b-%d')

    return data 

def csvformat(data, boya):
    ''' The CSV generating functions are not prepared to handle
        the historical data, since different variable names have
        been used. This function adapts the historical dataset
        to the format expected by the CSV generating functions. '''

    new = dict(data)

    # Wind speed
    new['wind_rose_speed'] = new.pop('s_wind')

    # Wind direction
    new['wind_rose_direction'] = new.pop('d_wind')

    # Wave period
    new['wave_rose_period'] = new.pop('s_wave')

    # Wave direction
    new['wave_rose_direction'] = new.pop('d_wave')

    # Wave time
    new['wave_rose_time'] = new['time'] 

    # Currents time
    new['DCP_rose_time_surface'] = new['time']

    # Surface currents
    new['DCP_rose_speed_surface']     = new.pop('s_surface') 
    new['DCP_rose_direction_surface'] = new.pop('d_surface') 

    # Seabed currents
    if boya == 'Campello':
        new['DCP_rose_speed_seabed']     = new.pop('s_15m') 
        new['DCP_rose_direction_seabed'] = new.pop('d_15m') 
    elif boya == 'Deenish':
        new['DCP_rose_speed_seabed']     = new.pop('s_seabed') 
        new['DCP_rose_direction_seabed'] = new.pop('d_seabed') 

    # ADCP time
    new['DCP_time'] = new['time']

    return new

def subset(buoy, t0, t1):
    ''' Subset buoy data for the requested time period '''
    
    # List of available times in the buoy dataset
    time = buoy.index
    
    # Find appropriate time indexes
    i0, i1 = np.argmin(abs(time - t0)), np.argmin(abs(time - t1)) + 1
    
    sub = buoy[i0 : i1]
        
    return sub
