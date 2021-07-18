#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DomoTricks: Alerting functions

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
import datetime
import json
import smtplib
import sys

# DomoTricks libraries
sys.path.append('..')
from lib.sqlite import SqliteCmd
import settings

# Debug
# from pdb import set_trace as st

def get_metadata_value(metadata, key):
    """
    Return a the metadata key value
    """
    for meta in metadata:
        if meta['key'] == key:
            return meta['value']
    return None

def send_mail(sent_to, subject, body):
    """
    Send a mail
    """
    print(f'Send mail: {sent_to} {subject} {body}')
    sent_from = settings.GMAIL_USER
    email_text = f"""\
From: {sent_from}
To: {", ".join(sent_to)}
Subject: {subject}

{body}
"""
    server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server_ssl.ehlo()
    server_ssl.login(settings.GMAIL_USER, settings.GMAIL_PASSWORD)
    server_ssl.sendmail(sent_from, sent_to, email_text.encode())

def debug(nickname, metadata):
    """
    Debug function
    """
    print(nickname, metadata)

def humidity_10(nickname, metadata):
    """
    Send mail if humidity is below 10%
    """
    humidity = get_metadata_value(metadata, 'Humidity')
    if humidity is not None and int(humidity) <= 10:
        send_mail(
            settings.MAIL_RECIPIENTS,
            f'[DT] {nickname} humidity',
            f'Humidity is at {humidity}%, below 10%')

def report_temperature(nickname, _, hours=12):
    """
    Send mail to report last hours temperatures
    """
    conn = SqliteCmd(settings.DB_PATH)
    asset_key = conn.get_asset_key(nickname)
    if asset_key is None:
        return
    asset_key = asset_key[0]
    asset_data = conn.get_asset(asset_key)
    if asset_data is None:
        return
    max_temperature = -256
    min_temperature = 256
    now = datetime.datetime.now()
    limit_time = now - datetime.timedelta(hours=hours)
    for i in range(len(asset_data)):
        timestamp = datetime.datetime.strptime(asset_data[i][0], '%Y-%m-%d %H:%M:%S')
        if timestamp < limit_time:
            break
        temperature = get_metadata_value(
            json.loads(asset_data[i][3].replace("'", '"')),
            'Temperature')
        if temperature is None:
            continue
        temperature = float('{:.2f}'.format(float(temperature)))
        if temperature < min_temperature:
            min_temperature = temperature
        if temperature > max_temperature:
            max_temperature = temperature
    send_mail(
        settings.MAIL_RECIPIENTS,
        f'[DT] {nickname} {min_temperature}°C to {max_temperature}°C',
        f'''Report of the past {hours}h temperatures in {nickname}.
Between {limit_time} and {now}, the temperature was between {min_temperature}°C and {max_temperature}°C''')

def door_during_holidays(nickname, metadata):
    """
    Send mail if door open during holidays
    """
    conn = SqliteCmd(settings.DB_PATH)
    is_door_open = get_metadata_value(metadata, 'Command') == 'On'
    # Holidays mode
    holidays_data = conn.get_asset(settings.HOLIDAY_ASSET_ID)
    if holidays_data is None:
        return
    holidays_metadata = json.loads(holidays_data[0][3].replace("'", '"'))
    is_holidays = get_metadata_value(holidays_metadata, 'Command') == 'On'
    if is_holidays and is_door_open:
        send_mail(
            settings.MAIL_RECIPIENTS,
            f'[DT] {nickname} open during holidays',
            f'At {datetime.datetime.now()} the door "{nickname}" is open.')

def holidays_switching(_, metadata):
    """
    Send mail if holidays is switching
    """
    command = get_metadata_value(metadata, 'Command')
    if command is None:
        return
    send_mail(
        settings.MAIL_RECIPIENTS,
        f'[DT] Holidays mode is {command}',
        f'At {datetime.datetime.now()} the holidays mode is set to {command}.')
