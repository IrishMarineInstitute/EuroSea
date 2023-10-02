''' 
    
(C) Copyright EuroSea H2020 project under Grant No. 862626. All rights reserved.

 Copyright notice
   --------------------------------------------------------------------
   Copyright (C) 2022 Marine Institute
       Diego Pereiro Rodriguez

       diego.pereiro@marine.ie

   This library is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this library.  If not, see <http://www.gnu.org/licenses/>.
   --------------------------------------------------------------------

'''

from telegram.constants import ParseMode
from datetime import datetime 
from log import set_logger, now
from pickle import load
import numpy as np
import requests
import telebot
import json

logger = set_logger()

def configuration():
    ''' Read secrets (configuration) file '''
    config = {}
    with open('config', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save as environment variable
            config[key] = val
    return config

def send_message(message, TOKEN, chat_id):
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url).json()

def telebots():

    # Read configuration options
    config = configuration()

    # Get Telegram Bot Token and Chat ID
    token, chat = config['token'], config['chat']

    # Start bot
    bot = telebot.TeleBot(token)

    # Get levels of orange and red warnings
    orange, red = float(config['orange']), float(config['red'])
                
    # Read wave forecast
    try:
        with open(config['forecast'], 'rb') as f:
            data = load(f)
        time, SWH = json.loads(data[config['time']]), np.array(json.loads(data[config['SWH']]))

        # Get maximum forecasted Significant Wave Height
        maximum, timemax = SWH.max(), time[np.argmax(SWH)]

    except Exception as e:
        logger.error(f'{now()} ERROR: Could not read wave forecast due to this error: {str(e)}')

    info = 'Altura de ola significante esperada de ' + '{0:.2f}'.format(maximum) + \
              f' m a {timemax}. '
 
    link = "[VER WEB](https://eurosea.marine.ie/es/El-Campello-in-situ#Wave-Height-Series"

    if maximum > red:
        message = u'\U0001F534 \U0001F534 \U0001F534' + \
          ' Alerta roja para El Campello por mala mar. ' + info + link

    elif maximum > orange:
        message = u'\U0001F7E0 \U0001F7E0 \U0001F7E0' + \
          ' Alerta naranja para El Campello por mala mar. ' + info + link

    elif maximum <= orange and datetime.now().hour == 10:
        message = u'\U0001F7E2 \U0001F7E2 \U0001F7E2' + \
          ' Buenas condiciones del mar en El Campello en los próximos cinco días. ' + info + link

    else:
         message = '' # Do not send any message

    # Send message to Telegram channel
    if message:
        try:
            bot.send_message(chat_id=chat, text=message ,parse_mode=ParseMode.MARKDOWN)
            logger.info(f'{now()} SUCCESS: Message {message} sent successfully.')
        except Exception as e:
            logger.error(f'{now()} ERROR: Could not send message due to this error: {str(e)}')

if __name__ == '__main__':
    telebots()
