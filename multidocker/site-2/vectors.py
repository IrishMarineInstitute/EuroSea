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
    dt = dt[0].total_seconds()
    
    dx, dy, Dx, Dy = 0, 0, [], []
    
    for u, v in zip(U, V):
        dx += u * dt; Dx.append(dx)
        dy += v * dt; Dy.append(dy)
    return f*np.array(Dx), f*np.array(Dy)

def vector_request(buoy, variable):
    ''' Subset time and u, v components of velocity for the selected date '''        
  
    # Get times for the selected date
    t = buoy['time'][-145:]    
    # Subset u, v components of velocity for the selected date
    if 'Surface' in variable:
        u, v = buoy['u0'][-145:], buoy['v0'][-145:]
        buoy['u0'], buoy['v0'] = u, v
    elif 'Mid-water' in variable:
        u, v = buoy['umid'][-145:], buoy['vmid'][-145:]
        buoy['umid'], buoy['vmid'] = u, v
    elif 'Seabed' in variable:
        u, v = buoy['ubot'][-145:], buoy['vbot'][-145:]
        buoy['ubot'], buoy['vbot'] = u, v
    elif 'Wind' in variable:
        u, v = buoy['uwind'][-145:], buoy['vwind'][-145:]
        buoy['uwind'], buoy['vwind'] = u, v
    
    return buoy, u, v, t   
