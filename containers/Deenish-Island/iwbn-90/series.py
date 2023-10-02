import plotly.graph_objects as go
import plotly
import json

def timeSeries(title, time, data, climatology=None, SST=None):
    ''' Create time series figure '''

    # Create figure
    fig = go.Figure()

    # Temperature time series
    fig.add_trace(go.Scatter(
                  name="In-situ seawater temperature",
                  mode="lines", x=time, y=data
              ))

    if climatology:

        DOY, seas, PC90 = climatology

        # Add climatology traces (seasonal cycle and PCT. 90)

        fig.add_trace(go.Scatter(
                      name="PCT. 90",
                      mode="lines", x=DOY, y=PC90,
                      hoverinfo="none",
                      line=dict(width=0.5),
                  ))

        fig.add_trace(go.Scatter(
                      name="climatology",
                      mode="lines", x=DOY, y=seas,
                      hoverinfo="none",
                      line=dict(width=0.5),
                  ))
    
    if SST:
   
        SSTtime, SSTfnd = SST

        fig.add_trace(go.Scatter(
                      name="Remote-Sensing SST",
                      mode="lines", x=SSTtime, y=SSTfnd,
                      line=dict(width=0.5),
                  ))

    fig.update_layout(title=title,
                      yaxis_title='°C',
                      yaxis_tickformat='.1f',
                      xaxis_range=[time[0], time[-1]])

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
