#!/usr/bin/env python3
# coding=UTF-8
"""
DomoTricks: RFX utils

Based on Sebastian Sjoholm work https://github.com/ssjoholm/rfxcmd_gc
Copyright 2012-2014 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
Based on Nicolas Béguier work https://github.com/nbeguier/rfxcmd
Copyright 2018-2021 by Nicolas BEGUIER, nicolas_beguier@hotmail.com

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
from binascii import hexlify

def stripped(string):
    """
    Strip all characters that are not valid
    Credit: http://rosettacode.org/wiki/Strip_control_codes_and_extended_characters_from_a_string
    """
    return ''.join([i for i in string if ord(i) in range(32, 127)])

def ByteToHex(byteStr):
    """
    Convert a byte string to it's hex string representation e.g. for output.
    http://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/

    Added str() to byteStr in case input data is in integer
    """
    try:
        return hexlify(byteStr).decode('utf-8')
    except:
        return '{0:#0{1}x}'.format(byteStr, 4).split('0x')[1]
    return '00'

def dec2bin(dec, width=8):
    """
    Base-2 (Binary) Representation Using Python
    http://stackoverflow.com/questions/187273/base-2-binary-representation-using-python
    Brian (http://stackoverflow.com/users/9493/brian)
    """
    return ''.join(str((dec>>i)&1) for i in range(width-1,-1,-1))

def testBit(int_type, offset):
    """
    testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
    http://wiki.python.org/moin/BitManipulation
    """
    mask = 1 << offset
    return int_type & mask

def clearBit(int_type, offset):
    """
    clearBit() returns an integer with the bit at 'offset' cleared.
    http://wiki.python.org/moin/BitManipulation
    """
    mask = ~(1 << offset)
    return int_type & mask

def split_len(seq, length):
    """
    Split string into specified chunks.
    """
    return [seq[i:i+length] for i in range(0, len(seq), length)]
