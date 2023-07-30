from datetime import datetime, timedelta
import numpy as np
from json import loads
from glob import glob
import os

def csvname(data, timevar, param):
    ''' Create name of CSV file '''

    if not os.path.isdir('/data/CSV'):
        os.mkdir('/data/CSV')

    # Clean data directory if needed to prevent accumulation of too many .csv files
    lista = glob('/data/CSV/*.csv')
    if len(lista) > 100: # Too many .csv files. Clean directory. 
        for file in lista:
            os.remove(file)

    # Get time from data
    time = loads(data[timevar])
    
    # Get start and end dates
    idate, edate = time[0], time[-1]

    inp, out = '%Y-%m-%d %H:%M', '%Y%m%d'
    # Convert strings to datetimes
    idate, edate = datetime.strptime(idate, inp), datetime.strptime(edate, inp) - timedelta(hours=1) 
    # Convert back to strings, but without blank spaces
    idate, edate = idate.strftime(out), edate.strftime(out)

    return '/data/CSV/csv-' + param + '-' + idate + '-' + edate + '.csv'

def to_csv_current_profile(data, language):
    ''' Write current profile to CSV file '''

    f = csvname(data, 'DCP_time', 'ADCP')

    # Get DCPS depths [m]
    z = loads(data['DCPS'])

    # Set header
    if language == 'en':
        header = 'Date\t'
    elif language == 'es':
        header = 'Fecha\t'

    for i in z:
        header += f'{i} m\t'

    header += '(cm/s)\n'

    time, V = loads(data['DCP_time']), np.array(loads(data['DCP_speed'])).T

    with open(f, 'w') as csvfile:

        csvfile.write(header)

        for t, v in zip(time, V):

            line = t + '\t'

            for k in v:

                line += '%.1f' %  float(k) + '\t'


            line += '\n'

            csvfile.write(line)

    return f  

def to_csv_currents_rose(data, language):
    ''' Write Current Speed and Direction series to CSV file '''

    f = csvname(data, 'DCP_rose_time_surface', 'currents')
 
    # Set header
    if language == 'en':
        header = 'Date\tSurface speed (cm/s)\tSurface direction (º)\t15-meter depth speed (cm/s)\t15-meter depth direction (º)\n'
    elif language == 'es':
        header = 'Fecha\tVelocidad superficie (cm/s)\tDirección superficie (º)\tVelocidad a 15 metros de profundidad (cm/s)\tDirección a 15 metros de profundidad (º)\n'

    time = loads(data['DCP_rose_time_surface'])

    surface_speed, surface_direction = loads(data['DCP_rose_speed_surface']), loads(data['DCP_rose_direction_surface'])

    seabed_speed,  seabed_direction =  loads(data['DCP_rose_speed_seabed']),  loads(data['DCP_rose_direction_seabed'])


    with open(f, 'w') as csvfile:

        csvfile.write(header)

        for t, a, b, c, d in zip(time, surface_speed, surface_direction, seabed_speed, seabed_direction):

            t, v1, v2, v3, v4     =  t, '%.1f' % float(a), '%.1f' % float(b), '%.1f' % float(c), '%.1f' % float(d)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\t' + v3 + '\t' + v4 + '\n')

    return f  

def to_csv_wind(data, language, write_forecast=True):
    ''' Write wind speed and direction series to CSV file '''

    f = csvname(data, 'time', 'wind')
 
    # Set header
    if language == 'en':
        observations = '*** Observed ***\n\n'
        forecast = '\n*** Forecast ***\n\n'
        header = 'Date\tWind direction (º)\tWind speed (km/h)\n'
    elif language == 'es':
        observations = '*** Mediciones ***\n\n'
        forecast = '\n*** Predicción ***\n\n'
        header = 'Fecha\tDirección del viento (º)\tVelocidad del viento (km/h)\n' 

    time, speed, direction = data['time'], data['wind_speed_csv_export'], data['wind_direction_csv_export']
    time, direction, speed = loads(time), loads(direction), loads(speed)

    if write_forecast:
        fc_time, fc_speed, fc_direction = data['fc_wind_rose_time'], data['fc_wind_rose_period'], data['fc_wind_rose_direction']
        fc_time, fc_direction, fc_speed = loads(fc_time), loads(fc_direction), loads(fc_speed)

    with open(f, 'w') as csvfile:

        csvfile.write(observations)

        csvfile.write(header)

        for t, D, T in zip(time, direction, speed):

            t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

        if write_forecast:

            csvfile.write(forecast)

            csvfile.write(header)

            for t, D, T in zip(fc_time, fc_direction, fc_speed):

                t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

                csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

    return f

