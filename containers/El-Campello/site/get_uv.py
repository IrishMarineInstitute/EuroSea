import numpy as np

def get_uv(r, D, criteria):
    ''' Get u, v components from speed (r) and direction (D). Direction [deg] 
    starting at North (0), East (90), South (180), West (270). Criteria is 
    either "TO" (e.g. currents) or "FROM" (e.g. winds). '''
    
    if isinstance(r, list):
        r = np.array(r)
    if isinstance(D, list):
        D = np.array(D)
    
    if criteria == 'FROM':
        D += 180
        
    D[D >= 360] = D[D >= 360] - 360
        
    D = 90 - D 
    
    D = np.pi * D / 180
    
    u = r * np.cos(D)
    v = r * np.sin(D)
    
    return u, v
    