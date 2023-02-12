#!/usr/bin/env python3
# coding=UTF-8
"""
DomoTricks: RFX command

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

# Standard library
import logging
import subprocess
import threading

LOGGER = logging.getLogger('domotricks-rfxcmd')

class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        def target():
            LOGGER.debug('Thread started, timeout = %s', str(timeout))
            self.process = subprocess.Popen(self.cmd, shell=True)
            self.process.communicate()
            LOGGER.debug('Return code: %s', str(self.process.returncode))
            LOGGER.debug('Thread finished')
            self.timer.cancel()

        def timer_callback():
            LOGGER.debug('Thread timeout, terminate it')
            if self.process.poll() is None:
                try:
                    self.process.kill()
                except OSError as error:
                    LOGGER.error('Error: %s ' % error)
                LOGGER.debug('Thread terminated')
            else:
                LOGGER.debug('Thread not alive')

        thread = threading.Thread(target=target)
        self.timer = threading.Timer(int(timeout), timer_callback)
        self.timer.start()
        thread.start()

# ----------------------------------------------------------------------------
