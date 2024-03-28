from datetime import datetime, timedelta
import numpy as np
from json import loads
from glob import glob
import os

def csvname(param, start, end):
    ''' Create name of CSV file '''

    if not os.path.isdir('/data/CSV'):
        os.mkdir('/data/CSV')

    # Clean data directory if needed to prevent accumulation of too many .csv files
    lista = glob('/data/CSV/*.csv')
    if len(lista) > 100: # Too many .csv files. Clean directory. 
        for file in lista:
            os.remove(file)

    return '/data/CSV/csv-' + param + '-' + start.replace('-', '') + '-' + end.replace('-', '') + '.csv'

def to_csv_currents_rose(data, startstr, endstr, language, buoy):
    ''' Write Current Speed and Direction series to CSV file '''

    f = csvname('currents', startstr, endstr)
 
    # Set header
    if language == 'en':
        if buoy == 'Campello':
            header = 'Date\tSurface speed (cm/s)\tSurface direction (º)\t15-meter depth speed (cm/s)\t15-meter depth direction (º)\n'
        elif buoy == 'Deenish':
            header = 'Date\tSurface speed (cm/s)\tSurface direction (º)\tSeabed speed (cm/s)\tSeabed direction (º)\n'

    elif language == 'es':
        if buoy == 'Campello':
            header = 'Fecha\tVelocidad superficie (cm/s)\tDirección superficie (º)\tVelocidad a 15 metros de profundidad (cm/s)\tDirección a 15 metros de profundidad (º)\n'
        elif buoy == 'Deenish':
            header = 'Fecha\tVelocidad superficie (cm/s)\tDirección superficie (º)\tVelocidad fondo (cm/s)\tDirección fondo (º)\n'

    time = data.index

    surface_speed, surface_direction = data['s-surface'], data['d-surface']

    if buoy == 'Campello':
        seabed_speed,  seabed_direction =  data['s-15m'],  data['d-15m']
    elif buoy == 'Deenish':
        seabed_speed,  seabed_direction =  data['s-seabed'],  data['d-seabed']

    with open(f, 'w') as csvfile:

        csvfile.write(header)

        for t, a, b, c, d in zip(time, surface_speed, surface_direction, seabed_speed, seabed_direction):

            t, v1, v2, v3, v4     =  t, '%.1f' % float(a), '%.1f' % float(b), '%.1f' % float(c), '%.1f' % float(d)

            csvfile.write(t.strftime('%Y-%m-%d %H:%M') + '\t' + v1 + '\t' + v2 + '\t' + v3 + '\t' + v4 + '\n')

    return f  

def to_csv_wind(data, startstr, endstr, language, write_forecast=True):
    ''' Write wind speed and direction series to CSV file '''

    f = csvname('wind', startstr, endstr,)
 
    # Set header
    if language == 'en':
        observations = '*** Observed ***\n\n'
        forecast = '\n*** Forecast ***\n\n'
        header = 'Date\tWind direction (º)\tWind speed (km/h)\n'
    elif language == 'es':
        observations = '*** Mediciones ***\n\n'
        forecast = '\n*** Predicción ***\n\n'
        header = 'Fecha\tDirección del viento (º)\tVelocidad del viento (km/h)\n' 

    time, speed, direction = data.index, data['s-wind'], data['d-wind']
    #time, direction, speed = loads(time), loads(direction), loads(speed)

    if write_forecast:
        fc_time, fc_speed, fc_direction = data['fc_wind_rose_time'], data['fc_wind_rose_period'], data['fc_d_wind']
        fc_time, fc_direction, fc_speed = loads(fc_time), loads(fc_direction), loads(fc_speed)

    with open(f, 'w') as csvfile:

        csvfile.write(observations)

        csvfile.write(header)

        for t, D, T in zip(time, direction, speed):

            t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

            csvfile.write(t.strftime('%Y-%m-%d %H:%M') + '\t' + v1 + '\t' + v2 + '\n')

        if write_forecast:

            csvfile.write(forecast)

            csvfile.write(header)

            for t, D, T in zip(fc_time, fc_direction, fc_speed):

                t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

                csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

    return f

def to_csv_wave_rose(data, startstr, endstr, language, write_forecast=True):
    ''' Write Wave Period and Direction series to CSV file '''

    f = csvname('wave', startstr, endstr)
 
    # Set header
    if language == 'en':
        observations = '*** Observed ***\n\n'
        forecast = '\n*** Forecast ***\n\n'
        header = 'Date\tWave Peak Direction (º)\tWave Peak Period (s)\n'
    elif language == 'es':
        observations = '*** Mediciones ***\n\n'
        forecast = '\n*** Predicción ***\n\n'
        header = 'Fecha\tDirección Pico del Oleaje (º)\tPeriodo Pico del Oleaje (s)\n' 

    time, direction, period = data.index, data['d-wave'], data['s-wave']

    if write_forecast:
        fc_time, fc_direction, fc_period = data['fc_time'], data['fc_d_wave'], data['fc_s_wave']
        fc_time, fc_direction, fc_period = loads(fc_time), loads(fc_direction), loads(fc_period)

    with open(f, 'w') as csvfile:

        csvfile.write(observations)

        csvfile.write(header)

        for t, D, T in zip(time, direction, period):

            t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

            csvfile.write(t.strftime('%Y-%m-%d %H:%M') + '\t' + v1 + '\t' + v2 + '\n')

        if write_forecast:
            csvfile.write(forecast)

            csvfile.write(header)

            for t, D, T in zip(fc_time, fc_direction, fc_period):

                t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

                csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

    return f


