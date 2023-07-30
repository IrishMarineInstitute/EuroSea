from flask import render_template, request, url_for, redirect, send_file
from datetime import datetime, timedelta
from email.message import EmailMessage
from pickle import load, dump
from app import app
import to_csv
import smtplib
import shutil
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

@app.route('/Galway-Bay', methods=['GET', 'POST'])
def galway():

    data = dataload('/data/pkl/GALWAY.pkl', {})
    data = dataload('galway-coastline.pkl', data)

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
        elif 'HELPDESK_ES' in request.form:
            return redirect(url_for('helpdesk_es'))
        elif 'Campello ISO ES' in request.form:
            return redirect(url_for('CISO_es'))
        elif 'QUESTIONNAIRES' in request.form:
            return redirect(url_for('questionnaires'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('home.html')

@app.route('/es', methods=['GET', 'POST'])
def home_es():
    if request.method == 'POST':
        if 'Deenish ISO' in request.form:
            return redirect(url_for('DISO'))
        elif 'Campello ISO ES' in request.form:
            return redirect(url_for('CISO_es'))
        elif 'Deenish RSO' in request.form:
            return redirect(url_for('DRSO'))
        elif 'Campello RSO' in request.form:
            return redirect(url_for('CRSO_es'))
        elif 'Deenish ISH' in request.form:
            return redirect(url_for('DISH'))
        elif 'Campello ISH' in request.form:
            return redirect(url_for('CISH_es'))
        elif 'Deenish RSH' in request.form:
            return redirect(url_for('DRSH'))
        elif 'HELPDESK_ES' in request.form:
            return redirect(url_for('helpdesk_es'))
        elif 'CUESTIONARIOS' in request.form:
            return redirect(url_for('cuestionarios'))
        else:
            return render_template('notexist.html')
    else:
        return render_template('home_es.html')

@app.route('/helpdesk', methods=['GET', 'POST'])
def helpdesk():
    if request.method == 'POST':

       if 'submit' in request.form:

           # Get sender's email and message
           email, message = request.form['email'], request.form['query']

           # Send email to service desk
           send_email_gmail(email, message, ['eurosea.helpdesk@marine.ie'] )

           return render_template('helpdesk.html', sent='true') 

    else:
        return render_template('helpdesk.html', sent='false') 

@app.route('/es/helpdesk', methods=['GET', 'POST'])
def helpdesk_es():
    if request.method == 'POST':

       if 'submit' in request.form:

           # Get sender's email and message
           email, message = request.form['email'], request.form['query']

           # Send email to service desk
           send_email_gmail(email, message, ['eurosea.helpdesk@marine.ie'] )

           return render_template('helpdesk_es.html', sent='true') 

    else:
        return render_template('helpdesk_es.html', sent='false') 

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

@app.route('/El-Campello-in-situ', methods=['GET', 'POST'])
def CISO():

    # Load observations
    data = dataload('/data/pkl/BUOY-2.pkl', {})
    # Load forecasts
    data = dataload('/data/pkl/MODEL-2.pkl', data)

    if os.path.isfile('/data/IMG/ECMWF-FORECAST.png'):
        shutil.move('/data/IMG/ECMWF-FORECAST.png', '/app/app/static/ECMWF-FORECAST.png')

    if request.method == 'POST':

        if 'temp' in request.form:
            f = to_csv.to_csv(data, 'temp', language='en')
        elif 'tur' in request.form:
            f = to_csv.to_csv(data, 'tur', language='en')
        elif 'O2' in request.form:
            f = to_csv.to_csv(data, 'O2', language='en')
        elif 'SWH' in request.form:
            f = to_csv.to_csv_swh(data, 'en')
        elif 'wave-period-direction-series' in request.form:
            f = to_csv.to_csv_wave_rose(data, 'en')
        elif 'current-speed-direction-series' in request.form:
            f = to_csv.to_csv_currents_rose(data, 'en')
        elif 'current-profile' in request.form:
            f = to_csv.to_csv_current_profile(data, 'en')
        elif 'wind' in request.form:
            f = to_csv.to_csv_wind(data, 'en')
        return send_file(f, as_attachment=True)

    else:
        return render_template('CISO.html', **data) 

@app.route('/es/El-Campello-in-situ', methods=['GET', 'POST'])
def CISO_es():

    # Load observations
    data = dataload('/data/pkl/BUOY-2.pkl', {})
    # Load forecasts
    data = dataload('/data/pkl/MODEL-2.pkl', data)

    if os.path.isfile('/data/IMG/ECMWF-FORECAST.png'):
        shutil.move('/data/IMG/ECMWF-FORECAST.png', '/app/app/static/ECMWF-FORECAST.png')

    if request.method == 'POST':

        if 'temp' in request.form:
            f = to_csv.to_csv(data, 'temp')
        elif 'tur' in request.form:
            f = to_csv.to_csv(data, 'tur')
        elif 'O2' in request.form:
            f = to_csv.to_csv(data, 'O2')
        elif 'SWH' in request.form:
            f = to_csv.to_csv_swh(data, 'es')
        elif 'wave-period-direction-series' in request.form:
            f = to_csv.to_csv_wave_rose(data, 'es')
        elif 'current-speed-direction-series' in request.form:
            f = to_csv.to_csv_currents_rose(data, 'es')
        elif 'current-profile' in request.form:
            f = to_csv.to_csv_current_profile(data, 'es')
        elif 'wind' in request.form:
            f = to_csv.to_csv_wind(data, 'es')
        return send_file(f, as_attachment=True)

    else:
        return render_template('CISO_es.html', **data) 

@app.route('/Deenish-rs')
def DRSO():
    # Load remote sensing
    data = dataload('/data/pkl/SST.pkl', {})
    # Load IWBN
    data = dataload('/data/pkl/IWBN.pkl', data)
    # Load oceancolour 
    data = dataload('/data/pkl/CHL.pkl', data)

    return render_template('DRSO.html', **data) 

@app.route('/Campello-rs')
def CRSO():
    # Load remote sensing
    data = dataload('/data/pkl/WAVES.pkl', {})

    return render_template('CRSO.html', **data)
    
@app.route('/es/Campello-rs')
def CRSO_es():
    # Load remote sensing
    data = dataload('/data/pkl/WAVES.pkl', {})

    return render_template('CRSO_es.html', **data)
    
@app.route('/El-Campello-in-situ-historical', methods=['GET', 'POST'])
def CISH():

    # Load historical data
    with open('/data/HISTORY/El-Campello-in-situ/El-Campello-in-situ.pkl', 'rb') as f: 
        data = load(f); timelist = data['time'][:-144]

    if request.method == 'POST':

        # Get dates selected in calendar widgets
        start, end, uv = get_dates(request.form)

        ini, fin = start.replace('-', ''), end.replace('-', '')
    
        if 'submit' in request.form:

            # Address in-situ historical request
            data = new_request(request.form, 'en')

            # Add whole time list for calendars
            data['timelist'] = timelist

            # Return template
            return render_template('CISH.html', **data,  
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

        elif 'ADCP' in request.form:
            f = f'/data/CSV/csv-ADCP-{ini}-{fin}.csv'

        return send_file(f, as_attachment=True)

    else:

        first, last = timelist[0].strftime('%Y-%m-%d'), timelist[-1].strftime('%Y-%m-%d')

        return render_template('CISH.html', timelist=timelist, 
            date1=first, date2=last, date3=last, csv='false')

@app.route('/es/El-Campello-in-situ-historical', methods=['GET', 'POST'])
def CISH_es():

    # Load historical data
    with open('/data/HISTORY/El-Campello-in-situ/El-Campello-in-situ.pkl', 'rb') as f: 
        data = load(f); timelist = data['time'][:-144]

    if request.method == 'POST':

        # Get dates selected in calendar widgets
        start, end, uv = get_dates(request.form)

        ini, fin = start.replace('-', ''), end.replace('-', '')
    
        if 'submit' in request.form:

            # Address in-situ historical request
            data = new_request(request.form, 'es')

            # Add whole time list for calendars
            data['timelist'] = timelist

            # Return template
            return render_template('CISH_es.html', **data,  
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

        elif 'ADCP' in request.form:
            f = f'/data/CSV/csv-ADCP-{ini}-{fin}.csv'

        return send_file(f, as_attachment=True)

    else:

        first, last = timelist[0].strftime('%Y-%m-%d'), timelist[-1].strftime('%Y-%m-%d')

        return render_template('CISH_es.html', timelist=timelist, 
            date1=first, date2=last, date3=last, csv='false')

def new_request(form, language):
    ''' This function addresses the in-situ historical requests '''

    start, end, uv = get_dates(form)

    if language == 'en':
        data = util.address_request(start, end, uv)
    elif language == 'es':
        data = util.address_request(start, end, uv, language='es')

    return data

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
    msg['Subject'] = 'FROM: ' + subject
    msg['From'] = 'eurosea.helpdesk@gmail.com'
    msg['To'] = destination
    server.send_message(msg)

@app.route('/questionnaires', methods=['GET', 'POST'])
def questionnaires():
    if request.method == 'POST':

       if 'submit' in request.form:
 
           if not os.path.isdir('/data/QUESTIONNAIRES'):
               os.mkdir('/data/QUESTIONNAIRES')

           now = datetime.now().strftime('%Y%m%dT%H%M%S')

           filename = f'/data/QUESTIONNAIRES/QUESTIONNAIRE-{now}.pkl'  

           with open(filename, 'wb') as f:
               dump(request.form, f)

           # Write message
           mensaje = respuestas_cuestionario(request.form, now, 'en')

           # Get sender's email and message
           email, message = 'QUESTIONNAIRE', mensaje

           # Send email to service desk
           send_email_gmail(email, message, ['eurosea.helpdesk@marine.ie',
                                             'martha.dunbar@csic.es'] )

           return render_template('questionnaires.html', sent='true') 

    else:
        return render_template('questionnaires.html', sent='false') 

@app.route('/cuestionarios', methods=['GET', 'POST'])
def cuestionarios():
    if request.method == 'POST':

       if 'submit' in request.form:
 
           if not os.path.isdir('/data/QUESTIONNAIRES'):
               os.mkdir('/data/QUESTIONNAIRES')

           now = datetime.now().strftime('%Y%m%dT%H%M%S')

           filename = f'/data/QUESTIONNAIRES/QUESTIONNAIRE-{now}.pkl'  

           with open(filename, 'wb') as f:
               dump(request.form, f)

           # Write message
           mensaje = respuestas_cuestionario(request.form, now, 'es')

           # Get sender's email and message
           email, message = 'CUESTIONARIO', mensaje

           # Send email to service desk
           send_email_gmail(email, message, ['eurosea.helpdesk@marine.ie',
                                             'martha.dunbar@csic.es'] )

           return render_template('cuestionarios.html', sent='true') 

    else:
        return render_template('cuestionarios.html', sent='false') 

def respuestas_cuestionario(form, date, language):
    ''' This function writes a text message from the 
        answers in a questionnaire. '''

    if language == 'es':
        text = f'CUESTIONARIO PORTAL EUROSEA ENVIADO A FECHA {date}\n\n' 
    elif language == 'en':
        text = f'EUROSEA PORTAL QUESTIONNAIRE SENT ON {date}\n\n'

    for item in form.items():
        line = item[0] + ' ' + item[1] + '\n\n'
        text += line
        
    return text
