import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import matplotlib
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from cmocean.cm import thermal
from datetime import datetime
from geopy.distance import distance
from PIL import Image
from urllib.request import urlopen, Request
import io
import pytz

font = {'size' : 18}; matplotlib.rc('font', **font)

units = {'temp': '$^\circ$C', 'salt': '', 'pH': '', 'chl': '', 'DOX': '%'}  
names = {'temp': 'Temperature', 
         'salt': 'Salinity',
         'pH': 'pH',
         'chl': 'Reference Fluorescence Units',
         'DOX': 'Oxygen saturation'}

def image_spoof(DBO, tile):
    ''' This function reformats web requests from OSM for cartopy
    Heavily based on code by Joshua Hrisko at:
    https://makersportal.com/blog/2020/4/24/geographic-visualizations-in-python-with-cartopy'''

    url = DBO._image_url(tile)                # get the url of the street map API
    req = Request(url)                         # start request
    req.add_header('User-agent','Anaconda 3')  # add user agent to request
    fh = urlopen(req) 
    im_data = io.BytesIO(fh.read())            # get image
    fh.close()                                 # close url
    img = Image.open(im_data)                  # open image with PIL
    img = img.convert(DBO.desired_tile_form)  # set image format
    return img, DBO.tileextent(tile), 'lower' # reformat for cartopy  

def osm_image(x, y, data=None, vmin=None, vmax=None, 
        cmap=None, units=None, title=None, style='map'):
    '''This function makes OpenStreetMap satellite or map image with circle and random points.
    Change np.random.seed() number to produce different (reproducable) random patterns of points.
    Also review 'scale' variable'''
  
    if style=='map': # MAP STYLE
        cimgt.OSM.get_image = image_spoof # reformat web request for street map spoofing
        img = cimgt.OSM() # spoofed, downloaded street map
    elif style =='satellite': # SATELLITE STYLE
        cimgt.QuadtreeTiles.get_image = image_spoof # reformat web request for street map spoofing
        img = cimgt.QuadtreeTiles() # spoofed, downloaded street map
    else:
        print('no valid style')

    x0, y0 = x.mean(), y.mean()
    cx = (x.min(), x.min(), x.max(), x.max())
    cy = (y.min(), y.max(), y.max(), y.min())
    radius = sum([distance((y0, x0), (y,x)).m for x, y in zip(cx, cy)])/4

    plt.close('all')
    fig = plt.figure(figsize=(10,10)) # open matplotlib figure
    ax = plt.axes(projection=img.crs, zorder=0) # project using coordinate reference system (CRS) of street map
    data_crs = ccrs.PlateCarree()
    
   
    scale = int(120/np.log(radius))
    scale = (scale<20) and scale or 19

    ax.set_title(title)
    ax.add_image(img, int(scale)) # add OSM with zoom specification
    
    gl = ax.gridlines(draw_labels=True, crs=data_crs,
                        color='k', lw=0.5)
    
    if data is not None:
        # data = np.ma.masked_where(data==0, data)
        ax.contourf(x, y, data, levels=20, vmin=vmin, vmax=vmax,
            cmap=cmap, transform=ccrs.PlateCarree(), zorder=1)        
        #ax.pcolor(x, y, data, vmin=vmin, vmax=vmax,
        #    cmap=cmap, transform=ccrs.PlateCarree(), zorder=1)        
        m = plt.cm.ScalarMappable(cmap=cmap)
    
        m.set_clim(vmin, vmax)
        P = ax.get_position(); P = [P.x1 + .02, P.y0,  .03, P.height] 
        fig.colorbar(m, cax=fig.add_axes(P), label=units)
        
        # fig.colorbar(m, ax=ax, label=units, fraction=0.046, pad=0.04)
        
    
    extent = [x.min(), x.max(), y.min(), y.max()]    
    ax.set_extent(extent) # set extents
   
    gl.top_labels = False
    gl.right_labels = False
    gl.xlocator = mticker.FixedLocator([-11, -10, -9])
    gl.ylocator = mticker.FixedLocator([50, 51, 52])

    return fig, ax

def plot2d(filename, x, y, data, vmin, vmax, 
                  cmap, units='', title=''):
      
    fig, ax = osm_image(x, y, data=data, 
        vmin=vmin, vmax=vmax, cmap=cmap, units=units, title=title)
    plt.savefig('IMAGES/' + filename, dpi=500, bbox_inches='tight')
    plt.close(fig) 
    
def Plot_SST(DBO):
    title = 'MUR-SST ' + datetime(DBO.sst_time[-1].year, 
        DBO.sst_time[-1].month, DBO.sst_time[-1].day).strftime('%d-%b-%Y')   
    avg = DBO.sst[-1, :, :].mean(); v_min, v_max = round(avg - 2), round(avg + 2)    
    plot2d('SST.png', DBO.sst_x, DBO.sst_y, DBO.sst[-1, :, :], v_min, v_max, 
            thermal, units='ºC', title=title)
    
