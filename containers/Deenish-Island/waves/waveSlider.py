import plotly.graph_objects as go
import numpy as np
import plotly
import json

def waveSlider(lon, lat, time, waves, coast, buoy):
    x_coast, y_coast = coast
    x_buoy,  y_buoy  = buoy

    trace1 = []

    # Add traces, one for each slider step
    for i in range(len(time)):
        wave = waves[i, :, :]
        trace1.append( go.Contour(
            z=wave, x=lon, y=lat,
            colorscale='Portland',  
            hoverinfo='z', line_width=0, line_smoothing=0.85,
            colorbar=dict(
                title=dict(text='m', font=dict(size=24)),
                tickvals=[0, 1, 2, 3, 4, 5],
                ticktext=['0', '1.0', '2.0', '3.0', '4.0', '5.0'],
                tickfont=dict(size=24),
            ),
            contours=dict(
                start=0,
                end=5,
                size=0.1,
            ),
         ))

    trace2 = [ go.Scatter(
        x=x_coast, y=y_coast, 
        line={'color': 'black', 'width': 4}, 
        hoverinfo='none',
    ) ]            

    trace3 = [ go.Scatter(
        x=(x_buoy,), y=(y_buoy,), mode='markers', text='Deenish Island', textposition='middle right',
        marker={'size': 20, 'symbol': 'cross-thin', 'line': {'color': 'black', 'width': 1}}, 
        hoverinfo='none',
    ) ]            

    # Create figure
    fig = go.Figure(data=trace1+trace2+trace3)

    # Create and add slider
    steps = []
    for i in range(len(time)):
        # Hide all traces
        step = dict(
            method='restyle',
            args = ['visible', [False] * len(fig.data)],
            label=time[i].strftime('%d-%b %H:%M'),
        )
  
        # Enable the traces we want to see
        step['args'][1][i] = True
        step['args'][1][-1] = True
        step['args'][1][-2] = True
    
        # Add step to step list
        steps.append(step)

    sliders = [dict(
        active=len(time)-1,
        currentvalue={"prefix": "", "xanchor": "center"},
        pad={"t": 50},
        len=1,
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
