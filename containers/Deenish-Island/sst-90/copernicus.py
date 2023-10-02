from motu import motu
import os

def Copernicus_Marine_Service(USER, PSWD, PRODUCT, SERVICE, 
    localpath, filename, lonmin, lonmax, latmin, latmax, idate, edate, var, mode):
    
    '''
            This function downloads, as a NetCDF file, the variable from the
            specified product and service. It uses motu-client
    '''

    for i in range(5): # Try up to 5 times to download from Copernicus Marine Service
    
        # Submit request to the motu client
        f = motu(USER, PSWD, SERVICE, PRODUCT, localpath, filename, 
             lonmin, lonmax, latmin, latmax, idate, edate, var, mode)
        
        if os.path.isfile(f): # File downloaded successfully. Leave loop...
            break
        else: # Download failed. Retry...
            continue
