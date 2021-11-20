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

__author__ = 'Nicolas Béguier'
__copyright__ = 'Copyright 2021, Nicolas Béguier'
__license__ = 'GPL'
__version__ = '1.0.2'
__maintainer__ = 'Nicolas Béguier'
__date__ = '$Date: 2021-06-01 15:00:00 +0100 (Tue, 1 Jun 2021) $'

# Standard library
from datetime import datetime, timedelta
import json
import re

# Third party library imports
from flask import Flask, render_template, request, send_from_directory
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
        asset_data = conn.get_asset(asset_key, last_only=True)
        if asset_data is None:
            continue
        raw_metadata = json.loads(asset_data[3].replace("'", '"'))
        metadata = list()
        for meta in raw_metadata:
            if meta['key'] not in BLACKLIST:
                metadata.append(meta)
        result.append({
            'key': asset_key,
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
    return render_template('lost_assets.html', lost_assets=assets)

@APP.route('/my_assets/')
def my_assets():
    """ Display my assets """
    conn = SqliteCmd(settings.DB_PATH)
    assets = conn.get_my_assets()
    return render_template('my_assets.html', my_assets=assets)

@APP.route('/my_assets/add/')
def add_my_assets():
    """ Add an asset """
    conn = SqliteCmd(settings.DB_PATH)
    asset_key = request.args.get('assetkey')
    if not re.match('[a-f0-9_]+', asset_key):
        return render_template('404.html'), 404
    packettype = request.args.get('packettype')
    conn.insert_my_asset(asset_key, packettype, '', '', asset_key)
    conn.delete_lost_asset(asset_key=asset_key)
    return my_assets()

@APP.route('/my_assets/delete/')
def delete_my_assets():
    """ Delete an asset """
    conn = SqliteCmd(settings.DB_PATH)
    asset_key = request.args.get('assetkey')
    if not re.match('[a-f0-9_]+', asset_key):
        return render_template('404.html'), 404
    conn.delete_my_asset(asset_key)
    return my_assets()

@APP.route('/my_assets/edit/')
def edit_my_assets():
    """ Edit an asset """
    conn = SqliteCmd(settings.DB_PATH)
    asset_key = request.args.get('assetkey')
    if not re.match('[a-f0-9_]+', asset_key):
        return render_template('404.html'), 404
    nickname = request.args.get('nickname')
    conn.update_my_asset_nickname(asset_key, nickname)
    return my_assets()

@APP.route('/asset/')
def asset():
    """ Display one assets """
    conn = SqliteCmd(settings.DB_PATH)
    asset_key = request.args.get('assetkey')
    if not re.match('[a-f0-9_]+', asset_key):
        return render_template('404.html'), 404
    nickname = conn.get_asset_nickname(asset_key)
    asset_data = conn.get_asset(asset_key)
    for i, _ in enumerate(asset_data):
        asset_data[i] = [x for x in asset_data[i]]
        try:
            asset_data[i][-1] = json.loads(asset_data[i][-1].replace("'", '"'))
        except:
            asset_data[i][-1] = [{'key': 'raw', 'value': asset_data[i][-1]}]
        raw_metadata = asset_data[i][-1].copy()
        for meta in raw_metadata:
            if meta['key'] in BLACKLIST:
                for k, _ in enumerate(asset_data[i][-1]):
                    if asset_data[i][-1][k]['key'] == meta['key']:
                        del asset_data[i][-1][k]
    return render_template('asset.html', asset=asset_data, nickname=nickname)

@APP.route('/asset.csv')
def asset_csv():
    """ return a CSV """
    result = 'date,value'
    conn = SqliteCmd(settings.DB_PATH)
    asset_key = request.args.get('assetkey')
    if not re.match('[a-f0-9_]+', asset_key):
        return render_template('404.html'), 404
    period = request.args.get('period')
    now = datetime.now()
    if period == 'hour':
        timestamp_min = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
    elif period == 'day':
        timestamp_min = (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
    elif period == 'week':
        timestamp_min = (now - timedelta(weeks=1)).strftime('%Y-%m-%d %H:%M')
    elif period == 'month':
        timestamp_min = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M')
    elif period == 'year':
        timestamp_min = (now - timedelta(days=365)).strftime('%Y-%m-%d %H:%M')
    else:
        return render_template('404.html'), 404
    interval = [timestamp_min, now]
    asset_data = conn.get_asset(asset_key, timestamp_interval=interval)
    for i, _ in enumerate(asset_data):
        asset_data[i] = [x for x in asset_data[i]]
        try:
            asset_data[i][-1] = json.loads(asset_data[i][-1].replace("'", '"'))
        except:
            asset_data[i][-1] = [{'key': 'raw', 'value': asset_data[i][-1]}]
        for meta in asset_data[i][-1]:
            if meta['key'] == 'Temperature':
                result += f'\n{asset_data[i][0]},{meta["value"]}'
    return result

@APP.route('/config/')
def configuration():
    """ Display configuration """
    conn = SqliteCmd(settings.DB_PATH)
    # result = {'device_alerting': [], ''}
    device_alerting = conn.get_device_alerting()
    for i, k in enumerate(device_alerting):
        device_alerting[i] = {
            'assetkey': k[0],
            'function': k[1],
            'nickname': conn.get_asset_nickname(k[0])}
    time_alerting = conn.get_time_alerting()
    for i, k in enumerate(time_alerting):
        time_alerting[i] = {
            'assetkey': k[0],
            'function': k[1].split(':')[0],
            'time': ':'.join(k[1].split(':')[1:]),
            'nickname': conn.get_asset_nickname(k[0])}
    config = {
        'GMAIL_USER': settings.GMAIL_USER,
        'MAIL_RECIPIENTS': settings.MAIL_RECIPIENTS,
        'DB_PATH': settings.DB_PATH,
        'HOLIDAY_ASSET_ID': settings.HOLIDAY_ASSET_ID,
        'LOCATION': settings.LOCATION,
        'LOCATION_NICKNAME': settings.LOCATION_NICKNAME,
        'LANG': settings.LANG
    }
    return render_template(
        'config.html',
        device_alerting=device_alerting,
        time_alerting=time_alerting,
        config=config)

@APP.route('/config/time_alerting')
def config_time_alerting():
    """ Edit time_alerting configuration """
    conn = SqliteCmd(settings.DB_PATH)
    asset_key_old = request.args.get('assetkey_old')
    asset_key_new = request.args.get('assetkey_new')
    if not re.match('[a-f0-9_]+', asset_key_old) or not re.match('[a-f0-9_]+', asset_key_new):
        return render_template('404.html'), 404
    conn.update_timealerting_asssetkey(asset_key_old, asset_key_new)
    return configuration()

@APP.errorhandler(404)
def page_not_found(_):
    """ Display error page """
    return render_template('404.html'), 404

@APP.route('/favicon.png')
def favicon():
    return send_from_directory('web/static/images',
        'favicon.png', mimetype='image/png')

if __name__ == '__main__':
    APP.run(debug=False, host='0.0.0.0', port=5000)
