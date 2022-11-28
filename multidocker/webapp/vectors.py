from datetime import timedelta
import numpy as np

def get_displacements(U, V, t, var):
    
    # Set factor to convert to kilometers
    f = 1e-3 if 'Wind' in var else 1e-5
        
    t = np.array(t)
    # Get time step
    dt = np.unique(t[1::] - t[0:-1])
    # Make sure time step is constant (TODO)
    if dt.size > 1: raise ValueError('Time step is not constant!')
    # Get time step [s]
    try:
        dt = dt[0].total_seconds()
    except IndexError: 
        nodata = [float('nan') for i in t]
        return nodata, nodata
    
    dx, dy, Dx, Dy = 0, 0, [], []
    
    for u, v in zip(U, V):
        dx += u * dt; Dx.append(dx)
        dy += v * dt; Dy.append(dy)
    return f*np.array(Dx), f*np.array(Dy)

def vector_request(buoy, variable, date):
    ''' Subset time and u, v components of velocity for the selected date '''        
  
    if 'Surface' in variable:
        uvar, vvar = buoy['u0'], buoy['v0']
    elif 'Mid-water' in variable:
        uvar, vvar = buoy['umid'], buoy['vmid']
    elif 'Seabed' in variable:
        uvar, vvar = buoy['ubot'], buoy['vbot']
    elif 'Wind' in variable:
        uvar, vvar = buoy['uwind'], buoy['vwind']

    Y, M, D = date.year, date.month, date.day
    # Get times for the selected date
    time = buoy['time']    

    u, v, t = [], [], []
    for idx, i in enumerate(time):
        y, m, d = i.year, i.month, i.day
        if ( y == Y ) and ( m == M ) and ( d == D ):
            u.append(uvar[idx]); v.append(vvar[idx]); t.append(i)
            
    # Added this to include 145 elements, including the 00:00 of the next day
    find = np.where(np.array(time) == date + timedelta(days=1))[0]
    if find:
        idx = find[0]
        u.append(uvar[idx]); v.append(vvar[idx]); t.append(time[idx])

    if 'Surface' in variable:
        buoy['u0'], buoy['v0'] = u, v
    elif 'Mid-water' in variable:
        buoy['umid'], buoy['vmid'] = u, v
    elif 'Seabed' in variable:
        buoy['ubot'], buoy['vbot'] = u, v
    elif 'Wind' in variable:
        buoy['uwind'], buoy['vwind'] = u, v

    return buoy, u, v, t   
