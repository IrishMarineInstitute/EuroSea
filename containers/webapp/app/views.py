from flask import render_template, request, url_for, redirect, send_file
from datetime import datetime
from mhw_historical import mhw_historical
from ostia import OSTIA, get_ostia_times
from pickle import load
from app import app
import numpy as np
import pandas as pd
import shutil
import glob
import json
import os
import util

def dataload(pkl, dic):
    ''' Load data from container. Update dictionary '''
    try:
        with open(pkl, 'rb') as f:
            var = load(f)
    except FileNotFoundError:
        var = {}
    return {**dic, **var}

#######################################################
#                                                     #
#                 HOME    PAGE                        #
#                                                     #
#######################################################

''' Home page English version '''
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'Deenish-Operational'  in request.form:
            return redirect(url_for('Deenish_Island'))
        elif 'Deenish-Historical' in request.form:
            return redirect(url_for('Deenish_Island_Historical'))
        elif 'Deenish-Remote-Sensing' in request.form:
            return redirect("https://www.marine.ie/site-area/data-services/remote-sensing/remote-sensing")
        elif 'Campello-Operational' in request.form:
            return redirect(url_for('El_Campello'))
        elif 'Campello-Historical' in request.form:
            return redirect(url_for('El_Campello_Historical'))
        elif 'Campello-Waves' in request.form:
            return redirect(url_for('El_Campello_Waves'))
        elif 'Galway-Bay' in request.form:
            return redirect(url_for('galway'))
        elif 'HELPDESK' in request.form:
            return redirect(url_for('helpdesk'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('home.html')

''' Home page Spanish version '''
@app.route('/es', methods=['GET', 'POST'])
def home_es():
    if request.method == 'POST':
        if 'Deenish-Operational'  in request.form:
            return redirect(url_for('Deenish_Island'))
        elif 'Deenish-Historical' in request.form:
            return redirect(url_for('Deenish_Island_Historical'))
        elif 'Deenish-Remote-Sensing' in request.form:
            return redirect("https://www.marine.ie/site-area/data-services/remote-sensing/remote-sensing")
        elif 'Campello-Operational' in request.form:
            return redirect(url_for('El_Campello_es'))
        elif 'Campello-Historical' in request.form:
            return redirect(url_for('El_Campello_Historical_es'))
        elif 'Campello-Waves' in request.form:
            return redirect(url_for('El_Campello_Waves_es'))
        elif 'HELPDESK' in request.form:
            return redirect(url_for('helpdesk_es'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('home_es.html')

@app.route('/helpdesk')
def helpdesk():
    return render_template('helpdesk.html')

@app.route('/es/helpdesk')
def helpdesk_es():
    return render_template('helpdesk_es.html')

@app.route('/sensor-specification-sheets', methods=['GET', 'POST'])
def sensor_specification_sheets():
    if request.method == 'POST':
        if 'AIRMAR' in request.form:
            return send_file('/app/app/static/pdf/17-472-01.pdf', as_attachment=True)
        elif 'Airmar' in request.form:
            return send_file('/app/app/static/pdf/Airmar_h2183.pdf', as_attachment=True)
        elif 'Maximet-GMX500' in request.form:
            return send_file('/app/app/static/pdf/1957-008_Maximet-gmx500_Iss_7.pdf', as_attachment=True)
        elif 'Maximet-Manual' in request.form:
            return send_file('/app/app/static/pdf/1957-PS-021-Maximet-Manual-Issue-8.pdf', as_attachment=True)
        elif 'Zpulse' in request.form:
            return send_file('/app/app/static/pdf/4420_4520_4830_4930_Zpulse_Doppler_Current_Sensor_Jan20.pdf', as_attachment=True)
        elif 'TD266-Zpulse' in request.form:
            return send_file('/app/app/static/pdf/td266-zpulse-dcs-4420-4830-4520-4930_Feb20.pdf', as_attachment=True)
        elif 'DCPS' in request.form:
            return send_file('/app/app/static/pdf/5400_DCPS_Jan20.pdf', as_attachment=True)
        elif 'EXO' in request.form:
            return send_file('/app/app/static/pdf/EXO-User-Manual-Web_K.pdf', as_attachment=True)
        elif 'Datalogger-TD293' in request.form:
            return send_file('/app/app/static/pdf/SMARTGUARD-Datalogger-TD293.pdf', as_attachment=True)
        elif 'SmartGuard' in request.form:
            return send_file('/app/app/static/pdf/SmartGuard_Jan20.pdf', as_attachment=True)
        elif 'YSI-EXO-Brochure' in request.form:
            return send_file('/app/app/static/pdf/YSI-EXO-Brochure.pdf', as_attachment=True)
        elif 'D4250-DB1750' in request.form:
            return send_file('/app/app/static/pdf/d426_db1750-buoy-platform.pdf', as_attachment=True)
        elif 'TD304' in request.form:
            return send_file('/app/app/static/pdf/td304-manual-dcps.pdf', as_attachment=True)
    else:
        return render_template('sensor-specification-sheets.html')

@app.route('/es/sensor-specification-sheets', methods=['GET', 'POST'])
def sensor_specification_sheets_es():
    if request.method == 'POST':
        if 'AIRMAR' in request.form:
            return send_file('/app/app/static/pdf/17-472-01.pdf', as_attachment=True)
        elif 'Airmar' in request.form:
            return send_file('/app/app/static/pdf/Airmar_h2183.pdf', as_attachment=True)
        elif 'Maximet-GMX500' in request.form:
            return send_file('/app/app/static/pdf/1957-008_Maximet-gmx500_Iss_7.pdf', as_attachment=True)
        elif 'Maximet-Manual' in request.form:
            return send_file('/app/app/static/pdf/1957-PS-021-Maximet-Manual-Issue-8.pdf', as_attachment=True)
        elif 'Zpulse' in request.form:
            return send_file('/app/app/static/pdf/4420_4520_4830_4930_Zpulse_Doppler_Current_Sensor_Jan20.pdf', as_attachment=True)
        elif 'TD266-Zpulse' in request.form:
            return send_file('/app/app/static/pdf/td266-zpulse-dcs-4420-4830-4520-4930_Feb20.pdf', as_attachment=True)
        elif 'DCPS' in request.form:
            return send_file('/app/app/static/pdf/5400_DCPS_Jan20.pdf', as_attachment=True)
        elif 'EXO' in request.form:
            return send_file('/app/app/static/pdf/EXO-User-Manual-Web_K.pdf', as_attachment=True)
        elif 'Datalogger-TD293' in request.form:
            return send_file('/app/app/static/pdf/SMARTGUARD-Datalogger-TD293.pdf', as_attachment=True)
        elif 'SmartGuard' in request.form:
            return send_file('/app/app/static/pdf/SmartGuard_Jan20.pdf', as_attachment=True)
        elif 'YSI-EXO-Brochure' in request.form:
            return send_file('/app/app/static/pdf/YSI-EXO-Brochure.pdf', as_attachment=True)
        elif 'D4250-DB1750' in request.form:
            return send_file('/app/app/static/pdf/d426_db1750-buoy-platform.pdf', as_attachment=True)
        elif 'TD304' in request.form:
            return send_file('/app/app/static/pdf/td304-manual-dcps.pdf', as_attachment=True)
    else:
        return render_template('sensor-specification-sheets_es.html')

#######################################################
#                                                     #
#                   Galway Bay                        #
#                                                     #
#######################################################

''' Galway Bay '''
@app.route('/Galway-Bay/', methods=['GET', 'POST'])
def galway():

    if request.method == 'POST':
        if 'Renville'  in request.form:
            return redirect(url_for('dashboard', site='Renville'))
        elif 'Ballinacourty'  in request.form:
            return redirect(url_for('dashboard', site='Ballinacourty'))
        elif 'Blackweir'  in request.form:
            return redirect(url_for('dashboard', site='Blackweir'))
        elif 'Cave'  in request.form:
            return redirect(url_for('dashboard', site='Cave'))
        elif 'Killeenaran'  in request.form:
            return redirect(url_for('dashboard', site='Killeenaran'))
        elif 'Tarrea'  in request.form:
            return redirect(url_for('dashboard', site='Tarrea'))
        elif 'Kinvara'  in request.form:
            return redirect(url_for('dashboard', site='Kinvara'))
        elif 'Crushoa'  in request.form:
            return redirect(url_for('dashboard', site='Crushoa'))
        elif 'Parkmore'  in request.form:
            return redirect(url_for('dashboard', site='Parkmore'))
        elif 'Traught'  in request.form:
            return redirect(url_for('dashboard', site='Traught'))
        elif 'Newtownlynch'  in request.form:
            return redirect(url_for('dashboard', site='Newtownlynch'))
        elif 'New-Quay'  in request.form:
            return redirect(url_for('dashboard', site='New-Quay'))
        elif 'Flaggy-Shore'  in request.form:
            return redirect(url_for('dashboard', site='Flaggy-Shore'))
        elif 'Bellharbour'  in request.form:
            return redirect(url_for('dashboard', site='Bellharbour'))
        elif 'Bishops-Quarter'  in request.form:
            return redirect(url_for('dashboard', site='Bishop_s-Quarter'))
        elif 'Ballyvaughan'  in request.form:
            return redirect(url_for('dashboard', site='Ballyvaughan'))
        elif 'Gleninagh' in request.form:
            return redirect(url_for('dashboard', site='Gleninagh'))
    else:
        return render_template('galway.html', latitude=53.2, longitude=-9.1)

''' Galway Bay Dashboard '''
@app.route('/Galway-Bay/<site>/')
def dashboard(site):
    data = dataload(f'/data/pkl/Galway-Bay/{site}.pkl', {})
    data = dataload(f'/data/BIRDS/{site}-WEB.pkl', data)
    return render_template('galway-dashboard.html', **data)

''' Galway Bay eBird '''
@app.route('/eBird')
def form():
    ''' Process bird requests from Leaflet map '''

    # Get longitude of request 
    longitude = request.args.get('longitude', type=float)
    # Get latitude of request
    latitude = request.args.get('latitude', type=float)
    # Get corresponding site name (Renville, Kinvara, etc.)
    site = request.args.get('site')
    # Get formatted site name for archive file name
    # as generated by the back-end bird container.
    filename = site.replace("'", "_").replace(" ", "-") 

    root = '/data/BIRDS/'
    with open(f'{root}{filename}-WEB.pkl', 'rb') as f:
        data = load(f) # Load eBird observations

    # Get coordinates of sightings
    lon, lat = data.get('lonBird'), data.get('latBird')
    # Convert strings to numbers
    lon = [float(i) for i in lon]
    lat = [float(i) for i in lat]
    # Get times and sites of observations
    t, loc = data.get('t'), data.get('loc')
    # Get species names, both common and scientific
    cm, sc = data.get('cm'), data.get('sc')
    # Get image files and paths
    pic = data.get('pic')
    # Get title
    title = data.get('title')

    where, common, species, picture, when = [], [], [], [], []
    # Keep only those observations matching the clicked marker
    for i, j, T, Com, Sci, Pic, Loc in zip(lon, lat, t, cm, sc, pic, loc):
        if ( abs(i - longitude) < 1e-8 ) and (abs(j - latitude) < 1e-8):
            where.append(Loc)
            common.append(Com)
            species.append(Sci)
            picture.append(Pic)
            when.append(T)

    # Move bird pictures to static folder
    imdir = '/app/app/static/BIRDS/'
    if not os.path.isdir(imdir):
        os.makedirs(imdir)

    for pic in picture:
        name = os.path.basename(pic)
        if not os.path.isfile(f'{imdir}{name}'):
            shutil.copy2(pic, imdir)

    im = []
    for pic in picture:
        folder = os.path.dirname(pic)
        im.append(pic.replace(folder, '../static/BIRDS'))

    return render_template("form.html", 
            longitude=longitude, latitude=latitude,
            site=site, title=title,
            entries=zip(where, common, species, im, when))

#######################################################
#                                                     #
#                Deenish Island                       #
#                                                     #
#######################################################

''' Dedicated home page '''
@app.route('/Deenish', methods=['GET', 'POST'])
def Deenish():
    if request.method == 'POST':
        if 'Deenish-Operational' in request.form:
            return redirect(url_for('Deenish_Island'))
        elif 'Deenish-Historical' in request.form:
            return redirect(url_for('Deenish_Island_Historical'))
        elif 'Deenish-Remote-Sensing' in request.form:
            return redirect(url_for('Deenish_Island_Remote_Sensing'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('Deenish.html')
        
''' Deenish: in-situ operational (EN) '''
@app.route('/Deenish-Island')
def Deenish_Island():

    # Load observations
    data = dataload('/data/pkl/BUOY-1.pkl', {})
    # Load forecasts
    data = dataload('/data/pkl/MODEL-1.pkl', data)
    # Load wave forecast
    data = dataload('/data/pkl/DEENISH-WAVE-SERIES.pkl', data)

    return render_template('Deenish-Island.html', **data) 

''' Deenish: remote sensing (EN) '''
'''
@app.route('/Deenish-Island-Remote-Sensing', methods=['GET', 'POST'])
def Deenish_Island_Remote_Sensing():

    if request.method == 'POST':

        if 'sst'  in request.form:
            return redirect(url_for('sst'))
        elif 'anm' in request.form:
            return redirect(url_for('anm'))
        elif 'mhw' in request.form:
            return redirect(url_for('mhw'))
        elif 'his' in request.form:
            return redirect(url_for('his'))
        elif 'chl' in request.form:
            return redirect(url_for('chl'))
        elif 'hab' in request.form:
            return redirect(url_for('hab'))
        elif 'wav' in request.form:
            return redirect(url_for('wav'))
        elif 'adt' in request.form:
            return redirect(url_for('adt'))
        else:
            render_template('notexist.html')

    else:
        return render_template('remote-sensing.html') 
'''

''' Deenish: sea surface temperature (EN) '''
'''
@app.route('/Deenish-Island-Remote-Sensing/Sea-Surface-Temperature')
def sst():
    return render_template('sst.html')
'''

@app.route('/sst', methods=['GET', 'POST'])
def sstframe():

    if request.method == 'POST':
        userdate = request.form.get('select-date')
        # Load map for requested date
        return redirect(url_for('sstuserdate', userdate=userdate))
    else:
        # Read last two weeks SST figure
        data = dataload('/data/SST.pkl', {})
        # Get time list in SST database
        ini, timelist = get_ostia_times()
        # Append time information for date selection calendar widgets
        data['ini'] = ini; data['timelist'] = timelist
        # Return template
        return render_template('sst-iframe.html', **data)

@app.route('/sst/<userdate>')
def sstuserdate(userdate):

    # Read SST for selected date
    fig, timelist = OSTIA(userdate, 'sst')
    # Wrap everything before rendering template
    data = dict(SST=fig, ini=userdate, timelist=timelist)
    # Return template
    return render_template('sst-iframe.html', **data)

''' Deenish: sea surface temperature anomaly (EN) '''
'''
@app.route('/Deenish-Island-Remote-Sensing/Sea-Surface-Temperature-Anomaly')
def anm():
    return render_template('anm.html')
'''

@app.route('/anm', methods=['GET', 'POST'])
def anmframe():

    if request.method == 'POST':
        userdate = request.form.get('select-date')
        # Load map for requested date
        return redirect(url_for('anmuserdate', userdate=userdate))
    else:
        # Read last two weeks ANM figure
        data = dataload('/data/ANM.pkl', {})
        # Get time list in SST database
        ini, timelist = get_ostia_times()
        # Append time information for date selection calendar widgets
        data['ini'] = ini; data['timelist'] = timelist
        # Return template
        return render_template('anm-iframe.html', **data)

@app.route('/anm/<userdate>')
def anmuserdate(userdate):

    # Read ANM for selected date
    fig, timelist = OSTIA(userdate, 'anm')
    # Wrap everything before rendering template
    data = dict(ANM=fig, ini=userdate, timelist=timelist)
    # Return template
    return render_template('anm-iframe.html', **data)


''' Deenish: marine heat waves (EN) '''
'''
@app.route('/Deenish-Island-Remote-Sensing/Marine-Heat-Waves')
def mhw():
    return render_template('mhw.html')
'''

@app.route('/mhw', methods=['GET', 'POST'])
def mhwframe():

    if request.method == 'POST':
        userdate = request.form.get('select-date')
        # Load map for requested date
        return redirect(url_for('mhwuserdate', userdate=userdate))
    else:
        # Read last two weeks MHW figure
        data = dataload('/data/MHW.pkl', {})
        # Get time list in SST database
        ini, timelist = get_ostia_times()
        # Append time information for date selection calendar widgets
        data['ini'] = ini; data['timelist'] = timelist[4::]
        # Return template
        return render_template('mhw-iframe.html', **data)

@app.route('/mhw/<userdate>')
def mhwuserdate(userdate):

    # Read SST for selected date
    fig, timelist = OSTIA(userdate, 'mhw')
    # Wrap everything before rendering template
    data = dict(MHW=fig, ini=userdate, timelist=timelist[4::])
    # Return template
    return render_template('mhw-iframe.html', **data)

''' Deenish: chlorophyll (EN) '''
'''
@app.route('/Deenish-Island-Remote-Sensing/Chlorophyll')
def chl():
    return render_template('chl.html')
'''

@app.route('/chl')
def chlframe():

    data = dataload('/data/pkl/CHL.pkl', {})
    return render_template('chl-iframe.html', **data)

''' Deenish: wave forecast (EN) '''
'''
@app.route('/Deenish-Island-Waves')
def wav():

    data = dataload('/data/pkl/DEENISH-WAVES.pkl', {})
    return render_template('wav.html', **data)
'''

''' Deenish: Absolute Dynamic Topography (EN) '''
'''
@app.route('/Deenish-Island-Remote-Sensing/Absolute-Dynamic-Topography')
def adt():

    for pic in glob.iglob(os.path.join('/data/IMG/', '*.png')):
        if os.path.isfile(pic):
            shutil.copy2(pic, '/app/app/static/')
            os.remove(pic)

    return render_template('adt.html')
'''

''' Deenish: Red-Band Difference (EN) '''
'''
@app.route('/Deenish-Island-Remote-Sensing/Red-Band-Difference')
def hab():
    return render_template('hab.html')
'''

@app.route('/rbn')
def habframe():

    if not os.path.isdir('/app/app/static/HAB/daily'):
        os.makedirs('/app/app/static/HAB/daily')
    # Process daily images
    dates, daily = [], [] # Date list and figure list
    for pic in sorted(glob.iglob(os.path.join('/data/HAB/mv/', '*.png'))):
        if os.path.isfile(pic):
            dates.append(datetime.strptime(os.path.basename(pic)[9:17],
                '%Y%m%d').strftime('%Y-%b-%d'))
            daily.append('../static/HAB/daily/' + os.path.basename(pic))
            if not os.path.isfile('/app/app/static/HAB/daily/' + os.path.basename(pic)):
                shutil.copy2(pic, '/app/app/static/HAB/daily/')

    if not os.path.isdir('/app/app/static/HAB/weekly'):
        os.makedirs('/app/app/static/HAB/weekly')
    # Process weekly images
    Mon, Sun = [], [] # Monday (initial) and Sunday (end) dates lists
    weekly = []
    for pic in sorted(glob.iglob(os.path.join('/data/HAB/wk/', '*.png'))):
        if os.path.isfile(pic):
            Mon.append(datetime.strptime(os.path.basename(pic)[9:17],
                '%Y%m%d').strftime('%Y-%b-%d'))
            Sun.append(datetime.strptime(os.path.basename(pic)[18:26],
                '%Y%m%d').strftime('%Y-%b-%d'))
            weekly.append('../static/HAB/weekly/' + os.path.basename(pic))
            if not os.path.isfile('/app/app/static/HAB/weekly/' + os.path.basename(pic)):
                shutil.copy2(pic, '/app/app/static/HAB/weekly/')

    data = {'daily': daily, 'dates': dates, 
            'weekly': weekly, 'Monday': Mon, 'Sunday': Sun}

    return render_template('hab-iframe.html', **data)

def buoys():
    # Define buoy NetCDF properties 

    return dict(
            lon=(-10.2122, -5.4302, -10.5483, -9.9991, -6.7043, -15.88135, -9.9326),
            lat=(51.7431, 53.4836, 51.2160, 55.0000, 51.6904, 53.0748, 53.3306),
            nc=('Deenish-Island', 'M2', 'M3', 'M4', 'M5', 'M6', 'Mace-Head'),
            temp=('temp', 'SeaTemperature', 'SeaTemperature', 'SeaTemperature',
                  'SeaTemperature', 'SeaTemperature', 'sbe_temp_avg'))

''' Deenish: historical data selection (EN) '''
'''
@app.route('/Deenish-Island-Remote-Sensing/Historical')
def his():
    return render_template('his.html')
'''

@app.route('/his', methods=['GET', 'POST'])
def hisframe():

    if request.method == 'POST':

        for key in request.form:
            if 'csv' in key:
                return send_file(key, as_attachment=True)

        # Get position selected on the map 
        lon, lat = float(request.form['longitude']), float(request.form['latitude'])

        # Check marker is inside SST domain
        if lon < -25 or lon > -5 or lat < 46 or lat > 58 :
            error = 'SITE MUST BE WITHIN THE RECTANGLE (46ºN, 25ºW) TO (58ºN, 05ºW). SITE MUST BE AT SEA.'
            return render_template('remote-sensing-historical.html', latitude=52, longitude=-15,
                polygon=json.dumps([[46,-25],[58,-25],[58,-5],[46,-5]]), error=error) 

        ''' Find out if the seleted position matches any of the buoys '''
        # Load dictionary with buoy positions, NetCDF names and temperature 
        buoydict, buoy = buoys(), False
        # Coordinates of buoys     
        lons, lats = buoydict.get('lon'), buoydict.get('lat') 
        # NetCDF file names and temperature variables names for each buoy
        ncs, temps = buoydict.get('nc'),  buoydict.get('temp')

        insitu = False
        for i, j, nc, temp in zip(lons, lats, ncs, temps):
            if ( i == lon ) and ( j == lat ):
                buoy = (nc, temp); insitu = True; break # Use this NetCDF 

        MHW, CS = False, False
        if 'MHW' in request.form:
            MHW = True
        if 'CS' in request.form:
            CS = True

        # Produce figure 
        try:
            fig, csvsst, csvclim, csvmhw, csvcs, csvinsitu = mhw_historical(lon, lat, MHW, CS, buoy=buoy)
        except RuntimeError:
            error = 'SITE MUST BE AT SEA.'
            return render_template('remote-sensing-historical.html', latitude=52, longitude=-15,
                polygon=json.dumps([[46,-25],[58,-25],[58,-5],[46,-5]]), error=error) 
   
        # Return figure
        return render_template('figure.html', fig=fig, MHW=MHW, CS=CS, insitu=insitu,
                csvsst=csvsst, csvclim=csvclim, csvmhw=csvmhw, csvcs=csvcs, csvinsitu=csvinsitu)

    else:

        return render_template('remote-sensing-historical.html', latitude=52, longitude=-15,
            polygon=json.dumps([[46,-25],[58,-25],[58,-5],[46,-5]])) 

''' Deenish: Historical Data (EN) '''
@app.route('/Deenish-Island-Historical', methods=['GET', 'POST'])
def Deenish_Island_Historical():

    # Load historical data
    with open('/data/his/Deenish-Island/Deenish-Island.pkl', 'rb') as f: 
        data = load(f)
    timelist = data.index

    if request.method == 'POST':

        # Get dates selected in calendar widgets
        start, end, uv = get_dates(request.form)

        ini, fin = start.replace('-', ''), end.replace('-', '')
    
        if 'submit' in request.form:

            # Address in-situ historical request
            data = new_request(request.form, 'en', 'Deenish')

            # Add whole time list for calendars
            data['timelist'] = timelist

            # Return template
            return render_template('Deenish-Island-Historical.html', **data,  
                date1=start, date2=end, date3=uv, csv='true')

        elif 'temp' in request.form:
            f = f'/data/CSV/csv-temp-{ini}-{fin}.csv'

        elif 'salt' in request.form:
            f = f'/data/CSV/csv-salt-{ini}-{fin}.csv'

        elif 'ph' in request.form:
            f = f'/data/CSV/csv-pH-{ini}-{fin}.csv'

        elif 'O2' in request.form:
            f = f'/data/CSV/csv-O2-{ini}-{fin}.csv'

        elif 'RFU' in request.form:
            f = f'/data/CSV/csv-RFU-{ini}-{fin}.csv'

        elif 'BGA' in request.form:
            f = f'/data/CSV/csv-BGA-{ini}-{fin}.csv'

        elif 'currents' in request.form:
            f = f'/data/CSV/csv-currents-{ini}-{fin}.csv'

        return send_file(f, as_attachment=True)

    else:

        first, last = timelist[0].strftime('%Y-%m-%d'), timelist[-1].strftime('%Y-%m-%d')

        return render_template('Deenish-Island-Historical.html', timelist=timelist, 
            date1=first, date2=last, date3=last, csv='false')

#######################################################
#                                                     #
#                   El Campello                       #
#                                                     #
#######################################################

''' Dedicated home page '''
@app.route('/Campello', methods=['GET', 'POST'])
def Campello():
    if request.method == 'POST':
        if 'Campello-Operational' in request.form:
            return redirect(url_for('El_Campello'))
        elif 'Campello-Historical' in request.form:
            return redirect(url_for('El_Campello_Historical'))
        elif 'Campello-Waves' in request.form:
            return redirect(url_for('El_Campello_Waves'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('Campello.html')

''' El Campello: in-situ operational (EN) '''
@app.route('/El-Campello')
def El_Campello():

    # Load observations
    data = dataload('/data/pkl/BUOY-2.pkl', {})
    # Load forecasts
    data = dataload('/data/pkl/MODEL-2.pkl', data)

    for pic in glob.iglob(os.path.join('/data/IMG/', '*.png')):
        if os.path.isfile(pic):
            shutil.copy2(pic, '/app/app/static/')
            os.remove(pic)

    return render_template('El-Campello.html', **data) 

''' El Campello: in-situ operational (ES) '''
@app.route('/es/El-Campello')
def El_Campello_es():

    # Load observations
    data = dataload('/data/pkl/BUOY-2.pkl', {})
    # Load forecasts
    data = dataload('/data/pkl/MODEL-2.pkl', data)

    for pic in glob.iglob(os.path.join('/data/IMG/', '*.png')):
        if os.path.isfile(pic):
            shutil.copy2(pic, '/app/app/static/')
            os.remove(pic)

    return render_template('El-Campello_es.html', **data) 

''' El Campello: Regional Wave Forecast (EN) '''
@app.route('/El-Campello-Waves')
def El_Campello_Waves():
    # Load remote sensing
    data = dataload('/data/pkl/CAMPELLO-WAVES.pkl', {})

    return render_template('El-Campello-Waves.html', **data)
    
''' El Campello: Regional Wave Forecast (ES) '''
@app.route('/es/El-Campello-Waves')
def El_Campello_Waves_es():
    # Load remote sensing
    data = dataload('/data/pkl/CAMPELLO-WAVES.pkl', {})

    return render_template('El-Campello-Waves_es.html', **data)
    
''' El Campello: Historical Data (EN) '''
@app.route('/El-Campello-Historical', methods=['GET', 'POST'])
def El_Campello_Historical():

    # Load historical data
    with open('/data/his/El-Campello/El-Campello.pkl', 'rb') as f: 
        data = load(f)
    timelist = data.index

    if request.method == 'POST':

        # Get dates selected in calendar widgets
        start, end, uv = get_dates(request.form)

        ini, fin = start.replace('-', ''), end.replace('-', '')
    
        if 'submit' in request.form:

            # Address in-situ historical request
            data = new_request(request.form, 'en', 'Campello')
            
            for key, val in data.items():
                if isinstance(val, pd.Series):
                    data[key] = np.array(val)

            # Add whole time list for calendars
            data['timelist'] = timelist

            # Return template
            return render_template('El-Campello-Historical.html', **data,  
                date1=start, date2=end, date3=uv, csv='true')

        elif 'temp' in request.form:
            f = f'/data/CSV/csv-temp-{ini}-{fin}.csv'

        elif 'tur' in request.form:
            f = f'/data/CSV/csv-tur-{ini}-{fin}.csv'

        elif 'O2' in request.form:
            f = f'/data/CSV/csv-O2-{ini}-{fin}.csv'

        elif 'SWH' in request.form:
            f = f'/data/CSV/csv-swh-{ini}-{fin}.csv'

        elif 'wave' in request.form:
            f = f'/data/CSV/csv-wave-{ini}-{fin}.csv'

        elif 'wind' in request.form:
            f = f'/data/CSV/csv-wind-{ini}-{fin}.csv'

        elif 'currents' in request.form:
            f = f'/data/CSV/csv-currents-{ini}-{fin}.csv'

        return send_file(f, as_attachment=True)

    else:

        first, last = timelist[0].strftime('%Y-%m-%d'), timelist[-1].strftime('%Y-%m-%d')

        return render_template('El-Campello-Historical.html', timelist=timelist, 
            date1=first, date2=last, date3=last, csv='false')

''' El Campello: Historical Data (ES) '''
@app.route('/es/El-Campello-Historical', methods=['GET', 'POST'])
def El_Campello_Historical_es():

    # Load historical data
    with open('/data/his/El-Campello/El-Campello.pkl', 'rb') as f: 
        data = load(f)
    timelist = data.index

    if request.method == 'POST':

        # Get dates selected in calendar widgets
        start, end, uv = get_dates(request.form)

        ini, fin = start.replace('-', ''), end.replace('-', '')
    
        if 'submit' in request.form:

            # Address in-situ historical request
            data = new_request(request.form, 'es', 'Campello')

            for key, val in data.items():
                if isinstance(val, pd.Series):
                    data[key] = np.array(val)

            # Add whole time list for calendars
            data['timelist'] = timelist

            # Return template
            return render_template('El-Campello-Historical_es.html', **data,  
                date1=start, date2=end, date3=uv, csv='true')

        elif 'temp' in request.form:
            f = f'/data/CSV/csv-temp-{ini}-{fin}.csv'

        elif 'tur' in request.form:
            f = f'/data/CSV/csv-tur-{ini}-{fin}.csv'

        elif 'O2' in request.form:
            f = f'/data/CSV/csv-O2-{ini}-{fin}.csv'

        elif 'SWH' in request.form:
            f = f'/data/CSV/csv-swh-{ini}-{fin}.csv'

        elif 'wave' in request.form:
            f = f'/data/CSV/csv-wave-{ini}-{fin}.csv'

        elif 'wind' in request.form:
            f = f'/data/CSV/csv-wind-{ini}-{fin}.csv'

        elif 'currents' in request.form:
            f = f'/data/CSV/csv-currents-{ini}-{fin}.csv'

        return send_file(f, as_attachment=True)

    else:

        first, last = timelist[0].strftime('%Y-%m-%d'), timelist[-1].strftime('%Y-%m-%d')

        return render_template('El-Campello-Historical_es.html', timelist=timelist, 
            date1=first, date2=last, date3=last, csv='false')

''' Utilities '''
def new_request(form, language, boya):
    ''' This function addresses the in-situ historical requests '''

    start, end, uv = get_dates(form)

    if language == 'en':
        data = util.address_request(start, end, uv, boya)
    elif language == 'es':
        data = util.address_request(start, end, uv, boya, language='es')

    return data

def get_dates(form):
    ''' This function returns the dates selected in the calendar widgets '''

    start, end, uv = form.get('start-date'), form.get('end-date'), form.get('uv-date')

    t0, t1 = datetime.strptime(start, '%Y-%m-%d'), datetime.strptime(end, '%Y-%m-%d')
    if t0 > t1: 
        start, end = end, start

    return start, end, uv