def to_csv_wave_rose(data, language, write_forecast=True):
    ''' Write Wave Period and Direction series to CSV file '''

    f = csvname(data, 'wave_rose_time', 'wave')
 
    # Set header
    if language == 'en':
        observations = '*** Observed ***\n\n'
        forecast = '\n*** Forecast ***\n\n'
        header = 'Date\tWave Peak Direction (º)\tWave Peak Period (s)\n'
    elif language == 'es':
        observations = '*** Mediciones ***\n\n'
        forecast = '\n*** Predicción ***\n\n'
        header = 'Fecha\tDirección Pico del Oleaje (º)\tPeriodo Pico del Oleaje (s)\n' 

    time, direction, period = data['wave_rose_time'], data['wave_rose_direction'], data['wave_rose_period']
    time, direction, period = loads(time), loads(direction), loads(period)

    if write_forecast:
        fc_time, fc_direction, fc_period = data['fc_wave_rose_time'], data['fc_wave_rose_direction'], data['fc_wave_rose_period']
        fc_time, fc_direction, fc_period = loads(fc_time), loads(fc_direction), loads(fc_period)

    with open(f, 'w') as csvfile:

        csvfile.write(observations)

        csvfile.write(header)

        for t, D, T in zip(time, direction, period):

            t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

        if write_forecast:
            csvfile.write(forecast)

            csvfile.write(header)

            for t, D, T in zip(fc_time, fc_direction, fc_period):

                t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

                csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

    return f


def to_csv_swh(data, language, write_forecast=True):
    ''' Write Significant Wave Height series to CSV file '''

    f = csvname(data, 'time', 'swh')
 
    # Set header
    if language == 'en':
        observations = '*** Observed ***\n\n'
        forecast = '\n*** Forecast ***\n\n'
        header = 'Date\tSignificant Wave Height (m)\tWave Height Swell (m)\n'
    elif language == 'es':
        observations = '*** Mediciones ***\n\n'
        forecast = '\n*** Predicción ***\n\n'
        header = 'Fecha\tAltura de Ola Significante (m)\tAltura de Mar de Fondo (m)\n' 

    time, SWH, SW = data['time'], data['Significant_Wave_Height_Hm0'], data['Wave_Height_Swell_Hm0']
    time, SWH, SW = loads(time), loads(SWH), loads(SW)

    if write_forecast:
        fc_time, fc_SWH, fc_SW = data['fc_wav_time'], data['fc_wav'], data['fc_wav_sw2']
        fc_time, fc_SWH, fc_SW = loads(fc_time), loads(fc_SWH), loads(fc_SW)

    with open(f, 'w') as csvfile:

        csvfile.write(observations)

        csvfile.write(header)

        for t, swh, sw in zip(time, SWH, SW):

            t, v1, v2     =  t, '%.1f' % float(swh), '%.1f' % float(sw)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

        if write_forecast:
            csvfile.write(forecast)

            csvfile.write(header)

            for t, swh, sw in zip(fc_time, fc_SWH, fc_SW):

                t, v1, v2     =  t, '%.1f' % float(swh), '%.1f' % float(sw)

                csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

    return f

def to_csv(sub, variable, language='es', write_forecast=True):
    ''' Write data into CSV file for download '''
    
    f = csvname(sub, 'time', variable)
    
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
        elif variable == 'tur':
            if language=='es':
                header = 'Fecha\tTurbidez (FNU)\n'
            elif language=='en':
                header = 'Date\tTurbidity (FNU)\n'
            time1, varname1 = 'time', 'TUR'
            time2, varname2 = '', ''
        elif variable == 'O2':
            if language=='es':
                header = 'Fecha\tSaturación de Oxígeno en Disolución (%)\n'
            elif language=='en':
                header = 'Date\tDissolved Oxygen Saturation (%)\n'
            time1, varname1 = 'time', 'O2'
            time2, varname2 = '', ''

        # Get variables
        time1 = sub[time1][1:-1].split(', ')
        var1  = sub[varname1][1:-1].split(', ')
        if varname2:
            time2 = sub[time2][1:-1].split(', ')
            var2  = sub[varname2][1:-1].split(', ')

        csvfile.write(header)
        for t, value in zip(time1, var1):
            t, value = t[1:-1], '%.2f' % float(value)
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
