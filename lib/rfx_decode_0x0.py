#!/usr/bin/env python3
# coding=UTF-8
"""
DomoTricks: Decoding 0x0. protocols

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

# Standard library
from string import whitespace

# DomoTricks libraries
import lib.rfx_sensors
from lib.rfx_utils import ByteToHex, testBit

RFX = lib.rfx_sensors.rfx_data()


def decode_0x01(message):
    """
    0x01 - Interface Message
    """

    data = {
        'packetlen' : ByteToHex(message[0]),
        'packettype' : ByteToHex(message[1]),
        'subtype' : ByteToHex(message[2]),
        'seqnbr' : ByteToHex(message[3]),
        'cmnd' : ByteToHex(message[4]),
        'msg1' : ByteToHex(message[5]),
        'msg2' : ByteToHex(message[6]),
        'msg3' : ByteToHex(message[7]),
        'msg4' : ByteToHex(message[8]),
        'msg5' : ByteToHex(message[9]),
        'msg6' : ByteToHex(message[10]),
        'msg7' : ByteToHex(message[11]),
        'msg8' : ByteToHex(message[12]),
        'msg9' : ByteToHex(message[13])
    }

    result = list()

    # Subtype
    if data['subtype'] == '00':
        result.append({'key': 'Subtype', 'value': 'Interface response'})
    else:
        result.append({'key': 'Subtype', 'value': 'Unknown type (' + data['packettype'] + ')'})

    # Seq
    result.append({'key': 'Sequence number', 'value': data['seqnbr']})

    # Command
    try:
        result.append({'key': 'Response on command', 'value': RFX.rfx_cmnd[data['cmnd']]})
    except KeyError:
        result.append({'key': 'Response on command', 'value': 'Invalid'})

    # MSG 1
    try:
        result.append({'key': 'Transceiver type', 'value': RFX.rfx_subtype_01_msg1[data['msg1']]})
    except KeyError:
        result.append({'key': 'Transceiver type', 'value': 'Invalid'})

    # MSG 2
    result.append({'key': 'Firmware version', 'value': int(data['msg2'], 16)})

    protocols = list()

    # ------------------------------------------------------
    # MSG 3

    protocols.append({
        'key': RFX.rfx_subtype_01_msg3['128'],
        'value': bool(testBit(int(data['msg3'], 16), 7) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg3['64'],
        'value': bool(testBit(int(data['msg3'], 16), 6) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg3['32'],
        'value': bool(testBit(int(data['msg3'], 16), 5) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg3['16'],
        'value': bool(testBit(int(data['msg3'], 16), 4) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg3['8'],
        'value': bool(testBit(int(data['msg3'], 16), 3) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg3['4'],
        'value': bool(testBit(int(data['msg3'], 16), 2) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg3['2'],
        'value': bool(testBit(int(data['msg3'], 16), 1) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg3['1'],
        'value': bool(testBit(int(data['msg3'], 16), 0) == 128)})

    # # ------------------------------------------------------
    # # MSG 4

    protocols.append({
        'key': RFX.rfx_subtype_01_msg4['128'],
        'value': bool(testBit(int(data['msg4'], 16), 7) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg4['64'],
        'value': bool(testBit(int(data['msg4'], 16), 6) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg4['32'],
        'value': bool(testBit(int(data['msg4'], 16), 5) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg4['16'],
        'value': bool(testBit(int(data['msg4'], 16), 4) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg4['8'],
        'value': bool(testBit(int(data['msg4'], 16), 3) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg4['4'],
        'value': bool(testBit(int(data['msg4'], 16), 2) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg4['2'],
        'value': bool(testBit(int(data['msg4'], 16), 1) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg4['1'],
        'value': bool(testBit(int(data['msg4'], 16), 0) == 128)})

    # # ------------------------------------------------------
    # # MSG 5

    protocols.append({
        'key': RFX.rfx_subtype_01_msg5['128'],
        'value': bool(testBit(int(data['msg5'], 16), 7) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg5['64'],
        'value': bool(testBit(int(data['msg5'], 16), 6) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg5['32'],
        'value': bool(testBit(int(data['msg5'], 16), 5) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg5['16'],
        'value': bool(testBit(int(data['msg5'], 16), 4) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg5['8'],
        'value': bool(testBit(int(data['msg5'], 16), 3) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg5['4'],
        'value': bool(testBit(int(data['msg5'], 16), 2) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg5['2'],
        'value': bool(testBit(int(data['msg5'], 16), 1) == 128)})
    protocols.append({
        'key': RFX.rfx_subtype_01_msg5['1'],
        'value': bool(testBit(int(data['msg5'], 16), 0) == 128)})

    result.append({'key': 'Protocols', 'value': protocols})

    return result, dict()

# ----------------------------------------------------------------------------

def decode_0x02(subtype, seqnbr, id1):
    """
    0x02 - Receiver/Transmitter Message
    """

    result = list()

    result.append({'key': 'Subtype', 'value': RFX.rfx_subtype_02[subtype]})
    result.append({'key': 'Sequence number', 'value': seqnbr})

    if subtype == '01':
        result.append({'key': 'Message', 'value': RFX.rfx_subtype_02_msg1[id1]})

    if subtype == '00':
        output_extra = []
    else:
        output_extra = [('id1', id1)]

    return result, output_extra


def decode_0x03(message, subtype, seqnbr):
    """
    0x03 - Undecoded Message
    """

    result = list()

    result.append({'key': 'Subtype', 'value': RFX.rfx_subtype_03[subtype]})
    result.append({'key': 'Sequence number', 'value': seqnbr})

    indata = ByteToHex(message)
    # remove all spaces
    for i in whitespace:
        indata = indata.replace(i, "")
    indata = indata[4:]
    result.append({'key': 'Message', 'value': indata})

    return result, [('message', indata)]
