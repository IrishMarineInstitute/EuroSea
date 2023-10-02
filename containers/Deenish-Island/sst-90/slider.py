import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import subprocess
import plotly
import glob
import json
import os

from log import set_logger, now
logger = set_logger()

pio.kaleido.scope.chromium_args += ("--single-process",) 

def VideoMaker(path, filename):
    ''' Create video from image list '''
    
    logger.info('INSIDE VIDEOMAKER FUNCTION NOW!')

    subprocess.call(f'ffmpeg -r 1 -i {path}/%02d.png -vcodec libx264 -acodec aac {filename}', shell=True)

def Slider(case, lon, lat, time, data, coast, buoy, bathymetry, colorscale, tickvals, contours):
    ''' Create slider figure to display on portal '''

    # Coastline coordinates
    x_coast, y_coast = coast

    # Buoy(s) coordinates
    x_buoy,  y_buoy  = buoy

    # Bathymetry
    x_bathy, y_bathy = bathymetry

    # Initialize 1st trace: the 2-D contour data
    trace1 = []
    # Add traces, one for each slider step
    for i in range(len(time)):
        datos = data[i, :, :]
        trace1.append( go.Contour(
            z=datos, x=lon, y=lat,
            colorscale=colorscale,  
            hoverinfo='z', line_width=0, line_smoothing=0.85,
            colorbar=dict(
                title=dict(text='°C', font=dict(size=48)),
                tickvals=tickvals,
                tickfont=dict(size=48),
            ),
            contours=contours,
         ))

    # 2nd trace is the coastline
    trace2 = [ go.Scatter(
        x=x_coast, y=y_coast, 
        line={'color': 'black', 'width': 8}, 
        hoverinfo='none',
    ) ]            

    # 3rd trace is the buoys
    trace3 = [ go.Scatter(
        x=np.array(x_buoy), y=np.array(y_buoy), mode='markers+text', text=["Deenish", "M2", "M3", "M4", "M5", "M6"], 
        textposition=["middle left", "bottom center", "bottom right", "top left", "bottom left", "bottom left"],
        marker={'size': 48, 'symbol': 'cross-thin', 'line': {'color': 'black', 'width': 4}}, 
        hoverinfo='none',
    ) ]            

    # Traces 4 is the bathymetry contour 
    trace4 = [go.Scatter(
        x=x_bathy, y=y_bathy, 
        line={'color': 'black', 'width': 4, 'dash': 'dash'}, 
        hoverinfo='none',
            )]
    
    ''' This code is to create an animation from image frames '''

    # Set output directory for frames
    path = f'/data/SST/FRAMES/{case}' 
    if not os.path.isdir(path):
        os.makedirs(path)

    images = [] 

    for i, frame in enumerate(trace1):
        logger.info(f'{now()} Printing image {case}-{i:02d}...')
        # Create new frame
        frame = go.Figure(data=[frame]+trace2+trace3+trace4)
        # Add layout
        frame.update_layout(width=2000, height=1948, showlegend=False,
            xaxis=dict(mirror=True, showline=True, ticks='outside', 
                    tickvals=[-25, -20, -15, -10, -5],
                    ticktext=['25ºW', '20ºW', '15ºW', '10ºW', '5ºW'],
                    automargin=True, range=[-25, -5]),
            yaxis=dict(mirror=True, showline=True, ticks='outside', 
                    tickvals=[46, 50, 54, 58],
                    ticktext=['46ºN', '50ºN', '54ºN', '58ºN'],
                    range=[46, 58]),
            font_family='Sans-Serif', font_size=48, 
            title=time[i].strftime('%d %b'), title_x=0.5)

        # Save image
        pio.write_image(frame, f'{path}/{i:02d}.png')
        # Append image name to list 
        images.append(f'{path}/{i:02}.png')

    videopath = f'/data/SST/VIDEOS/'

    VideoMaker(f'{path}', f'{videopath}{case}.mp4')

    return f'{videopath}{case}.mp4'
