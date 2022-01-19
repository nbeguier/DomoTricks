#!/usr/bin/env python3
"""
DomoTricks: Time alerting, should be use in CRON (or any other scheduler)

Copyright 2021-2022 Nicolas Béguier

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
from datetime import datetime
import json

# DomoTricks libraries
import alerting
from lib.sqlite import SqliteCmd
import settings

# Debug
# from pdb import set_trace as st

def main():
    """
    Main function
    """
    # TODO
    conn = SqliteCmd(settings.DB_PATH)
    assets = conn.get_time_alerting()
    hour_now = datetime.now().hour
    minute_now = datetime.now().minute
    for asset in assets:
        assetkey = asset[0]
        functions = asset[1]
        print(f'Asset: {assetkey}, functions: {functions}')
        for function in functions.split('|'):
            if len(function.split(':')) != 3:
                print(f'Alerting function "{function}" is malformed...')
                continue
            function_name = function.split(':')[0]
            hour = int(function.split(':')[1])
            minute = int(function.split(':')[2])
            if not hasattr(alerting, function_name):
                print(f'Alerting function "{function_name}" does not exist...')
                continue
            if hour != hour_now or minute != minute_now:
                continue
            nickname = conn.get_asset_nickname(assetkey)
            print( f'Trigger alerting function "{function_name}" for {nickname}')
            asset_data = conn.get_asset(assetkey)
            if asset_data is None:
                print(f'Asset "{nickname}" ({assetkey}) is empty...')
                continue
            # Apply function on the most recent element (0) metadata (3)
            metadata = json.loads(asset_data[0][3].replace("'", '"'))
            getattr(alerting, function_name)(nickname, metadata)

if __name__ == '__main__':
    main()
