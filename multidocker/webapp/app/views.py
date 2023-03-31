from flask import render_template, request, url_for, redirect, send_file
from datetime import datetime
from pickle import load
from glob import glob
from app import app
import to_csv_func
import to_csv_func_2
import smtplib
from email.message import EmailMessage
import os
import rs
import util
import util_2

def dataload(pkl, dic):
    ''' Load data from container. Update dictionary '''
    try:
        with open(pkl, 'rb') as f:
            var = load(f)
    except FileNotFoundError:
        var = {}
    return {**dic, **var}

@app.route('/Galway-Bay', methods=['GET', 'POST'])
def galway():

    data = dataload('/data/pkl/GALWAY.pkl', {})
    data = dataload('galway-coastline.pkl', data)

    if request.method == 'POST':

        # Clean data directory if needed to prevent accumulation of too many .csv files
        lista = glob('/data/*.csv')
        if len(lista) > 100: # Too many .csv files. Clean directory. 
            for file in lista:
                os.remove(file)

        for file in lista:
            os.remove(file)
        if 'temp' in request.form:
            f = to_csv_func.to_csv(data, 'temp')
        elif 'salt' in request.form:
            f = to_csv_func.to_csv(data, 'salt')
        return send_file(f, as_attachment=True)

    else:
        return render_template('galway.html', **data) 

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'Deenish ISO' in request.form:
            return redirect(url_for('DISO'))
        elif 'Campello ISO' in request.form:
            return redirect(url_for('CISO'))
        elif 'Deenish RSO' in request.form:
            return redirect(url_for('DRSO'))
        elif 'Campello RSO' in request.form:
            return redirect(url_for('CRSO'))
        elif 'Deenish ISH' in request.form:
            return redirect(url_for('DISH'))
        elif 'Campello ISH' in request.form:
            return redirect(url_for('CISH'))
        elif 'Deenish RSH' in request.form:
            return redirect(url_for('DRSH'))
        elif 'HELPDESK' in request.form:
            return redirect(url_for('helpdesk'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('home.html')

@app.route('/helpdesk', methods=['GET', 'POST'])
def helpdesk():
    if request.method == 'POST':

       if 'submit' in request.form:

           # Get sender's email and message
           email, message = request.form['email'], request.form['query']

           # Send email to service desk
           send_email_gmail(email, message, ['eurosea.helpdesk@gmail.com'] )

           return render_template('helpdesk.html', sent='true') 

    else:
        return render_template('helpdesk.html', sent='false') 

@app.route('/Deenish', methods=['GET', 'POST'])
def Deenish():
    if request.method == 'POST':
        if 'Deenish ISO' in request.form:
            return redirect(url_for('DISO'))
        elif 'Deenish RSO' in request.form:
            return redirect(url_for('DRSO'))
        elif 'Deenish ISH' in request.form:
            return redirect(url_for('DISH'))
        elif 'Deenish RSH' in request.form:
            return redirect(url_for('DRSH'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('Deenish.html')
        
@app.route('/Campello', methods=['GET', 'POST'])
def Campello():
    if request.method == 'POST':
        if 'Campello ISO' in request.form:
            return redirect(url_for('CISO'))
        elif 'Campello ISH' in request.form:
            return redirect(url_for('CISH'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('Campello.html')

@app.route('/Deenish-in-situ', methods=['GET', 'POST'])
def DISO():

    # Load observations
    data = dataload('/data/pkl/BUOY.pkl', {})
    # Load forecasts
    data = dataload('/data/pkl/MODEL.pkl', data)

    if request.method == 'POST':

        # Clean data directory if needed to prevent accumulation of too many .csv files
        lista = glob('/data/*.csv')
        if len(lista) > 100: # Too many .csv files. Clean directory. 
            for file in lista:
                os.remove(file)

        for file in lista:
            os.remove(file)
        if 'temp' in request.form:
            f = to_csv_func.to_csv(data, 'temp')
        elif 'profile' in request.form:
            f = to_csv_func.to_csv_profile(data) 
        elif 'salt' in request.form:
            f = to_csv_func.to_csv(data, 'salt')
        elif 'pH' in request.form:
            f = to_csv_func.to_csv(data, 'pH')
        elif 'O2' in request.form:
            f = to_csv_func.to_csv(data, 'O2')
        elif 'RFU' in request.form:
            f = to_csv_func.to_csv(data, 'RFU')
        elif 'uv-surf' in request.form or 'uv-mid' in request.form or 'uv-seab' in request.form:
            f = to_csv_func.to_csv_uv(data, request.form)
        return send_file(f, as_attachment=True)

    else:
        return render_template('DISO.html', **data) 

@app.route('/El-Campello-in-situ', methods=['GET', 'POST'])
def CISO():

    # Load observations
    data = dataload('/data/pkl/BUOY-2.pkl', {})
    # Load forecasts
    data = dataload('/data/pkl/MODEL-2.pkl', data)

    if request.method == 'POST':

        # Clean data directory if needed to prevent accumulation of too many .csv files
        lista = glob('/data/*.csv')
        if len(lista) > 100: # Too many .csv files. Clean directory. 
            for file in lista:
                os.remove(file)

        for file in lista:
            os.remove(file)
        if 'temp' in request.form:
            f = to_csv_func_2.to_csv(data, 'temp')
        elif 'tur' in request.form:
            f = to_csv_func_2.to_csv(data, 'tur')
        elif 'O2' in request.form:
            f = to_csv_func_2.to_csv(data, 'O2')
        elif 'SWH' in request.form:
            f = to_csv_func_2.to_csv_swh(data, 'en')
        elif 'wave-period-direction-series' in request.form:
            f = to_csv_func_2.to_csv_wave_rose(data, 'en')
        elif 'current-speed-direction-series' in request.form:
            f = to_csv_func_2.to_csv_currents_rose(data, 'en')
        elif 'current-profile' in request.form:
            f = to_csv_func_2.to_csv_current_profile(data, 'en')
        return send_file(f, as_attachment=True)

    else:
        #return render_template('CISO.html', **data, waves=zip(safe0, safe1)) 
        return render_template('CISO.html', **data) 

@app.route('/Deenish-rs')
def DRSO():
    # Load remote sensing
    data = dataload('/data/pkl/RS.pkl', {})
    # Load LPTM
    data = dataload('/data/pkl/LPTM.pkl', data)

    return render_template('DRSO.html', **data) 

@app.route('/Campello-rs')
def CRSO():
    # Load remote sensing
    data = dataload('/data/pkl/RS-2.pkl', {})

    return render_template('CRSO.html', **data)
    
    
@app.route('/Deenish-rs-historical', methods=['GET', 'POST'])
def DRSH():
    # Load historical data
    with open('/data/buoy.pkl', 'rb') as f: 
        data = load(f); timelist = data['time'][:-144]
    if request.method == 'POST':
        start = request.form.get('start-date')
        maps = rs.address_request(start)
        return render_template('DRSH.html', **maps,
            timelist=timelist, date=start, csv='true')
    else:
        last = timelist[-1].strftime('%Y-%m-%d')
        return render_template('DRSH.html', timelist=timelist, 
            date=last, csv='false')

@app.route('/Deenish-in-situ-historical', methods=['GET', 'POST'])
def DISH():

    # Load historical data
    with open('/data/buoy.pkl', 'rb') as f: 
        data = load(f); timelist = data['time'][:-144]

    if request.method == 'POST':

        # Clean data directory if needed to prevent accumulation of too many .csv files
        lista = glob('/data/*.csv')
        if len(lista) > 100: # Too many .csv files. Clean directory. 
            for file in lista:
                os.remove(file)

        # Get dates selected in calendar widgets
        start, end, uv = get_dates(request.form)

        ini, fin = start.replace('-', ''), end.replace('-', '')
    
        if 'submit' in request.form:

            # Address in-situ historical request
            data, mhw_times, mhw_temps = new_request(request.form)

            # Add whole time list for calendars
            data['timelist'] = timelist

            # Return template
            return render_template('DISH.html', **data, mhw=zip(mhw_times, mhw_temps), 
                date1=start, date2=end, date3=uv, csv='true')

        elif 'temp' in request.form:
            f = f'/data/csv-temp-{ini}-{fin}.csv'

        elif 'profile' in request.form:
            f = f'/data/csv-profile-{ini}-{fin}.csv'

        elif 'salt' in request.form:
            f = f'/data/csv-salt-{ini}-{fin}.csv'

        elif 'pH' in request.form:
            f = f'/data/csv-pH-{ini}-{fin}.csv'

        elif 'O2' in request.form:
            f = f'/data/csv-O2-{ini}-{fin}.csv'

        elif 'RFU' in request.form:
            f = f'/data/csv-RFU-{ini}-{fin}.csv'

        elif 'uv-surf' in request.form:
            f = f'/data/csv-uv-surf-{ini}-{fin}.csv'

        elif 'uv-mid' in request.form:
            f = f'/data/csv-uv-mid-{ini}-{fin}.csv'

        elif 'uv-seab' in request.form:
            f = f'/data/csv-uv-seab-{ini}-{fin}.csv'

        return send_file(f, as_attachment=True)

    else:

        first, last = timelist[0].strftime('%Y-%m-%d'), timelist[-1].strftime('%Y-%m-%d')

        return render_template('DISH.html', timelist=timelist, 
            date1=first, date2=last, date3=last, csv='false')

@app.route('/El-Campello-in-situ-historical', methods=['GET', 'POST'])
def CISH():

    # Load historical data
    with open('/data/buoy-2.pkl', 'rb') as f: 
        data = load(f); timelist = data['time'][:-144]

    if request.method == 'POST':

        # Clean data directory if needed to prevent accumulation of too many .csv files
        lista = glob('/data/*.csv')
        if len(lista) > 100: # Too many .csv files. Clean directory. 
            for file in lista:
                os.remove(file)

        # Get dates selected in calendar widgets
        start, end, uv = get_dates(request.form)

        ini, fin = start.replace('-', ''), end.replace('-', '')
    
        if 'submit' in request.form:

            # Address in-situ historical request
            data, mhw_times, mhw_temps = new_request_2(request.form)

            # Add whole time list for calendars
            data['timelist'] = timelist

            # Return template
            return render_template('CISH.html', **data, mhw=zip(mhw_times, mhw_temps), 
                date1=start, date2=end, date3=uv, csv='true')

        elif 'temp' in request.form:
            f = f'/data/csv-temp-{ini}-{fin}.csv'

        elif 'profile' in request.form:
            f = f'/data/csv-profile-{ini}-{fin}.csv'

        elif 'salt' in request.form:
            f = f'/data/csv-salt-{ini}-{fin}.csv'

        elif 'tur' in request.form:
            f = f'/data/csv-tur-{ini}-{fin}.csv'

        elif 'O2' in request.form:
            f = f'/data/csv-O2-{ini}-{fin}.csv'

        elif 'uv-surf' in request.form:
            f = f'/data/csv-uv-surf-{ini}-{fin}.csv'

        elif 'uv-mid' in request.form:
            f = f'/data/csv-uv-mid-{ini}-{fin}.csv'

        elif 'uv-seab' in request.form:
            f = f'/data/csv-uv-seab-{ini}-{fin}.csv'

        return send_file(f, as_attachment=True)

    else:

        first, last = timelist[0].strftime('%Y-%m-%d'), timelist[-1].strftime('%Y-%m-%d')

        return render_template('CISH.html', timelist=timelist, 
            date1=first, date2=last, date3=last, csv='false')

def new_request(form):
    ''' This function addresses the in-situ historical requests '''

    start, end, uv = get_dates(form)

    data, mhw_times, mhw_temps = util.address_request(start, end, uv)

    return data, mhw_times, mhw_temps

def new_request_2(form):
    ''' This function addresses the in-situ historical requests '''

    start, end, uv = get_dates(form)

    data, mhw_times, mhw_temps = util_2.address_request(start, end, uv)

    return data, mhw_times, mhw_temps

def get_dates(form):
    ''' This function returns the dates selected in the calendar widgets '''

    start, end, uv = form.get('start-date'), form.get('end-date'), form.get('uv-date')

    t0, t1 = datetime.strptime(start, '%Y-%m-%d'), datetime.strptime(end, '%Y-%m-%d')
    if t0 > t1: 
        start, end = end, start

    return start, end, uv

def send_email_gmail(subject, message, destination):
    ''' This function sends an email to the HelpDesk Service. '''
       

    server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()

    server.login('eurosea.helpdesk@gmail.com', 'vsyjmeqsxkcxzhxe')

    msg = EmailMessage()

    message = f'{message}\n'
    msg.set_content(message)
    msg['Subject'] = subject
    msg['From'] = 'eurosea.helpdesk@gmail.com'
    msg['To'] = destination
    server.send_message(msg)

def submit_query_to_helpdesk(form):
    ''' Collect feedback from users '''


    return
