#!/usr/bin/env python3
# coding=UTF-8
"""
DomoTricks: RFX433 reader

Based on Sebastian Sjoholm work https://github.com/ssjoholm/rfxcmd_gc
Copyright 2012-2014 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
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

__author__ = 'Nicolas Béguier'
__copyright__ = 'Copyright 2021-2023, Nicolas Béguier'
__license__ = 'GPL'
__version__ = '1.0.3'
__maintainer__ = 'Nicolas Béguier'
__date__ = '$Date: 2021-12-20 15:00:00 +0100 (Tue, 1 Jun 2021) $'

# Standard library
from codecs import decode as codecs_decode
from inspect import currentframe, getframeinfo
from json import dumps
import logging
from argparse import ArgumentParser
import os
from time import strftime, sleep
from traceback import format_exc
from signal import signal, SIGINT, SIGTERM
import sys
import xml.dom.minidom as minidom

# Third party library imports
from serial import Serial, VERSION, SerialException

# DomoTricks libraries
import alerting
from lib.rfx_socket import MESSAGEQUEUE, RFXcmdSocketAdapter
from lib.rfx_utils import stripped, ByteToHex
from lib.sqlite import SqliteCmd
import lib.rfx_sensors
import lib.rfx_decode_0x0 as rfxdecode0x0
import lib.rfx_decode_0x1 as rfxdecode0x1
import lib.rfx_decode_0x2 as rfxdecode0x2
import lib.rfx_decode_0x3 as rfxdecode0x3
import lib.rfx_decode_0x4 as rfxdecode0x4
import lib.rfx_decode_0x5 as rfxdecode0x5
import lib.rfx_decode_0x7 as rfxdecode0x7
import lib.rfx_protocols as protocol
import settings

# Debug
# from pdb import set_trace as st

# ------------------------------------------------------------------------------
# VARIABLE CLASSS
# ------------------------------------------------------------------------------

class ConfigData:
    """
    Configuration Data
    """
    def __init__(
            self,
            barometric=0,
            daemon_active=False,
            daemon_pidfile='rfxcmd.pid',
            device=None,
            log_msg=False,
            log_msgfile='',
            logfile='rfxcmd.log',
            loglevel='info',
            process_rfxmsg=True,
            program_path='',
            protocol_file='protocol.xml',
            protocol_startup=False,
            serial_active=True,
            serial_device=None,
            serial_rate=38400,
            serial_timeout=9,
            sockethost='',
            socketport='',
            socketserver=False,
            whitelist_active=False,
            whitelist_file='',
        ):

        self.barometric = barometric
        self.daemon_active = daemon_active
        self.daemon_pidfile = daemon_pidfile
        self.device = device
        self.log_msg = log_msg
        self.log_msgfile = log_msgfile
        self.logfile = logfile
        self.loglevel = loglevel
        self.process_rfxmsg = process_rfxmsg
        self.program_path = program_path
        self.protocol_file = protocol_file
        self.protocol_startup = protocol_startup
        self.serial_active = serial_active
        self.serial_device = serial_device
        self.serial_rate = serial_rate
        self.serial_timeout = serial_timeout
        self.sockethost = sockethost
        self.socketport = socketport
        self.socketserver = socketserver
        self.whitelist_active = whitelist_active
        self.whitelist_file = whitelist_file

class CmdArgData:
    """
    Command Argument Data
    """
    def __init__(
            self,
            action='',
            configfile='',
            createpid=False,
            device='',
            pidfile='',
            printout_complete=False,
            printout_csv=False,
            printout_debug=False,
            rawcmd='',
        ):
        self.action = action
        self.configfile = configfile
        self.createpid = createpid
        self.device = device
        self.pidfile = pidfile
        self.printout_complete = printout_complete
        self.printout_csv = printout_csv
        self.printout_debug = printout_debug
        self.rawcmd = rawcmd

class RfxCmdData:
    """
    RFX Command Data
    """
    def __init__(
            self,
            reset='0d00000000000000000000000000',
            save='0d00000006000000000000000000',
            status='0d00000002000000000000000000',
        ):
        self.reset = reset
        self.save = save
        self.status = status

class SerialData:
    """
    Serial Data
    """
    def __init__(
            self,
            port=None,
            rate=38400,
            timeout=9
        ):
        self.port = port
        self.rate = rate
        self.timeout = timeout

class WhitelistData:
    """
    Store the whitelist data from xml file
    """
    def __init__(
            self,
            data=''
        ):
        self.data = data

# ----------------------------------------------------------------------------
# DEAMONIZE
# Credit: George Henze
# ----------------------------------------------------------------------------

def shutdown():
    """
    Shutdown function
    """
    # clean up PID file after us
    log_me('debug', 'Shutdown')

    if CMDARG.createpid:
        log_me('debug', 'Removing PID file ' + str(CMDARG.pidfile))
        os.remove(CMDARG.pidfile)

    if SERIAL_PARAM.port is not None:
        log_me('debug', 'Close serial port')
        SERIAL_PARAM.port.close()
        SERIAL_PARAM.port = None

    log_me('debug', 'Exit 0')
    sys.stdout.flush()
    # pylint: disable=protected-access
    os._exit(0)

# pylint: disable=unused-argument
def handler(signum=None, frame=None):
    """
    Handler, signum & frame are used
    """
    if not isinstance(signum, type(None)):
        log_me('debug', 'Signal %i caught, exiting...' % int(signum))
        shutdown()

def daemonize():
    """
    Daemonize
    """
    try:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
    except OSError as err:
        raise RuntimeError('1st fork failed: %s [%d]' % (err.strerror, err.errno)) from err

    os.setsid()

    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    try:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
    except OSError as err:
        raise RuntimeError('2nd fork failed: %s [%d]' % (err.strerror, err.errno)) from err

    if CMDARG.createpid:
        pid = str(os.getpid())
        log_me('debug', 'Writing PID ' + pid + ' to ' + str(CMDARG.pidfile))
        pid_file = open(CMDARG.pidfile, 'w')
        pid_file.write('%s\n' % pid)
        pid_file.close()

# ----------------------------------------------------------------------------
# C __LINE__ equivalent in Python by Elf Sternberg
# http://www.elfsternberg.com/2008/09/23/c-__line__-equivalent-in-python/
# ----------------------------------------------------------------------------

def _line():
    info = getframeinfo(currentframe().f_back)[0:3]
    return '[%s:%d]' % (info[2], info[1])

# ----------------------------------------------------------------------------

def readbytes(number):
    """
    Read x amount of bytes from serial port.
    Credit: Boris Smus http://smus.com
    """
    buf = bytes()
    for _ in range(number):
        try:
            byte = SERIAL_PARAM.port.read()
        except (IOError, OSError) as err:
            log_me('error', err)
        buf += byte

    return buf

# ----------------------------------------------------------------------------

def decode_packet(message):
    """
    Decode incoming RFXtrx message.
    """

    timestamp = strftime('%Y-%m-%d %H:%M:%S')
    decoded = False

    # Verify incoming message
    log_me('debug', 'Verify incoming packet')
    if not test_rfx(ByteToHex(message)):
        log_me('error', 'The incoming message is invalid (' +
               ByteToHex(message) + ') Line: ' + _line())
        return
    log_me('debug', 'Verified OK')

    raw_message = ByteToHex(message)
    raw_message = raw_message.replace(' ', '')

    packettype = ByteToHex(message[1])
    log_me('debug', 'PacketType: %s' % str(packettype))

    subtype = None
    if len(message) > 2:
        subtype = ByteToHex(message[2])
        log_me('debug', 'SubType: %s' % str(subtype))

    seqnbr = None
    if len(message) > 3:
        seqnbr = ByteToHex(message[3])
        log_me('debug', 'SeqNbr: %s' % str(seqnbr))

    id1 = None
    if len(message) > 4:
        id1 = ByteToHex(message[4])
        log_me('debug', 'Id1: %s' % str(id1))

    id2 = None
    if len(message) > 5:
        id2 = ByteToHex(message[5])
        log_me('debug', 'Id2: %s' % str(id2))

    log_me('info', 'Packettype\t\t\t= ' + RFX.rfx_packettype[packettype])

    # ---------------------------------------
    # Verify correct length on packets
    # ---------------------------------------
    log_me('debug', 'Verify correct packet length')
    if packettype == '00' and len(message) != 14:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '01' and len(message) != 14 and len(message) != 21:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '02' and len(message) != 5:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '10' and len(message) != 8:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '11' and len(message) != 12:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '12' and len(message) != 9:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '13' and len(message) != 10:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '14' and len(message) != 11:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '15' and len(message) != 12:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '16' and len(message) != 8:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '17' and len(message) != 8:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '18' and len(message) != 8:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '19' and len(message) != 10:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '1A' and len(message) != 13:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '20' and len(message) != 9:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '28' and len(message) != 7:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '30' and len(message) != 8:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '40' and len(message) != 10:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '41' and len(message) != 7:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '42' and len(message) != 9:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '4E' and len(message) != 11:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '4F' and len(message) != 11:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '50' and len(message) != 9:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '51' and len(message) != 9:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '52' and len(message) != 11:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '53' and len(message) != 10:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '54' and len(message) != 14:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '55' and len(message) != 12:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '56' and len(message) != 17:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '57' and len(message) != 10:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '58' and len(message) != 14:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '59' and len(message) != 14:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '5A' and len(message) != 18:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '5B' and len(message) != 20:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '5C' and len(message) != 16:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '5D' and len(message) != 9:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '70' and len(message) != 8:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '71' and len(message) != 11:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    if packettype == '72' and len(message) != 10:
        log_me('error', 'Packet has wrong length, discarding')
        decoded = True
        packettype = None

    # ---------------------------------------
    # If packet is OK and the log_msg is active
    # then save the packet to log_msgfile designated
    # file on disk
    # ---------------------------------------
    if not decoded and CONFIG.log_msg:
        log_me('debug', 'Save packet to log_msgfile')
        try:
            data = str(ByteToHex(message))
            data = data.replace(' ', '')
            config_file = open(CONFIG.log_msgfile, 'a+')
            config_file.write(data + '\n')
            config_file.close()
        except Exception as err:
            log_me('error', 'Error when trying to write message log')
            log_me('error', err)

    metadata = list()
    output_extra = list()

    # 0x0 - Interface Control
    if packettype == '00':
        log_me('debug', 'Decode packetType 0x' + str(packettype) + ' - Start')
        decoded = True

    # 0x01 - Interface Message
    if packettype == '01':
        decoded = True
        metadata, output_extra = rfxdecode0x0.decode_0x01(message)

    # 0x02 - Receiver/Transmitter Message
    if packettype == '02':
        decoded = True
        metadata, output_extra = rfxdecode0x0.decode_0x02(subtype, seqnbr, id1)

    # 0x03 - Undecoded Message
    if packettype == '03':
        decoded = True
        metadata, output_extra = rfxdecode0x0.decode_0x03(message, subtype, seqnbr)

    # 0x10 Lighting1
    if packettype == '10':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x10(message, subtype, seqnbr)

    # 0x11 Lighting2
    if packettype == '11':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x11(message, subtype, seqnbr)

    # 0x12 Lighting3
    if packettype == '12':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x12(message, subtype, seqnbr)

    # 0x13 Lighting4
    if packettype == '13':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x13(message, subtype, seqnbr)

    # 0x14 Lighting5
    if packettype == '14':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x14(message, subtype, seqnbr, id1, id2)

    # 0x15 Lighting6
    if packettype == '15':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x15(message, subtype, seqnbr, id1, id2)

    # 0x16 Chime
    if packettype == '16':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x16(message, subtype, seqnbr, id1, id2)

    # 0x17 Fan (Transmitter only)
    if packettype == '17':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x17(subtype, seqnbr)

    # 0x18 Curtain1 (Transmitter only)
    if packettype == '18':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x18(subtype, seqnbr)

    # 0x19 Blinds1
    if packettype == '19':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x19(subtype, seqnbr)

    # 0x1A RTS
    if packettype == '1A':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x1a(message, subtype, seqnbr, id1, id2)

    # 0x20 Security1
    if packettype == '20':
        decoded = True
        metadata, output_extra = rfxdecode0x2.decode_0x20(message, subtype, seqnbr, id1, id2)

    # 0x28 Camera1
    if packettype == '28':
        decoded = True
        metadata, output_extra = rfxdecode0x2.decode_0x28(subtype, seqnbr)

    # 0x30 Remote control and IR
    if packettype == '30':
        decoded = True
        metadata, output_extra = rfxdecode0x3.decode_0x30(message, subtype, seqnbr, id1)

    # 0x40 Thermostat1
    if packettype == '40':
        decoded = True
        metadata, output_extra = rfxdecode0x4.decode_0x40(message, subtype, seqnbr, id1, id2)

    # 0x41 Thermostat2
    if packettype == '41':
        decoded = True
        metadata, output_extra = rfxdecode0x4.decode_0x41(subtype, seqnbr)

    # 0x42 Thermostat3
    if packettype == '42':
        decoded = True
        metadata, output_extra = rfxdecode0x4.decode_0x42(message, subtype, seqnbr, id1, id2)

    # 0x50 Temperature sensors
    if packettype == '50':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x50(message, subtype, seqnbr, id1, id2)

    # 0x51 Humidity sensors
    if packettype == '51':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x51(message, subtype, seqnbr, id1, id2)

    # 0x52 Temperature and humidity sensors
    if packettype == '52':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x52(message, subtype, seqnbr, id1, id2)

    # 0x53 Barometric
    if packettype == '53':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x53(subtype, seqnbr)

    # 0x54 Temperature, humidity and barometric sensors
    if packettype == '54':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x54(message, subtype, seqnbr, id1, id2, \
            CONFIG.barometric)

    # 0x55 Rain sensors
    if packettype == '55':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x55(message, subtype, seqnbr, id1, id2)

    # 0x56 Wind sensors
    if packettype == '56':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x56(message, subtype, seqnbr, id1, id2)

    # 0x57 UV Sensor
    if packettype == '57':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x57(message, subtype, seqnbr, id1, id2)

    # 0x58 Date/Time sensor
    if packettype == '58':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x58(message, subtype, seqnbr, id1, id2)

    # 0x59 Current Sensor
    if packettype == '59':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x59(message, subtype, seqnbr, id1, id2)

    # 0x5A Energy sensor
    if packettype == '5A':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5a(message, subtype, seqnbr, id1, id2)

    # 0x5B Current Sensor
    if packettype == '5B':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5b(message, subtype, seqnbr, id1, id2)

    # 0x5C Power Sensors
    if packettype == '5C':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5c(message, subtype, seqnbr, id1, id2)

    # 0x5D
    if packettype == '5D':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5d(subtype, seqnbr)

    # 0x5E Gas Usage Sensor
    if packettype == '5E':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5e(subtype, seqnbr)

    # 0x5F Water Usage Sensor
    if packettype == '5F':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5f(subtype, seqnbr)

    # 0x70 RFXsensor
    if packettype == '70':
        decoded = True
        metadata, output_extra = rfxdecode0x7.decode_0x70(message, subtype, seqnbr, id1)

    # 0x71 RFXmeter
    if packettype == '71':
        decoded = True
        metadata, output_extra = rfxdecode0x7.decode_0x71(message, subtype, seqnbr, id1, id2)

    # 0x72 FS20
    if packettype == '72':
        decoded = True
        metadata, output_extra = rfxdecode0x7.decode_0x72(subtype, seqnbr)

    # Not decoded message

    # The packet is not decoded, then log_me('info', it on the screen)
    if not decoded:
        log_me('error', 'Message not decoded. Line: ' + _line())
        log_me('error', 'Message: ' + ByteToHex(message))
        log_me('info', timestamp + ' ' + ByteToHex(message))
        log_me('info', 'RFXCMD cannot decode message, see http://code.google.com/p/rfxcmd/wiki/')

    # Print result
    print_decoded(metadata)
    output_me(timestamp, message, packettype, subtype, seqnbr, output_extra)
    domotricks_me(timestamp, message, packettype, subtype, seqnbr, metadata)

    # decodePackage END
    return

# ----------------------------------------------------------------------------

def read_socket():
    """
    Check socket for messages

    Credit: Olivier Djian
    """

    if not MESSAGEQUEUE.empty():
        log_me('debug', 'Message received in socket MESSAGEQUEUE')
        message = MESSAGEQUEUE.get().decode('UTF-8')

        if test_rfx(message):

            if CONFIG.serial_active:
                # Flush buffer
                SERIAL_PARAM.port.flushOutput()
                log_me('debug', 'SerialPort flush output')
                SERIAL_PARAM.port.flushInput()
                log_me('debug', 'SerialPort flush input')

            timestamp = strftime('%Y-%m-%d %H:%M:%S')

            log_me('info', '------------------------------------------------')
            log_me('info', 'Incoming message from socket')
            log_me('info', 'Send\t\t\t= ' + ByteToHex(codecs_decode(message, 'hex')))
            log_me('info', 'Date/Time\t\t\t= ' + timestamp)
            log_me('info', 'Packet Length\t\t= ' + ByteToHex(codecs_decode(message, 'hex')[0]))

            try:
                log_me('debug', 'Decode message')
                decode_packet(codecs_decode(message, 'hex'))
            except KeyError:
                log_me('error', 'Unrecognizable packet. Line: ' + _line())

            if CONFIG.serial_active:
                log_me('debug', 'Write message to serial port')
                SERIAL_PARAM.port.write(codecs_decode(message, 'hex'))

        else:
            log_me('error', 'Invalid message from socket. Line: ' + _line())

# ----------------------------------------------------------------------------

def test_rfx(message):
    """
    Test, filter and verify that the incoming message is valid
    Return true if valid, False if not
    """

    log_me('debug', 'Test message: ' + message)

    # Remove all invalid characters
    message = stripped(message)

    return_statement = True

    # Remove any whitespaces
    try:
        message = message.replace(' ', '')
    except Exception:
        log_me('error', 'Removing white spaces')
        return False

    # Test the string if it is hex format
    if message == '':
        log_me('error', 'Packet empty')
        return_statement = False
    # Check that length is even
    elif len(message) % 2:
        log_me('error', 'Packet length not even')
        return_statement = False
    # Check that first byte is not 00
    elif ByteToHex(codecs_decode(message, 'hex')[0]) == '00':
        log_me('error', 'Packet first byte is 00')
        return_statement = False
    # Length more than one byte
    elif not len(codecs_decode(message, 'hex')) > 1:
        log_me('error', 'Packet is not longer than one byte')
        return_statement = False
    # Check if string is the length that it reports to be
    elif not len(codecs_decode(message, 'hex')) == (codecs_decode(message, 'hex')[0] + 1):
        log_me('error', 'Packet length is not valid')
        return_statement = False
    else:
        log_me('debug', 'Message OK')

    return return_statement

# ----------------------------------------------------------------------------

def send_rfx(message):
    """
    Decode and send raw message to RFX device
    """
    timestamp = strftime('%Y-%m-%d %H:%M:%S')

    log_me('info', '------------------------------------------------')
    log_me('info', 'Send\t\t\t= ' + ByteToHex(message))
    log_me('info', 'Date/Time\t\t\t= ' + timestamp)
    log_me('info', 'Packet Length\t\t= ' + ByteToHex(message[0]))

    try:
        decode_packet(message)
    except KeyError as err:
        log_me('error', 'unrecognizable packet %s' % err)

    SERIAL_PARAM.port.write(message)
    sleep(1)

# ----------------------------------------------------------------------------

def read_rfx():
    """
    Read message from RFXtrx and decode the decode the message
    """
    message = None
    byte = None

    try:
        try:
            if SERIAL_PARAM.port.inWaiting() != 0:
                timestamp = strftime('%Y-%m-%d %H:%M:%S')
                log_me('debug', 'Timestamp: ' + timestamp)
                log_me('debug', 'SerWaiting: ' + str(SERIAL_PARAM.port.inWaiting()))
                byte = SERIAL_PARAM.port.read()
                log_me('debug', 'Byte: ' + str(ByteToHex(byte)))
        except IOError as err:
            log_me('error', err)
            log_me('error', 'Serial read %s, Line: %s' % (str(err), _line()))

        if byte:
            message = byte + readbytes(ord(byte))
            log_me('debug', 'Message: ' + str(ByteToHex(message)))

            # First byte indicate length of message, must be other than 00
            if ByteToHex(message[0]) != '00':

                # Verify length
                log_me('debug', 'Verify length')
                if (len(message) - 1) == message[0]:
                    log_me('debug', 'Length OK')

                    log_me('info', '------------------------------------------------')
                    log_me('info', 'Received\t\t\t= ' + ByteToHex(message))
                    log_me('info', 'Date/Time\t\t\t= ' + timestamp)
                    log_me('info', 'Packet Length\t\t= ' + ByteToHex(message[0]))

                    log_me('debug', 'Decode packet')
                    try:
                        decode_packet(message)
                    except KeyError as err:
                        log_me('error', 'unrecognizable packet (' + ByteToHex(message) + \
                               ') Line: ' + _line())
                        log_me('error', err)
                    rawcmd = ByteToHex(message)
                    rawcmd = rawcmd.replace(' ', '')

                    return rawcmd

                log_me('error', 'Incoming packet not valid length. Line: '  + _line())
                log_me('error', '------------------------------------------------')
                log_me('error', 'Received\t\t\t= ' + ByteToHex(message))
                log_me('error', 'Incoming packet not valid, waiting for next...')

    except OSError:
        log_me('error', 'Error in message: ' + str(ByteToHex(message)) + ' Line: ' + _line())
        log_me('error', 'Traceback: ' + format_exc())
        log_me('error', '------------------------------------------------')
        log_me('error', 'Received\t\t\t= ' + ByteToHex(message))
        format_exc()
    return None

# ----------------------------------------------------------------------------

def read_config(configfile, configitem):
    """
    Read item from the configuration file
    """
    log_me('debug', 'Open configuration file')
    log_me('debug', 'File: ' + configfile)

    if os.path.exists(configfile):

        #open the xml file for reading:
        config_file = open(configfile, 'r')
        data = config_file.read()
        config_file.close()

        # xml parse file data
        log_me('debug', 'Parse config XML data')
        try:
            dom = minidom.parseString(data)
        except Exception as err:
            log_me('error', 'problem in the config.xml file, cannot process it')
            log_me('error', err)

        # Get config item
        log_me('debug', 'Get the configuration item: ' + configitem)

        try:
            xml_tag = dom.getElementsByTagName(configitem)[0].toxml()
            log_me('debug', 'Found: ' + xml_tag)
            xml_data = xml_tag.replace('<' + configitem + '>', '').\
                replace('</' + configitem + '>', '')
            log_me('debug', '--> ' + xml_data)
        except Exception as err:
            log_me('error', 'The item tag not found in the config file')
            log_me('error', err)
            xml_data = ''

        log_me('debug', 'Return')

    else:
        log_me('error', 'Config file does not exists. Line: ' + _line())

    return xml_data

# ----------------------------------------------------------------------------

def print_version():
    """
    Print RFXCMD version, build and date
    """
    log_me('debug', 'print_version')
    log_me('info', 'RFXCMD Version: ' + __version__)
    log_me('info', __date__.replace('$', ''))
    log_me('debug', 'Exit 0')
    sys.exit(0)

# ----------------------------------------------------------------------------

def check_pythonversion():
    """
    Check python version
    """
    if sys.hexversion < 0x02060000:
        log_me('error', 'Your Python need to be 2.6 or newer, please upgrade.')
        sys.exit(1)

# ----------------------------------------------------------------------------

def option_listen():
    """
    Listen to RFXtrx device and process data, exit with CTRL+C
    """
    log_me('debug', 'Start listening...')

    if CONFIG.serial_active:
        log_me('debug', 'Open serial port')
        open_serialport()

    if CONFIG.socketserver:
        try:
            serversocket = RFXcmdSocketAdapter(CONFIG.sockethost, int(CONFIG.socketport))
        except Exception as err:
            log_me('error', 'Error starting socket server. Line: ' + _line())
            log_me('error', 'can not start server socket, another instance already running?')
            log_me('error', err)
            sys.exit(1)
        if serversocket.net_adapter_registered:
            log_me('debug', 'Socket interface started')
        else:
            log_me('warning', 'Cannot start socket interface')

    if CONFIG.serial_active:
        # Flush buffer
        log_me('debug', 'Serialport flush output')
        SERIAL_PARAM.port.flushOutput()
        log_me('debug', 'Serialport flush input')
        SERIAL_PARAM.port.flushInput()

        # Send RESET
        log_me('debug', 'Send rfxcmd_reset (' + RFXCMD.reset + ')')
        SERIAL_PARAM.port.write(codecs_decode(RFXCMD.reset, 'hex'))
        log_me('debug', 'Sleep 1 sec')
        sleep(1)

        # Flush buffer
        log_me('debug', 'Serialport flush output')
        SERIAL_PARAM.port.flushOutput()
        log_me('debug', 'Serialport flush input')
        SERIAL_PARAM.port.flushInput()

        # Send STATUS
        log_me('debug', 'Send rfxcmd_status (' + RFXCMD.status + ')')
        SERIAL_PARAM.port.write(codecs_decode(RFXCMD.status, 'hex'))
        log_me('debug', 'Sleep 1 sec')
        sleep(1)

        # If active (autostart)
        if CONFIG.protocol_startup:
            log_me('debug', 'Protocol AutoStart activated')
            try:
                p_message = protocol.set_protocolfile(CONFIG.protocol_file)
                log_me('debug', 'Send set protocol message (' + p_message + ')')
                SERIAL_PARAM.port.write(codecs_decode(p_message, 'hex'))
                log_me('debug', 'Sleep 1 sec')
                sleep(1)
            except Exception as err:
                log_me('error', 'Could not create protocol message')

    try:
        while 1:
            # Let it breath
            # Without this sleep it will cause 100% CPU in windows
            sleep(0.01)

            if CONFIG.serial_active:
                # Read serial port
                if CONFIG.process_rfxmsg:
                    rawcmd = read_rfx()
                    if rawcmd:
                        log_me('debug', 'Processed: ' + str(rawcmd))

            # Read socket
            if CONFIG.socketserver:
                read_socket()

    except KeyboardInterrupt:
        log_me('debug', 'Received keyboard interrupt')
        log_me('debug', 'Close server socket')
        serversocket.net_adapter.shutdown()

        if CONFIG.serial_active:
            log_me('debug', 'Close serial port')
            close_serialport()

        log_me('info', '\nExit...')

# ----------------------------------------------------------------------------

def option_getstatus():
    """
    Get status from RFXtrx device and log_me('info', on screen)
    """

    # Flush buffer
    SERIAL_PARAM.port.flushOutput()
    SERIAL_PARAM.port.flushInput()

    # Send RESET
    SERIAL_PARAM.port.write(codecs_decode(RFXCMD.reset, 'hex'))
    sleep(1)

    # Flush buffer
    SERIAL_PARAM.port.flushOutput()
    SERIAL_PARAM.port.flushInput()

    # Send STATUS
    send_rfx(codecs_decode(RFXCMD.status, 'hex'))
    sleep(1)
    read_rfx()

# ----------------------------------------------------------------------------

def open_serialport():
    """
    Open serial port for communication to the RFXtrx device.
    """

    # Check that serial module is loaded
    try:
        log_me('debug', 'Serial extension version: ' + VERSION)
    except Exception as err:
        log_me('error', 'You need to install Serial extension for Python')
        log_me('error', err)
        sys.exit(1)

    # Check for serial device
    if CONFIG.device:
        log_me('debug', 'Device: ' + CONFIG.device)
    else:
        log_me('error', 'Device name missing. Line: ' + _line())
        sys.exit(1)

    # Open serial port
    log_me('debug', 'Open Serialport')
    try:
        SERIAL_PARAM.port = Serial(CONFIG.device,
                                   SERIAL_PARAM.rate,
                                   timeout=SERIAL_PARAM.timeout)
    except SerialException as err:
        log_me('error', 'Failed to connect on device ' + CONFIG.device + ' Line: ' + _line())
        log_me('error', err)
        sys.exit(1)

    if not SERIAL_PARAM.port.isOpen():
        SERIAL_PARAM.port.open()

# ----------------------------------------------------------------------------

def close_serialport():
    """
    Close serial port.
    """

    log_me('debug', 'Close serial port')
    try:
        SERIAL_PARAM.port.close()
        log_me('debug', 'Serial port closed')
    except SerialException as err:
        log_me('error', 'Failed to close the serial port (' + CONFIG.device + ') Line: ' + _line())
        log_me('error', err)
        sys.exit(1)

# ----------------------------------------------------------------------------

def dict_asset(timestamp, message, packettype, subtype, seqnbr, metadata_obj):
    """
    Return a dict formed by asset data
    """
    rawcmd = ByteToHex(message)
    rawcmd = rawcmd.replace(' ', '')

    result = dict()
    result['timestamp'] = timestamp
    result['key'] = f'{packettype}_{subtype}'
    result['rawcmd'] = rawcmd
    result['packettype'] = RFX.rfx_packettype[packettype]
    result['packettype_id'] = packettype
    result['subtype'] = subtype
    result['seqnbr'] = seqnbr

    if not metadata_obj:
        result['metadata'] = dict()
    elif isinstance(metadata_obj[0], dict):
        result['metadata'] = metadata_obj
        for metadata in metadata_obj:
            if metadata['key'] == 'Id':
                result['key'] += f'_{metadata["value"]}'
        for metadata in metadata_obj:
            if metadata['key'] == 'Unitcode':
                result['key'] += f'_{metadata["value"]}'
    else:
        result['metadata'] = dict()
        for metadata in metadata_obj:
            result['metadata'][metadata[0]] = metadata[1]
        if 'id' in result['metadata']:
            result['key'] += f'_{result["metadata"]["id"]}'
        if 'unitcode' in result['metadata']:
            result['key'] += f'_{result["metadata"]["unitcode"]}'

    return result

def domotricks_me(timestamp, message, packettype, subtype, seqnbr, metadata_dict):
    """
    This function writes in the sqlite database and trigger alerting
    """
    conn = SqliteCmd(settings.DB_PATH)

    asset = dict_asset(timestamp, message, packettype, subtype, seqnbr, metadata_dict)

    # Log in specific table if the asset is registred
    if conn.is_registered_asset(asset['key']):
        nickname = conn.get_asset_nickname(asset['key'])
        log_me('debug', f'registred asset: {asset["key"]} as {nickname}')
        conn.create_asset_table(asset['key'])
        conn.insert_asset(
            f'asset_{asset["key"]}',
            asset['timestamp'],
            asset['packettype'],
            asset['packettype_id'],
            asset['subtype'],
            asset['seqnbr'],
            str(asset['metadata']))
        functions = conn.get_device_alerting(asset['key'])
        if functions is not None:
            for function in functions[0].split('|'):
                if not hasattr(alerting, function):
                    log_me('error', f'alerting function "{function}" does not exist...')
                    continue
                log_me('debug', f'trigger alerting function "{function}" for {nickname}')
                getattr(alerting, function)(nickname, metadata_dict)
    elif asset['key'] not in ['01_00']:
        log_me('debug', f'lost asset: {asset["key"]}')
        conn.insert_lost_asset(
            asset['key'],
            asset['timestamp'],
            asset['packettype'],
            asset['packettype_id'],
            asset['subtype'],
            asset['seqnbr'],
            str(asset['metadata']))

def output_me(timestamp, message, packettype, subtype, seqnbr, metadata_list):
    """
    This function writes json or csv output in a different file
    """
    try:
        output_file = open('/var/log/output.log', 'a+')
    except Exception as err:
        log_me('error', err)
        return

    asset = dict_asset(timestamp, message, packettype, subtype, seqnbr, metadata_list)

    if CMDARG.printout_csv:
        result = f'{asset["timestamp"]};{asset["key"]};{asset["rawcmd"]};{asset["packettype"]};{asset["subtype"]};{asset["seqnbr"]};{str(asset["metadata"])}'
    else:
        result = dumps(asset)
    output_file.write(str(result) + '\n')
    output_file.close()
    sys.stdout.write(str(result) + '\n')
    sys.stdout.flush()

def log_me(verbosity, message):
    """
    This function write logs
    """
    if verbosity == 'error':
        LOGGER.error(message)
    elif verbosity == 'warning':
        LOGGER.warning(message)
    elif verbosity == 'info':
        if CMDARG.printout_complete:
            LOGGER.info(message)
    else:
        if CMDARG.printout_debug:
            LOGGER.debug(message)

def print_decoded(metadata, prefix=''):
    """
    Display metadata of a list of dict which may contains metadata as value
    """
    for i in metadata:
        if isinstance(i['value'], list):
            log_me('info', '%s%s:' % (prefix, i['key']))
            print_decoded(i['value'], prefix='    ')
        elif 'unit' in i:
            log_me('info', '%s%s: %s %s' % (prefix, i['key'], i['value'], i['unit']))
        else:
            log_me('info', '%s%s: %s' % (prefix, i['key'], i['value']))

# ----------------------------------------------------------------------------


if __name__ == '__main__':

    # Init shutdown handler
    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    # Init objects
    CONFIG = ConfigData()
    CMDARG = CmdArgData()
    RFX = lib.rfx_sensors.rfx_data()
    RFXCMD = RfxCmdData()
    SERIAL_PARAM = SerialData()

    # Check python version
    check_pythonversion()

    # Get directory of the rfxcmd script
    CONFIG.program_path = os.path.dirname(os.path.realpath(__file__))

    PARSER = ArgumentParser()
    PARSER.add_argument('-d', '--device', action='store', dest='device', \
        help='The serial device of the RFXCOM, example /dev/ttyUSB0')
    PARSER.add_argument('-l', '--listen', action='store_true', dest='listen', \
        help='Listen for messages from RFX device')
    PARSER.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False, \
        help='Output all messages to stdout')
    PARSER.add_argument('-c', '--csv', action='store_true', dest='csv', default=False, \
        help='Output all messages to stdout in CSV format')
    PARSER.add_argument('-V', '--version', action='store_true', dest='version', \
        help='Print rfxcmd version information')
    PARSER.add_argument('-D', '--debug', action='store_true', dest='debug', default=False, \
        help='Debug printout on stdout')
    ARGS = PARSER.parse_args()

    # ----------------------------------------------------------
    # VERSION PRINT
    if ARGS.version:
        print_version()

    # ----------------------------------------------------------
    # LOGHANDLER
    if ARGS.debug:
        LOGLEVEL = logging.DEBUG
    else:
        LOGLEVEL = logging.ERROR
    # Logging
    FORMATTER = logging.Formatter('%(asctime)s - %(threadName)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s')
    HANDLER = logging.StreamHandler()
    HANDLER.setFormatter(FORMATTER)
    LOGGER = logging.getLogger('RFXPROTO')
    LOGGER.setLevel(LOGLEVEL)
    LOGGER.addHandler(HANDLER)

    if ARGS.debug:
        CMDARG.printout_debug = True
        CMDARG.printout_complete = True
        log_me('debug', 'Debug printout ' + _line())

    if ARGS.verbose:
        CMDARG.printout_complete = True
        log_me('info', 'Verbose printout ' + _line())
        log_me('info', 'RFXCMD Version ' + __version__)

    log_me('debug', 'Python version: %s.%s.%s' % sys.version_info[:3])
    log_me('debug', 'RFXCMD Version: ' + __version__)
    log_me('debug', __date__.replace('$', ''))

    # ----------------------------------------------------------
    # OUTPUT
    if ARGS.csv:
        log_me('debug', 'CSV printout')
        CMDARG.printout_csv = True
    else:
        CMDARG.printout_csv = False

    # ----------------------------------------------------------
    # SERIAL
    if ARGS.device:
        CONFIG.device = ARGS.device
    elif CONFIG.serial_device:
        CONFIG.device = CONFIG.serial_device

    # ----------------------------------------------------------
    # DAEMON
    if CONFIG.daemon_active and ARGS.listen:
        log_me('debug', 'Daemon')
        log_me('debug', 'Check PID file')

        if CONFIG.daemon_pidfile:
            CMDARG.pidfile = CONFIG.daemon_pidfile
            CMDARG.createpid = True
            log_me('debug', 'PID file ' + CMDARG.pidfile)

            if os.path.exists(CMDARG.pidfile):
                log_me('info', 'PID file ' + CMDARG.pidfile + ' already exists. Exiting.')
                log_me('debug', 'PID file ' + CMDARG.pidfile + ' already exists.')
                sys.exit(1)
            else:
                log_me('debug', 'PID file does not exists')

        else:
            log_me('error', 'Command argument --pidfile missing. Line: ' + _line())
            sys.exit(1)

        log_me('debug', 'Check platform')
        if sys.platform == 'win32':
            log_me('error', 'Daemonize not supported under Windows. Line: ' + _line())
            sys.exit(1)
        else:
            log_me('debug', 'Platform: ' + sys.platform)

            try:
                log_me('debug', 'Write PID file')
                PID_FILE = open(CMDARG.pidfile, 'w')
                PID_FILE.write('pid')
                PID_FILE.close()
            except IOError as err:
                log_me('error', 'Line: ' + _line())
                log_me('error', 'Unable to write PID file: %s [%d]' % (err.strerror, err.errno))
                raise SystemExit('Unable to write PID file: %s [%d]' % (err.strerror, err.errno)) \
                    from err

            log_me('debug', 'Deactivate screen printouts')
            CMDARG.printout_complete = False

            log_me('debug', 'Start daemon')
            daemonize()

    # ----------------------------------------------------------
    # SQLite
    SqliteCmd(settings.DB_PATH).create_device_alerting_table()
    SqliteCmd(settings.DB_PATH).create_lost_table()
    SqliteCmd(settings.DB_PATH).create_myassets_table()
    SqliteCmd(settings.DB_PATH).create_time_alerting_table()

    # ----------------------------------------------------------
    # LISTEN
    if ARGS.listen:
        option_listen()

    log_me('debug', 'Exit 0')
    sys.exit(0)

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
