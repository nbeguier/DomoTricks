#!/usr/bin/python3
#-*- coding: utf-8 -*-
"""
DomoTricks: log aggregator

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
__version__ = '1.0.3'
__maintainer__ = 'Nicolas Béguier'
__date__ = '$Date: 2021-12-20 15:00:00 +0100 (Tue, 1 Jun 2021) $'

# Standard library
import json
from datetime import datetime, timedelta

# DomoTricks libraries
from lib.sqlite import SqliteCmd
import settings

# Debug
# from pdb import set_trace as st

def aggregate_log_per_hour():
    """
    After one day, logs are aggregated per hour
    """
    print('> aggregate_log_per_hour')
    conn = SqliteCmd(settings.DB_PATH)
    assets = conn.get_my_assets()
    now = datetime.now()
    for asset in assets:
        assetkey = asset[0]
        print(f'Asset: {assetkey}')
        # Aggregate 90 last days
        for d in range(90):
            for h in range(24):
                aggregated_date = (now - timedelta(days=d+1)).strftime('%Y-%m-%d')
                interval = [aggregated_date+f' {h:02}:00', aggregated_date+f' {h+1:02}:00']
                datas = conn.get_asset(assetkey, timestamp_interval=interval)
                # Skip empty or already aggregated datas
                if len(datas) <= 1:
                    continue
                temp_sum = 0
                temp_count = 0
                humidity_sum = 0
                humidity_count = 0
                for entry in datas:
                    meta = json.loads(entry[-1].replace("'", '"'))
                    for m in meta:
                        if m['key'] == 'Temperature':
                            temp_sum += float(m['value'])
                            temp_count += 1
                        elif m['key'] == 'Humidity':
                            humidity_sum += float(m['value'])
                            humidity_count += 1
                if temp_count > 0 or humidity_count > 0:
                    duplicate_meta = meta.copy()
                    for i, m in enumerate(meta):
                        if m['key'] == 'Temperature' and temp_count > 0:
                            duplicate_meta[i]['value'] = temp_sum / temp_count
                        elif m['key'] == 'Humidity' and humidity_count > 0:
                            duplicate_meta[i]['value'] = humidity_sum / humidity_count
                    if not conn.delete_asset_log(assetkey, timestamp_interval=interval):
                        print(f'Error deleting asset {assetkey} logs...')
                        continue
                    print(f'Aggregating {assetkey} at {aggregated_date} {h:02}:00')
                    conn.insert_asset(f'asset_{assetkey}', aggregated_date+f' {h:02}:00:01', datas[-1][1], datas[-1][2], '', '', str(duplicate_meta))

def remove_old_lost_assets():
    """
    Remove lost assets after a week without updates
    """
    print('> remove_old_lost_assets')
    now = datetime.now()
    timestamp = (now - timedelta(weeks=1)).strftime('%Y-%m-%d')
    print(f'Remove all before {timestamp}')
    conn = SqliteCmd(settings.DB_PATH)
    conn.delete_lost_asset(timestamp=timestamp)

if __name__ == '__main__':
    aggregate_log_per_hour()
    remove_old_lost_assets()
