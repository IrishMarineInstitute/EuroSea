from opendrift.models.oceandrift import OceanDrift 
from opendrift.readers import reader_ROMS_native
# from opendrift.readers import reader_netCDF_CF_generic  
from opendrift.readers import reader_global_landmask
from datetime import date, datetime, timedelta
from netCDF4 import Dataset, num2date
from shapely.geos import TopologicalError
import numpy as np
import matplotlib.pyplot as plt
from Plot import osm_image
import imageio
import os

# Set boundaries (W, E, S, N)
xmin, xmax, ymin, ymax = -10.8, -9.4, 51.39, 51.81

# Set horizontal resolution grid for particle count
dh = .001

def LPTM():
    
    if not os.path.isdir('LPTM'):
        os.mkdir('LPTM')
        
    # Define landmask extension    
    landmask = reader_global_landmask.Reader(
        extent=[-11, 51,  # min. longitude, min. latitude, 
                 -9, 52]) # max. longitude, max. latitude
        
    # Output NetCDF file name     
    filename = 'LPTM/Deenish-LPTM-' + date.today().strftime('%Y%m%d') + '.nc'
        
    # Seeding transect. Numerical drifters are seeded along a line    
    # Longitude end points of transect 
    x0, x1 = -10.54, -10.24
    # Latitude end points of transect
    y0, y1 =  51.58,  51.58
    
    # Number of floats        
    N = 1000
    
    # Release drifters for today, from 00:00 to 00:00 (+1) 
    hoy = date.today(); Y, M, D = hoy.year, hoy.month, hoy.day
    idate = datetime(Y, M, D); edate = idate + timedelta(days=1)
    	
    # Time step        
    step = timedelta(minutes=3)
    
    # Output frequency    
    NHIS = 10
    
    # Input ocean file(s)           
    his1 = r'\\MIFS01\nas_data\ROMS\OUTPUT\Bantry_Bay\FC\WEEK_ARCHIVE\BANT_*.nc'
    his2 = 'http://milas.marine.ie/thredds/dodsC/IMI_ROMS_HYDRO/NEATLANTIC_NATIVE_2KM_40L_1H/AGGREGATE'
           
    o = OceanDrift(loglevel=20)    
    # Initialize ocean reader 
    phys1 = reader_ROMS_native.Reader(his1)
    phys2 = reader_ROMS_native.Reader(his2)
    # Add readers 
    o.add_reader([landmask, phys1, phys2])
    # Allow a stranded drifter to go back to the water 
    o.set_config('general:coastline_action', 'previous')
    # Add diffusion
    o.set_config('drift:horizontal_diffusivity', .01)
    # Limit drifter age to 3 days 
    o.set_config('drift:max_age_seconds', 3*86400)
        
    # Seed elements 
    while idate < edate:
        o.seed_cone(lon=[x0, x1], lat=[y0, y1], # Seed along transect
                    number=N,                   # Number of elements
                    radius=[0, 0],              # Radius for dispersion around transect
                    time=idate)                 # Initial and end date for particle release 
        idate += timedelta(seconds=60)
    
    # Run 
    o.run(end_time=phys1.end_time,                 # Run until the latest available oceanic forecast
          time_step=step,                          # Time step
          time_step_output=NHIS*step,              # Output frequency
          outfile=filename,                        # Output NetCDF file name
          export_variables=['lon', 'lat', 'time'], # Output variables
          export_buffer_length=10)                 # Synchronize output file every 10 records

                                                   
    density(filename) 
    
    
def density(f):    
    ''' Get density of particles '''
    
    # Create grid for particle count
    x_grid, y_grid = np.arange(xmin, xmax, dh), np.arange(ymin, ymax, dh)
    
    with Dataset(f, 'r') as nc:    
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        # Get number of floats
        N = len(nc.variables['trajectory'])
                
        images_data = []
        
        print('\nPrinting LPTM figures...') 
        for i, t in enumerate(time):  
            print('\t' + t.strftime('%d-%b-%Y %H:%M'))
            # Output initialization
            D = np.zeros((len(y_grid), len(x_grid)))            
            # Read longitude and latitude for i-th time step
            while 1:
                try:
                    lon_t, lat_t = nc.variables['lon'][:, i], nc.variables['lat'][:, i]; break
                except RuntimeError:
                    continue
            for x, y in zip(lon_t, lat_t):
                if np.ma.is_masked(x): continue
                index_x = np.argmax(x < x_grid) - 1
                index_y = np.argmax(y < y_grid) - 1
                D[index_y, index_x] += 1             
            # Mask where there are no floats to keep it transparent and 
            # show the underlying background satellite image beneath
            D = np.ma.masked_where(D == 0, D)
            try:
                fig, ax = osm_image(x_grid, y_grid, data=D/N, 
                    vmin=0, vmax=1e-3, cmap='YlOrRd', cbar=False)           
            except TopologicalError:
                continue
            # Add date and time as title
            ax.set_title(t.strftime('%d-%b-%Y %H:%M'))
            # Set image name
            imname = 'LPTM/LPTM-' + t.strftime('%Y%m%d%H%M') + '.png'
            # Save and close figure              
            plt.savefig(imname, dpi=300, bbox_inches='tight'); plt.close(fig)  
            # Append image to GIF
            images_data.append(imageio.imread(imname))
            
    # Set GIF file name
    imageio.mimwrite(filename.replace('nc', 'gif'), images_data, format= '.gif', fps = 4)

# def animate(f):
#     ''' Produce an animation from OpenDrift output '''
    
#     with Dataset(f, 'r') as nc:
#         time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        
#         print('\nPrinting LPTM figures...')        
#         for i, t in enumerate(time):
#             print('\t' + t.strftime('%d-%b-%Y %H:%M'))
#             # Read longitude and latitude for i-th time step
#             x, y = nc.variables['lon'][:, i], nc.variables['lat'][:, i]
#             # Create map
#             fig, ax = osm_image(np.array([-10.8, -9.5]), np.array([51.40, 51.85]))
#             # Draw drifter's positions
#             ax.scatter(x, y, s=6, c='r', transform=ccrs.PlateCarree())
#             # Add title
#             ax.set_title(t.strftime('%d-%b-%Y %H:%M'))
#             # Save image
#             plt.savefig('LPTM/LPTM-' + t.strftime('%Y%m%d%H%M') + '.png', 
#                         dpi=300, bbox_inches='tight')