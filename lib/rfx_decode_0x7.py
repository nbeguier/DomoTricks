#!/usr/bin/env python3
# coding=UTF-8
"""
DomoTricks: Decoding 0x7. protocols

Based on Nicolas Béguier work https://github.com/nbeguier/rfxcmd
Copyright 2018-2023 by Nicolas BEGUIER, nicolas_beguier@hotmail.com

Copyright 2021-2023 Nicolas Béguier

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
from lib.rfx_utils import ByteToHex
import lib.rfx_decode as rfxdecode

RFX = lib.rfx_sensors.rfx_data()

def decode_0x70(message, subtype, seqnbr, id1):
    """
    0x70 RFXsensor
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_70[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    result.append({'key': 'Id', 'value': id1})

    temperature = 0
    if subtype == '00':
        temperature = float(rfxdecode.decode_temperature(message[5], message[6]))
        temperature = temperature * 0.1
    result.append({'key': 'Temperature', 'value': temperature, 'unit': 'C'})

    voltage = 0
    if subtype == '01' or subtype == '02':
        voltage_hi = int(ByteToHex(message[5]), 16) * 256
        voltage_lo = int(ByteToHex(message[6]), 16)
        voltage = voltage_hi + voltage_lo
    result.append({'key': 'Voltage', 'value': voltage, 'unit': 'mV'})

    sensor_message = '0x' + message[6]
    if subtype == '03':
        try:
            sensor_message = RFX.rfx_subtype_70_msg03[message[6]]
        except KeyError:
            sensor_message = '0x' + message[6]
    result.append({'key': 'Message', 'value': sensor_message})

    signal = rfxdecode.decode_signal(message[7])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('signal_level', signal),
        ('id', id1),
        ('message', message),
        ('temperature', temperature),
        ('voltage', voltage)]

    return result, output_extra


def decode_0x71(message, subtype, seqnbr, id1, id2):
    """
    0x71 RFXmeter
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_71[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    sensor_power = rfxdecode.decode_power(message[7], message[8], message[9])
    result.append({'key': 'Power', 'value': sensor_power})

    output_extra = [
        ('id', sensor_id),
        ('power', sensor_power)]

    return result, output_extra


def decode_0x72(subtype, seqnbr):
    """
    0x72 FS20
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_72[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []
