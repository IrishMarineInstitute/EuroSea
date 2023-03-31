from datetime import datetime
import numpy as np
from math import atan2, pi
from json import loads

def to_csv_current_profile(data, language):
    ''' Write current profile to CSV file '''

    f = '/data/csv-profile-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'

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

    f = '/data/csv-currents-rose-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
 
    # Set header
    if language == 'en':
        header = 'Date\tSurface Speed (cm/s)\tSurface Direction (º)\tSeabed Speed (cm/s)\tSeabed Direction (º)\n'
    elif language == 'es':
        header = 'Fecha\tVelocidad superficie (cm/s)\Dirección superficie (º)\tVelocidad fondo (cm/s)\tDirección fondo (º)\n'

    time = loads(data['DCP_rose_time_surface'])

    surface_speed, surface_direction = loads(data['DCP_rose_speed_surface']), loads(data['DCP_rose_direction_surface'])

    seabed_speed,  seabed_direction =  loads(data['DCP_rose_speed_seabed']),  loads(data['DCP_rose_direction_seabed'])


    with open(f, 'w') as csvfile:

        csvfile.write(header)

        for t, a, b, c, d in zip(time, surface_speed, surface_direction, seabed_speed, seabed_direction):

            t, v1, v2, v3, v4     =  t, '%.1f' % float(a), '%.1f' % float(b), '%.1f' % float(c), '%.1f' % float(d)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\t' + v3 + '\t' + v4 + '\n')

    return f  


def to_csv_wave_rose(data, language):
    ''' Write Wave Period and Direction series to CSV file '''

    f = '/data/csv-wave-rose-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
 
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

    fc_time, fc_direction, fc_period = data['fc_wave_rose_time'], data['fc_wave_rose_direction'], data['fc_wave_rose_period']

    # Recover actual (numerical) data from jsonized string objects.
    time, direction, period = loads(time), loads(direction), loads(period)

    fc_time, fc_direction, fc_period = loads(fc_time), loads(fc_direction), loads(fc_period)

    with open(f, 'w') as csvfile:

        csvfile.write(observations)

        csvfile.write(header)

        for t, D, T in zip(time, direction, period):

            t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

        csvfile.write(forecast)

        csvfile.write(header)

        for t, D, T in zip(fc_time, fc_direction, fc_period):

            t, v1, v2     =  t, '%.1f' % float(D), '%.1f' % float(T)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

    return f


def to_csv_swh(data, language):
    ''' Write Significant Wave Height series to CSV file '''

    f = '/data/csv-swh-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
 
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

    fc_time, fc_SWH, fc_SW = data['fc_wav_time'], data['fc_wav'], data['fc_wav_sw2']

    # Recover actual (numerical) data from jsonized string objects.
    time, SWH, SW = loads(time), loads(SWH), loads(SW)

    fc_time, fc_SWH, fc_SW = loads(fc_time), loads(fc_SWH), loads(fc_SW)

    with open(f, 'w') as csvfile:

        csvfile.write(observations)

        csvfile.write(header)

        for t, swh, sw in zip(time, SWH, SW):

            t, v1, v2     =  t, '%.1f' % float(swh), '%.1f' % float(sw)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

        csvfile.write(forecast)

        csvfile.write(header)

        for t, swh, sw in zip(fc_time, fc_SWH, fc_SW):

            t, v1, v2     =  t, '%.1f' % float(swh), '%.1f' % float(sw)

            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\n')

    return f

def to_csv_uv(data, form):
    ''' Write vectorial data into CSV file for download '''

    f = '/data/csv-uv-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    
    timestamps = data['timestamps'][1:-1].split(', ')
    time = [datetime.fromtimestamp(float(i)).strftime('%Y-%m-%d %H:%M') for i in timestamps]
  
    if 'uv-surf' in form:  
        u, v, x, y = data['u0'], data['v0'], data['Dx0'], data['Dy0']
    elif 'uv-mid' in form:
        u, v, x, y = data['umid'], data['vmid'], data['Dxmid'], data['Dymid']
    elif 'uv-seab' in form:
        u, v, x, y = data['ubot'], data['vbot'], data['Dxbot'], data['Dybot']

    u, v = u[1:-1].split(', '), v[1:-1].split(', ')
    x, y = x[1:-1].split(', '), y[1:-1].split(', ')

    u = [float(i) for i in u] ; v = [float(i) for i in v ];
    x = [float(i) for i in x] ; y = [float(i) for i in y ];

    with open(f, 'w') as csvfile:
        csvfile.write('Fecha\tVelocidad (cm/s)\tDirección (N90E)\tDistancia (km)\tDirección (N90E)\n')
        for t, uu, vv, xx, yy in zip(time, u, v, x, y):
            speed = ( uu**2 + vv**2 ) ** .5

            dist = ( xx**2 + yy**2 ) ** .5
            
            direction = 90 - atan2(vv, uu) * 180 / pi
            if direction < 0: direction += 360

            direc = 90 - atan2(yy, xx) * 180 / pi
            if direc < 0: direc += 360

            speed = '%.1f' % speed
            dist = '%.1f' % dist
            try:
                direction = '%03d' % round(direction)
            except ValueError:
                direction = 'nan'
            try:
                direc = '%03d' % round(direc)
            except ValueError:
                direc = 'nan'
            csvfile.write(t + '\t' + speed + '\t' + direction + '\t' + dist + '\t' + direc + '\n')
        
    return f
 

def to_csv_profile(sub):
    ''' Write profile data into CSV file for download '''
    
    # Set ouptut file name
    f = '/data/csv-profile-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
        
    time  = sub['fc_temp3d_time'][1:-1].split(', ')
    var1  = sub['fc_temp3d_0'][1:-1].split(', ')
    var2  = sub['fc_temp3d_1'][1:-1].split(', ')
    var3  = sub['fc_temp3d_2'][1:-1].split(', ')
    var4  = sub['fc_temp3d_3'][1:-1].split(', ')
    var5  = sub['fc_temp3d_4'][1:-1].split(', ')
    var6  = sub['fc_temp3d_5'][1:-1].split(', ')
    var7  = sub['fc_temp3d_6'][1:-1].split(', ')
    var8  = sub['fc_temp3d_7'][1:-1].split(', ')
    var9  = sub['fc_temp3d_8'][1:-1].split(', ')
    var10  = sub['fc_temp3d_9'][1:-1].split(', ')
    var11  = sub['fc_temp3d_10'][1:-1].split(', ')
    var12  = sub['fc_temp3d_11'][1:-1].split(', ')
    var13  = sub['fc_temp3d_12'][1:-1].split(', ')
    var14  = sub['fc_temp3d_13'][1:-1].split(', ')
    var15  = sub['fc_temp3d_14'][1:-1].split(', ')

    with open(f, 'w') as csvfile:
        csvfile.write('Fecha\t1 m\t3 m\t5 m\t8 m\t11 m\t13 m\t16 m\t19 m\t23 m\t26 m\t30 m\t34 m\t38 m\t42 m\t47 m\n')
        for t, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15 in zip(time, var1, var2, var3, var4, var5, var6, var7, var8, var9, var10, var11, var12, var13, var14, var15):
            t = t[1:-1]
            v1, v2, v3, v4, v5      = '%.2f' % float(v1), '%.2f' % float(v2), '%.2f' % float(v3), '%.2f' % float(v4), '%.2f' % float(v5)
            v6, v7, v8, v9, v10     = '%.2f' % float(v6), '%.2f' % float(v7), '%.2f' % float(v8), '%.2f' % float(v9), '%.2f' % float(v10)
            v11, v12, v13, v14, v15 = '%.2f' % float(v11), '%.2f' % float(v12), '%.2f' % float(v13), '%.2f' % float(v14), '%.2f' % float(v15)
            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\t' + v3 + '\t' + v4 + '\t' + v5 + '\t' + v6 + '\t' + v7 + '\t' + v8 + \
                              '\t' + v9 + '\t' + v10 + '\t' + v11 + '\t' + v12 + '\t' + v13 + '\t' + v14 + '\t' + v15 + '\n')
        
    return f

def to_csv(sub, variable):
    ''' Write data into CSV file for download '''
    
    # Set output file name    
    f = '/data/csv-' + variable + '-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    
    with open(f, 'w') as csvfile:    
    
        csvfile.write('*** Mediciones ***\n\n')
        if variable == 'temp':
            header = 'Fecha\tTemperatura del mar (ºC)\n'
            time1, varname1 = 'time', 'temp'
            time2, varname2 = 'fc_sst_time', 'fc_sst'
        elif variable == 'salt':
            header = 'Fecha\tSalinidad\n'
            time1, varname1 = 'time', 'salt'
            time2, varname2 = '', ''
        elif variable == 'tur':
            header = 'Fecha\tTurbidez (FNU)\n'
            time1, varname1 = 'time', 'pH'
            time2, varname2 = '', ''
        elif variable == 'O2':
            header = 'Fecha\tSaturación de Oxígeno en Disolución (%)\n'
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
            csvfile.write('*** Predicción ***\n\n')
            csvfile.write(header)             
            for t, value in zip(time2, var2):
                t, value = t[1:-1], '%.2f' % float(value)
                csvfile.write(t + '\t' + value + '\n')
        
    return f

def to_csv_from_request(sub, variable, start, end):
    ''' Write data into CSV file for download '''

    time = sub['time']

    ini, end = start.replace('-', ''), end.replace('-', '')
    
    # Set output file name    
    f = f'/data/csv-{variable}-{ini}-{end}.csv'
    
    with open(f, 'w') as csvfile:    
    
        if variable == 'temp':
            header, varname = 'Fecha\tTemperatura del mar (ºC)\n', 'Temperature'

        elif variable == 'salt':
            header, varname = 'Fecha\tSalinidad\n', 'Salinity'

        elif variable == 'tur':
            header, varname = 'Fecha\tTurbidez (FNU)\n', 'pH'

        elif variable == 'O2':
            header, varname = 'Fecha\tSaturación de Oxígeno en Disolución (%)\n', 'Oxygen Saturation'

        var  = sub[varname]

        csvfile.write(header)
        for t, value in zip(time, var):
            t, value = t.strftime('%Y-%m-%d %H:%M'), '%.2f' % float(value)
            csvfile.write(t + '\t' + value + '\n')
            
def to_csv_uv_from_request(sub, time, variable, start, end):
    ''' Write vectorial data into CSV file for download '''

    ini, end = start.replace('-', ''), end.replace('-', '')
    
    # Set output file name    
    f = f'/data/csv-uv-{variable}-{ini}-{end}.csv'
    
    if 'uv-surf' in f:  
        u, v, x, y = sub['u0'], sub['v0'], sub['surf-x'], sub['surf-y']
    elif 'uv-mid' in f:
        u, v, x, y = sub['umid'], sub['vmid'], sub['mid-x'], sub['mid-y']
    elif 'uv-seab' in f:
        u, v, x, y = sub['ubot'], sub['vbot'], sub['seab-x'], sub['seab-y']

    with open(f, 'w') as csvfile:
        csvfile.write('Fecha\tVelocidad (cm/s)\tDirección (N90E)\tDistancia (km)\tDirección (N90E)\n')
        for t, uu, vv, xx, yy in zip(time, u, v, x, y):
            speed = ( uu**2 + vv**2 ) ** .5

            dist = ( xx**2 + yy**2 ) ** .5
            
            direction = 90 - atan2(vv, uu) * 180 / pi
            if direction < 0: direction += 360

            direc = 90 - atan2(yy, xx) * 180 / pi
            if direc < 0: direc += 360

            speed = '%.1f' % speed
            dist = '%.1f' % dist
            try:
                direction = '%03d' % round(direction)
            except ValueError:
                direction = 'nan'
            try:
                direc = '%03d' % round(direc)
            except ValueError:
                direc = 'nan'
            csvfile.write(t.strftime('%Y-%m-%d %H:%M') + '\t' + speed + '\t' + direction + '\t' + dist + '\t' + direc + '\n')
  
def to_csv_profile_from_request(time, temp, start, end):
    ''' Write profile data into CSV file for download '''
    
    ini, end = start.replace('-', ''), end.replace('-', '')
    
    # Set ouptut file name
    f = f'/data/csv-profile-{ini}-{end}.csv'
    
    var1, var2, var3, var4, var5 = temp[:,0], temp[:,1], temp[:,2], temp[:,3], temp[:,4]
    var6, var7, var8, var9, var10 = temp[:,5], temp[:,6], temp[:,7], temp[:,8], temp[:,9]
    var11, var12, var13, var14, var15 = temp[:,10], temp[:,11], temp[:,12], temp[:,13], temp[:,14]
    
    with open(f, 'w') as csvfile:
        csvfile.write('Fecha\t1 m\t3 m\t5 m\t8 m\t11 m\t13 m\t16 m\t19 m\t23 m\t26 m\t30 m\t34 m\t38 m\t42 m\t47 m\n')
        for t, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15 in zip(time, var1, var2, var3, var4, var5, var6, var7, var8, var9, var10, var11, var12, var13, var14, var15):
            t = t.strftime('%Y-%m-%d %H:%M')
            v1, v2, v3, v4, v5      = '%.2f' % float(v1), '%.2f' % float(v2), '%.2f' % float(v3), '%.2f' % float(v4), '%.2f' % float(v5)
            v6, v7, v8, v9, v10     = '%.2f' % float(v6), '%.2f' % float(v7), '%.2f' % float(v8), '%.2f' % float(v9), '%.2f' % float(v10)
            v11, v12, v13, v14, v15 = '%.2f' % float(v11), '%.2f' % float(v12), '%.2f' % float(v13), '%.2f' % float(v14), '%.2f' % float(v15)
            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\t' + v3 + '\t' + v4 + '\t' + v5 + '\t' + v6 + '\t' + v7 + '\t' + v8 + \
                              '\t' + v9 + '\t' + v10 + '\t' + v11 + '\t' + v12 + '\t' + v13 + '\t' + v14 + '\t' + v15 + '\n')
        
