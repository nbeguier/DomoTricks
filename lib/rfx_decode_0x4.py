#!/usr/bin/env python3
# coding=UTF-8
"""
DomoTricks: Decoding 0x4. protocols

Based on Nicolas Béguier work https://github.com/nbeguier/rfxcmd
Copyright 2018-2022 by Nicolas BEGUIER, nicolas_beguier@hotmail.com

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

# DomoTricks libraries
import lib.rfx_sensors
from lib.rfx_utils import ByteToHex, testBit
import lib.rfx_decode as rfxdecode

RFX = lib.rfx_sensors.rfx_data()

def decode_0x40(message, subtype, seqnbr, id1, id2):
    """
    0x40 - Thermostat1
    Credit: Jean-François Pucheu
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_40[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    temperature = int(ByteToHex(message[6]), 16)
    result.append({'key': 'Temperature', 'value': temperature, 'unit': 'C'})

    temperature_set = int(ByteToHex(message[7]), 16)
    result.append({'key': 'Temperature set', 'value': temperature_set, 'unit': 'C'})

    status_hex = str(testBit(int(ByteToHex(message[8]), 16), 0) + \
                     testBit(int(ByteToHex(message[8]), 16), 1))
    try:
        status = RFX.rfx_subtype_40_status[status_hex]
    except KeyError:
        status = '0x' + status_hex
    result.append({'key': 'Status', 'value': status})

    if testBit(int(ByteToHex(message[8]), 16), 7) == 128:
        mode = RFX.rfx_subtype_40_mode['1']
    else:
        mode = RFX.rfx_subtype_40_mode['0']
    result.append({'key': 'Mode', 'value': mode})

    signal = rfxdecode.decode_signal(message[9])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('signal_level', signal),
        ('mode', mode),
        ('id', sensor_id),
        ('status', status),
        ('temperature_set', temperature_set),
        ('temperature', temperature)]

    return result, output_extra


def decode_0x41(subtype, seqnbr):
    """
    0x41 Thermostat2
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_41[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []


def decode_0x42(message, subtype, seqnbr, id1, id2):
    """
    0x40 - Thermostat1
    Credit: Jean-François Pucheu
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_42[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    command_hex = ByteToHex(message[7])
    try:
        if subtype == '00':
            unitcode = ByteToHex(message[4])
            command = RFX.rfx_subtype_42_cmd00[command_hex]
        elif subtype == '01':
            unitcode = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6])
            command = RFX.rfx_subtype_42_cmd01[command_hex]
        else:
            unitcode = '00'
            command = '0x' + command_hex
    except KeyError:
        command = '0x' + command_hex

    result.append({'key': 'Unitcode', 'value': unitcode})
    result.append({'key': 'Command', 'value': command})

    signal = rfxdecode.decode_signal(message[8])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('signal_level', signal),
        ('id', sensor_id),
        ('unitcode', unitcode),
        ('command', command)]

    return result, output_extra