def to_csv_swh(data, startstr, endstr, language, write_forecast=True):
    ''' Write Significant Wave Height series to CSV file '''

    f = csvname('swh', startstr, endstr)
 
    # Set header
    if language == 'en':
        observations = '*** Observed ***\n\n'
        forecast = '\n*** Forecast ***\n\n'
        header = 'Date\tSignificant Wave Height (m)\tWave Height Swell (m)\n'
    elif language == 'es':
        observations = '*** Mediciones ***\n\n'
        forecast = '\n*** Predicción ***\n\n'
        header = 'Fecha\tAltura de Ola Significante (m)\tAltura de Mar de Fondo (m)\n' 

    time, SWH, SW = data.index, data['wave-height'], data['swell-height']

    if write_forecast:
        fc_time, fc_SWH, fc_SW = data['fc_wav_time'], data['fc_wav'], data['fc_wav_sw2']
        fc_time, fc_SWH, fc_SW = loads(fc_time), loads(fc_SWH), loads(fc_SW)

    with open(f, 'w') as csvfile:

        csvfile.write(observations)

        csvfile.write(header)

        for t, swh, sw in zip(time, SWH, SW):

            t, v1, v2     =  t, '%.1f' % float(swh), '%.1f' % float(sw)

            csvfile.write(t.strftime('%Y-%m-%d %H:%M') + '\t' + v1 + '\t' + v2 + '\n')

        if write_forecast:
            csvfile.write(forecast)

            csvfile.write(header)

            for t, swh, sw in zip(fc_time, fc_SWH, fc_SW):

                t, v1, v2     =  t, '%.1f' % float(swh), '%.1f' % float(sw)

                csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

    return f

def to_csv(sub, startstr, endstr, variable, language='es', write_forecast=True):
    ''' Write data into CSV file for download '''
    
    f = csvname(variable, startstr, endstr)
    
    with open(f, 'w') as csvfile:    
    
        if language == 'es':
            csvfile.write('*** Mediciones ***\n\n')
        elif language == 'en':
            csvfile.write('*** Observed ***\n\n')

        if variable == 'temp':
            if language=='es':
                header = 'Fecha\tTemperatura del mar (ºC)\n'
            elif language=='en':
                header = 'Date\tSeawater temperature (ºC)\n'
            time1, varname1 = 'time', 'temp'
            if write_forecast:
                time2, varname2 = 'fc_sst_time', 'fc_sst'
            else:
                time2, varname2 = '', ''

        elif variable == 'salt':
            if language=='es':
                header = 'Fecha\tSalinidad\n'
            elif language=='en':
                header = 'Date\tSalinity\n'
            time1, varname1 = 'time', 'salt'
            time2, varname2 = '', ''

        elif variable == 'tur':
            if language=='es':
                header = 'Fecha\tTurbidez (FNU)\n'
            elif language=='en':
                header = 'Date\tTurbidity (FNU)\n'
            time1, varname1 = 'time', 'tur'
            time2, varname2 = '', ''

        elif variable == 'pH':
            if language=='es':
                header = 'Fecha\tpH\n'
            elif language=='en':
                header = 'Date\tpH\n'
            time1, varname1 = 'time', 'pH'
            time2, varname2 = '', ''

        elif variable == 'O2':
            if language=='es':
                header = 'Fecha\tSaturación de Oxígeno en Disolución (%)\n'
            elif language=='en':
                header = 'Date\tDissolved Oxygen Saturation (%)\n'
            time1, varname1 = 'time', 'O2'
            time2, varname2 = '', ''

        # Get variables
        time1 = sub.index
        var1  = sub[varname1]
        if varname2:
            time2 = sub[time2][1:-1].split(', ')
            var2  = sub[varname2][1:-1] #.split(', ')

        csvfile.write(header)
        for t, value in zip(time1, var1):
            t, value = t.strftime('%Y-%m-%d %H:%M'), '%.2f' % float(value)
            csvfile.write(t + '\t' + value + '\n')
        
        if varname2: # Forecast available    
            csvfile.write('\n\n')        
            if language == 'es':
                csvfile.write('*** Predicción ***\n\n')
            elif language == 'en':
                csvfile.write('*** Forecast ***\n\n')
            csvfile.write(header)             
            for t, value in zip(time2, var2):
                t, value = t[1:-1], '%.2f' % float(value)
                csvfile.write(t + '\t' + value + '\n')
        
    return f