def Plot_anom(DBO):
    title = 'MUR-SST Anomaly ' + datetime(DBO.sst_time[-1].year, 
        DBO.sst_time[-1].month, DBO.sst_time[-1].day).strftime('%d-%b-%Y') 
    # Find latest time
    latest = DBO.sst_time[-1].timetuple().tm_yday
    idx = np.where(DBO.clim_time == latest)[0][0]
    
    SST = DBO.sst[-1, :, :]
    seas = DBO.seas[idx, :, :]
    ANOM = SST - seas
    plot2d('ANOM.png', DBO.sst_x, DBO.sst_y, ANOM, -2, 2, 
            'bwr', units='ºC', title=title)
    
def Plot_Selection(DBO, lon, lat):
    fig, ax = plt.subplots(1)
    
    i, j = np.argmin(DBO.sst_x - lon), np.argmin(DBO.sst_y - lat)
    
    # Get SST series at selected location
    sst = DBO.sst[:, j, i]
    
    l1, = ax.plot(DBO.sst_time, sst, label='MUR-SST')
    
    # Set title
    plt.title(f'SST at {lat}$^\circ$N {abs(lon)}$^\circ$W', fontsize=12)
    
    # Set y-axis label (units)
    plt.ylabel('$^\circ$C', fontsize=12)
    
    # Set x-axis limits
    ax.set_xlim([min(DBO.sst_time), max(DBO.time)])
          
    # Show grid
    plt.grid()
    
    nwshelf = DBO.temp2d_interp[:, j, i]
    
    l2, = ax.plot(DBO.time2d, nwshelf, color='C1', label='NWSHELF')
       
    
    l3, = ax.plot(DBO.u_time, DBO.u_seas, color='C2', label='Climatology')
    l4, = ax.plot(DBO.u_time, DBO.u_pc90, color='C3', label='90-th pctl')

    # Add legend
    plt.legend(handles=[l1, l2, l3, l4], fontsize=8)
    
    # Set date ticks format
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%d-%b"))
    
    ax.tick_params(axis='both', labelsize=8)
    # Rotate date ticks 
    _ = plt.xticks(rotation=90) 
        
    # Save figure
    plt.savefig('IMAGEs/SST-Selection.png', dpi=300, bbox_inches='tight')
    # Close figure
    plt.close(fig)      
    
    
def Plot_Deenish_temperature(DBO, T):    
    fig, ax = plt.subplots(1)
    
    #time = [i.timestamp() for i in DBO.buoy['time']]
    time = [np.datetime64(i) for i in DBO.buoy['time']]
    
    l1, = ax.plot(time, T, linewidth=.5, label='Buoy')
    
   
    plt.title('Temperature at Deenish Island', fontsize=12)
    
   
    plt.ylabel('$^\circ$C', fontsize=12)
    
   
    plt.grid()
    
    # Model timestamp
    #tiempo = [i.timestamp() for i in DBO.time]
    tiempo = [np.datetime64(i) for i in DBO.time]

    l2, = ax.plot(tiempo, DBO.temp, color='C1', linewidth=.5, label='NWSHELF')
    
    ax.set_xlim([min(time), max(tiempo)])
   
    # Climatology time
    # C = [i.timestamp() for i in DBO.Deenish_time]
    C = [np.datetime64(i) for i in DBO.Deenish_time]
    
    l3, = ax.plot(C, DBO.Deenish_seas, color='C2', linewidth=.5, label='Climatology')
    l4, = ax.plot(C, DBO.Deenish_pc90, color='C3', linewidth=.5, label='90-th pctl')

    # Add legend
    plt.legend(handles=[l1, l2, l3, l4], fontsize=8)
    
    fill_mhw(ax, time, T, C, DBO.Deenish_pc90)
        
   
    # Set date ticks format
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%d-%b"))
    
    ax.tick_params(axis='both', labelsize=8)
    # Rotate date ticks 
    _ = plt.xticks(rotation=90) 
    
    
        
    # Save figure
    plt.savefig('IMAGES/Deenish-temp.png', dpi=300, bbox_inches='tight')
    # Close figure
    plt.close(fig)   
    
    
def Plot_Deenish(DBO, var):
    fig, ax = plt.subplots(1)
    
    try:
        l1, = ax.plot(DBO.buoy['time'], DBO.buoy[var], linewidth=.5, label='Buoy')
    except KeyError:
        print(f'\nError in Plot_Deenish: "{var}" is not a valid parameter.\n' + \
              'Valid parameters are: ' + str(list(DBO.buoy.keys())))
        return    
    
    # Set title
    plt.title(f'{names[var]} at Deenish Island', fontsize=12)
    
    # Set y-axis label (units)
    plt.ylabel(units[var], fontsize=12)
    
    # For RFU, make sure lower y-axis limit is 0
    if var == 'chl':
        ax.set_ylim([0, max(DBO.buoy[var]) + .1])
        
    # Show grid
    plt.grid()
    
    
    
    if var == 'temp':
        l2, = ax.plot(DBO.time, DBO.temp, color='C1', linewidth=.5, label='NWSHELF')
        # Set x-axis limits
        ax.set_xlim([min(DBO.buoy['time']), max(DBO.time)])
       
        
        l3, = ax.plot(DBO.Deenish_time, DBO.Deenish_seas, color='C2', linewidth=.5, label='Climatology')
        l4, = ax.plot(DBO.Deenish_time, DBO.Deenish_pc90, color='C3', linewidth=.5, label='90-th pctl')
    
        # Add legend
        plt.legend(handles=[l1, l2, l3, l4], fontsize=8)
        
        fill_mhw(ax, DBO.buoy['time'], DBO.buoy[var], DBO.Deenish_time, DBO.Deenish_pc90)
        
    else:
        
        # Set x-axis limits
        ax.set_xlim([min(DBO.buoy['time']), max(DBO.buoy['time'])])
        
    # Set date ticks format
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%d-%b"))
    
    ax.tick_params(axis='both', labelsize=8)
    # Rotate date ticks 
    _ = plt.xticks(rotation=90) 
    
    
        
    # Save figure
    plt.savefig(f'IMAGEs/Deenish-{var}.png', dpi=300, bbox_inches='tight')
    # Close figure
    plt.close(fig)      
    
def fill_mhw(ax, x1, y1, x2, y2):
    
    x1 = [i.astype('float') for i in x1]
    x2 = [i.astype('float') for i in x2]
    xfill = np.sort(np.concatenate([x1, x2]))
    y1fill = np.interp(xfill, x1, y1)
    y2fill = np.interp(xfill, x2, y2)
    xfill = [datetime.fromtimestamp(i/1000000) for i in xfill]
    # ax.fill_between(xfill, y1fill, y2fill, where=y1fill < y2fill, interpolate=True, color='dodgerblue', alpha=0.2)
    ax.fill_between(xfill, y1fill, y2fill, where=y1fill > y2fill, interpolate=True, color='crimson', alpha=0.9)

    
def Plot_Deenish_YY(DBO, var1, var2):
    fig, ax1 = plt.subplots(1)
    
    try:
        ax1.plot(DBO.buoy['time'], DBO.buoy[var1], linewidth=.5, color='C0')
    except KeyError:
        print(f'\nError in Plot_Deenish: "{var1}" is not a valid parameter.\n' + \
              'Valid parameters are: ' + str(list(DBO.buoy.keys())))
        return   
    
    # Show grid
    plt.grid()
    
    ax2 = ax1.twinx()
    try:
        ax2.plot(DBO.buoy['time'], DBO.buoy[var2], linewidth=.5, color='C1')
    except KeyError:
        print(f'\nError in Plot_Deenish: "{var1}" is not a valid parameter.\n' + \
              'Valid parameters are: ' + str(list(DBO.buoy.keys())))
        return    
    
    # Set title
    plt.title(f'{names[var1]} & {names[var2]} at Deenish Island', fontsize=12)
    
    # Set y-axis label (units)
    ax1.set_ylabel(units[var1], fontsize=12, color='C0')
    ax2.set_ylabel(units[var2], fontsize=12, color='C1')
    
    ax1.tick_params(axis='y', color='C0', labelcolor='C0')
    ax2.tick_params(axis='y', color='C1', labelcolor='C1')
    
    # Set x-axis limits
    ax1.set_xlim([min(DBO.buoy['time']), max(DBO.buoy['time'])])
    # For RFU, make sure lower y-axis limit is 0
    if var1 == 'chl':
        ax1.set_ylim([0, max(DBO.buoy[var1]) + .1])
    if var2 == 'chl':
        ax2.set_ylim([0, max(DBO.buoy[var2]) + .1])
       
       
    # Set date ticks format
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    ax1.xaxis.set_minor_formatter(mdates.DateFormatter("%d-%b"))
    
    ax1.tick_params(axis='both', labelsize=8)
    ax2.tick_params(axis='both', labelsize=8)
    # Rotate date ticks 
    _ = plt.xticks(rotation=90)   
    
    # Save figure
    plt.savefig(f'IMAGEs/Deenish-{var1}-{var2}.png', dpi=300, bbox_inches='tight')
    # Close figure
    plt.close(fig)  