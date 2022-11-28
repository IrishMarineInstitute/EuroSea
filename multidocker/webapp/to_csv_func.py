from datetime import datetime
from math import atan2, pi

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
        csvfile.write('Date\tSpeed (cm/s)\tDirection (N90E)\tDistance (km)\tDirection (N90E)\n')
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
        
    time1 = sub['fc_temp3d_time'][1:-1].split(', ')
    var1  = sub['fc_temp3d_0'][1:-1].split(', ')
    var2  = sub['fc_temp3d_4'][1:-1].split(', ')
    var3  = sub['fc_temp3d_7'][1:-1].split(', ')

    with open(f, 'w') as csvfile:
        csvfile.write('Date\tsurface\t15 m\t30 m\n')
        for t, v1, v2, v3 in zip(time1, var1, var2, var3):
            t, v1, v2, v3 = t[1:-1], '%.2f' % float(v1), '%.2f' % float(v2), '%.2f' % float(v3)
            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\t' + v3 + '\n')
        
    return f

def to_csv(sub, variable):
    ''' Write data into CSV file for download '''
    
    # Set output file name    
    f = '/data/csv-' + variable + '-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    
    with open(f, 'w') as csvfile:    
    
        csvfile.write('*** Measurements ***\n\n')
        if variable == 'temp':
            header = 'Date\tSeawater temperature (ºC)\n'
            time1, varname1 = 'time', 'temp'
            time2, varname2 = 'fc_sst_time', 'fc_sst'
        elif variable == 'salt':
            header = 'Date\tSeawater salinity\n'
            time1, varname1 = 'time', 'salt'
            time2, varname2 = 'fc_sss_time', 'fc_sss'
        elif variable == 'pH':
            header = 'Date\tSeawater pH\n'
            time1, varname1 = 'time', 'pH'
            time2, varname2 = '', ''
        elif variable == 'O2':
            header = 'Date\tDissolved Oxygen Saturation (%)\n'
            time1, varname1 = 'time', 'O2'
            time2, varname2 = '', ''
        elif variable == 'RFU':
            header = 'Date\tRaw Fluorescence Units\n'
            time1, varname1 = 'time', 'RFU'
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
            csvfile.write('*** Forecast ***\n\n')
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
            header, varname = 'Date\tSeawater temperature (ºC)\n', 'Temperature'

        elif variable == 'salt':
            header, varname = 'Date\tSeawater salinity\n', 'Salinity'

        elif variable == 'pH':
            header, varname = 'Date\tSeawater pH\n', 'pH'

        elif variable == 'O2':
            header, varname = 'Date\tDissolved Oxygen Saturation (%)\n', 'Oxygen Saturation'

        elif variable == 'RFU':
            header, varname = 'Date\tRaw Fluorescence Units\n', 'RFU'

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
        csvfile.write('Date\tSpeed (cm/s)\tDirection (N90E)\tDistance (km)\tDirection (N90E)\n')
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
    
    var1, var2, var3 = temp[:, 0], temp[:, 4], temp[:, 7] # surface, 15 m, 30 m
    
    with open(f, 'w') as csvfile:
        csvfile.write('Date\tsurface\t15 m\t30 m\n')
        for t, v1, v2, v3 in zip(time, var1, var2, var3):
            t, v1, v2, v3 = t.strftime('%Y-%m-%d %H:%M'), '%.2f' % float(v1), '%.2f' % float(v2), '%.2f' % float(v3)
            csvfile.write(t + '\t' + v1 + '\t' + v2 + '\t' + v3 + '\n')
