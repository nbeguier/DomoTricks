#!/usr/bin/python3
#-*- coding: utf-8 -*-
"""
DomoTricks: web server

Copyright (C) 2021 Nicolas Béguier

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# Standard library
import json

# Third party library imports
from flask import Flask, render_template
from requests import Session

# DomoTricks libraries
from lib.sqlite import SqliteCmd
import settings

# Debug
# from pdb import set_trace as st

BLACKLIST = [
    'Battery',
    'Dim level',
    'Id',
    'Level',
    'Sequence number',
    'Signal level',
    'Subtype',
    'Unitcode'
]

APP = Flask(__name__, template_folder='web/templates', static_folder='web/static')
SESSION = Session()

def get_weather():
    """
    Get weather via OpenWeatherMap API
    """
    weather = {
        'location': settings.LOCATION_NICKNAME,
        'description': ' - ',
        'humidity': ' - %',
        'temperature': ' - °C'
    }
    req = SESSION.get(f'https://api.openweathermap.org/data/2.5/weather?q={settings.LOCATION}&appid={settings.API_KEY}&lang={settings.LANG}&units=metric')
    if req.status_code != 200:
        return weather
    try:
        weather['description'] = json.loads(req.text)['weather'][0]['description']
        weather['humidity'] = f'{json.loads(req.text)["main"]["humidity"]} %'
        weather['temperature'] = f'{json.loads(req.text)["main"]["temp"]} °C'
    except:
        pass
    return weather

@APP.route('/')
def index():
    """ Display home page """
    conn = SqliteCmd(settings.DB_PATH)
    result = list()
    assets = conn.get_my_assets()
    for asset in assets:
        asset_key = asset[0]
        asset_type = asset[1]
        nickname = asset[2]
        asset_data = conn.get_asset(asset_key)
        if asset_data is None:
            continue
        # Take the last one
        asset_data = asset_data[-1]
        raw_metadata = json.loads(asset_data[3].replace("'", '"'))
        metadata = list()
        for meta in raw_metadata:
            if meta['key'] not in BLACKLIST:
                metadata.append(meta)
        result.append({
            'nickname': nickname,
            'type': asset_type,
            'timestamp': asset_data[0],
            'metadata': metadata
            })
    return render_template('homepage.html', assets=result, weather=get_weather())

@APP.route('/lost/')
def lost_assets():
    """ Display lost assets """
    conn = SqliteCmd(settings.DB_PATH)
    assets = conn.get_lost_assets()
    for i, _ in enumerate(assets):
        assets[i] = [x for x in assets[i]]
        try:
            assets[i][-1] = json.loads(assets[i][-1].replace("'", '"'))
        except:
            assets[i][-1] = [{'key': 'raw', 'value': assets[i][-1]}]
    return render_template('lost_assets.html', lost_assets=reversed(assets))

@APP.route('/my_assets/')
def my_assets():
    """ Display my assets """
    conn = SqliteCmd(settings.DB_PATH)
    assets = conn.get_my_assets()
    return render_template('my_assets.html', my_assets=assets)

@APP.route('/config/')
def configuration():
    """ Display configuration """
    return render_template('config.html')

@APP.errorhandler(404)
def page_not_found(_):
    """ Display error page """
    return render_template('404.html'), 404

if __name__ == '__main__':
    APP.run(debug=False, host='0.0.0.0', port=5000)
