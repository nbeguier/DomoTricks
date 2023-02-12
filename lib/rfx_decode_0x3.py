#!/usr/bin/env python3
# coding=UTF-8
"""
DomoTricks: Decoding 0x3. protocols

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

def decode_0x30(message, subtype, seqnbr, id1):
    """
    0x30 Remote control and IR
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_30[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    command_hex = ByteToHex(message[5])
    cmndtype_hex = ByteToHex(message[7])
    command = None
    cmndtype = None
    toggle = None
    if subtype == '00':
        try:
            command = RFX.rfx_subtype_30_atiremotewonder[command_hex]
        except KeyError:
            command = '0x' + command_hex
    elif subtype == '02':
        command = RFX.rfx_subtype_30_medion[command_hex]
    elif subtype == '04':
        if cmndtype_hex == '00':
            cmndtype = "PC"
        elif cmndtype_hex == '01':
            cmndtype = "AUX1"
        elif cmndtype_hex == '02':
            cmndtype = "AUX2"
        elif cmndtype_hex == '03':
            cmndtype = "AUX3"
        elif cmndtype_hex == '04':
            cmndtype = "AUX4"
        else:
            cmndtype = "Unknown"
        result.append({'key': 'Command type', 'value': cmndtype})
        toggle = ByteToHex(message[6])
        result.append({'key': 'Toggle', 'value': toggle})

    result.append({'key': 'Command', 'value': command})

    result.append({'key': 'Id', 'value': id1})

    signal = rfxdecode.decode_signal(message[6])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('signal_level', signal),
        ('id', id1),
        ('toggle', toggle),
        ('cmndtype', cmndtype),
        ('command', command)]

    return result, output_extra
