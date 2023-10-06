import matplotlib.pyplot as plt
from datetime import datetime
from pickle import load
from json import loads
import numpy as np
from PIL import Image

def set_size(w,h, ax=None):
    """ w, h: width, height in inches """
    if not ax: ax=plt.gca()
    l = ax.figure.subplotpars.left
    r = ax.figure.subplotpars.right
    t = ax.figure.subplotpars.top
    b = ax.figure.subplotpars.bottom
    figw = float(w)/(r-l)
    figh = float(h)/(t-b)
    ax.figure.set_size_inches(figw, figh)

def windArrow(PKL, fout):
    ''' Draw Met Eireann like wind arrows '''
    
    ''' Set speed color scale following Beaufort scale '''
    Beaufort = dict(low=(0, 2, 6, 12, 20, 29, 39, 50, 62, 75, 89, 103, 118),
                    high=(1, 5, 11, 19, 28, 38, 49, 61, 74, 88, 102, 117, 1e9),
                    color=('#D3D3D3', '#AEF1F9', '#96F7DC', '#96F7B4', 
                           '#6FF46F', '#73ED12', '#A4ED12', '#DAED12', 
                           '#EDC212', '#ED8F12', '#ED6312', '#ED2912', '#D5102D'))                    
    
    # Load forecast data
    with open(PKL, 'rb') as f:   
        data = load(f)
        
    # Retrieve u, v components of wind
    u, v, time = data['u_wind_fc'], data['v_wind_fc'], data['wind_time_fc']
    u, v, time = np.array(loads(u)), np.array(loads(v)), loads(time)

    # Format time appropriately
    times = [datetime.strptime(i, '%Y-%m-%d %H:%M') for i in time]
    x = np.array( [(i - times[0]).total_seconds()/3600 for i in times] )

    time = [datetime.strptime(i, '%Y-%m-%d %H:%M') for i in time]
    time = [i.strftime('%d %b\n %H h') for i in time]
    
    fig, ax = plt.subplots(figsize=(12, 1))
    
    ax.set_xlim([x[0]-2, x[-1]+2]); ax.set_ylim([-1, 1])
    
    # Convert to km/h
    # u, v = 3.6*u, 3.6*v
    
    # Round wind speed values
    speed = np.round((u**2 + v**2)**.5)
    # Add gray circles
    for i, s in zip(x, speed):
        for l, h, c in zip(Beaufort['low'], Beaufort['high'], Beaufort['color']):
            if s >= l and s <= h:
                color = c
        ax.scatter(i, 0, s=300, color=color, 
                   linewidths=4, facecolors='none')    
    ax.scatter(x, np.zeros_like(x), s=400, 
               linewidths=1, facecolors='none')    
    # Loop along wind data
    for X, v, U, V, t in zip(x, speed, u, v, time):
        for l, h, c in zip(Beaufort['low'], Beaufort['high'], Beaufort['color']):
            if v >= l and v <= h:
                color = c
        if v < 10:
            x_shift = .3
        else:
            x_shift = .5
        ax.text(X-x_shift, -.08, f'%d' % v, fontsize=8)
        ax.text(X-1, -.95, t, fontsize=8)
        
        unorm, vnorm = U/v, V/v
        # Add arrows
        ax.quiver(np.array(X), np.array(0), np.array(unorm), np.array(vnorm), 
                  color=color, headwidth=10, scale=50, width=0.004, headlength=10)
    # Add units
    plt.text(-4,-.1,'km/h')
    # Add white circles
    ax.scatter(x, np.zeros_like(x), s=100, color='white', linewidths=4, facecolors='white')
    
    fig.tight_layout(); set_size(12,1); plt.axis('off')
    
    # Save image
    plt.savefig(fout, dpi=500)
    
    ''' Rearrange elements in image using PIL '''
    # Open image created above
    im = Image.open(fout)
    
    left, top, right, bottom = 80, 470, 250, 535
    # Crop units    
    im1 = im.crop((left, top, right, bottom))
        
    left, top, right, bottom = 525, 360, 3350, 760
    # Crop first 36 hours of forecast    
    im2 = im.crop((left, top, right, bottom))
        
    left, top, right, bottom = 3350, 360, 6200, 760
    # Crop last 36 hours of forecast    
    im3 = im.crop((left, top, right, bottom))
    
    # Create new (final) image    
    dst = Image.new('RGB', (3100, 800), color='white')
    # Paste units
    dst.paste(im1, (0, 100))
    # Paste first 36 hours of forecast
    dst.paste(im2, (200, 0))
    # Paste units
    dst.paste(im1, (0, 500))
    # Paste last 36 hours of forecast
    dst.paste(im3, (200, 400))
    
    # Save image
    dst.save(fout)
