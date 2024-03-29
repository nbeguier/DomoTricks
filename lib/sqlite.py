#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DomoTricks: Sqlite wrapper library

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
import sqlite3

# Debug
# from pdb import set_trace as st

class SqliteCmd(object):
    """
    Sqlite3 DB commands
    """
    def __init__(self, DBfile):
        self.conn = sqlite3.connect(DBfile)
        self.cur = self.conn.cursor()

    ## TABLE CREATION

    def create_asset_table(self, asset_key):
        """
        Creating Asset table if not exist
        """
        self.cur.execute(
        f'''
        CREATE TABLE IF NOT EXISTS asset_{asset_key}
            (
                timestamp    TEXT NOT NULL PRIMARY KEY,
                packettype   TEXT NOT NULL,
                packettypeid TEXT NOT NULL,
                subtype      TEXT NOT NULL,
                seqnb        TEXT NOT NULL,
                metadata     TEXT NOT NULL
            )
        ''')

    def create_device_alerting_table(self):
        """
        Creating Device Alerting table if not exist
        functions=function1|function2
        """
        self.cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS device_alerting
            (
                assetkey  TEXT NOT NULL PRIMARY KEY,
                functions TEXT NOT NULL
            )
        ''')

    def create_lost_table(self):
        """
        Creating Lost table if not exist
        """
        self.cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS lost
            (
                assetkey     TEXT NOT NULL PRIMARY KEY,
                timestamp    TEXT NOT NULL,
                packettype   TEXT NOT NULL,
                packettypeid TEXT NOT NULL,
                subtype      TEXT NOT NULL,
                seqnb        TEXT NOT NULL,
                metadata     TEXT NOT NULL
            )
        ''')

    def create_myassets_table(self):
        """
        Creating main table if not exist
        """
        self.cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS my_assets
            (
                assetkey     TEXT NOT NULL PRIMARY KEY,
                packettype   TEXT NOT NULL,
                packettypeid TEXT NOT NULL,
                subtype      TEXT NOT NULL,
                nickname     TEXT
            )
        ''')

    def create_time_alerting_table(self):
        """
        Creating Time Alerting table if not exist
        functions=function1:HH:MM|function2:HH:MM
        """
        self.cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS time_alerting
            (
                assetkey  TEXT NOT NULL PRIMARY KEY,
                functions TEXT NOT NULL
            )
        ''')

    ## MY ASSETS

    def get_asset_key(self, nickname):
        """
        Get asset from nickname
        """
        try:
            res = self.cur.execute(
            '''
            SELECT
                assetkey
            FROM
                my_assets
            WHERE
                nickname = ?
            ''', (nickname,))
            return res.fetchone()
        except sqlite3.OperationalError:
            return None

    def get_my_assets(self):
        """
        Get all my assets
        """
        res = self.cur.execute(
        '''
        SELECT
            assetkey, packettype, nickname
        FROM
            my_assets
        ''')
        return res.fetchall()

    def get_asset_nickname(self, asset_key):
        """
        Get asset nickname
        """
        res = self.cur.execute(
        '''
        SELECT
            nickname
        FROM
            my_assets
        WHERE
            assetkey = ?
        ''', (asset_key,))
        fetch = res.fetchone()
        if fetch:
            return fetch[0]
        return 'Unknown'

    def insert_my_asset(self, asset_key, packettype, packettypeid, subtype, nickname):
        '''
        Insert new asset in "my_assets"
        '''
        self.cur.execute(
            '''
            INSERT INTO my_assets
            (
                assetkey,
                packettype,
                packettypeid,
                subtype,
                nickname
            ) VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?
            )
            ''', (asset_key, packettype, packettypeid, subtype, nickname))
        self.conn.commit()

    def update_my_asset_nickname(self, assetkey, nickname):
        """
        Edit an asset nickname
        """
        try:
            self.cur.execute(
            '''
            UPDATE
                my_assets
            SET
                nickname = ?
            WHERE
                assetkey = ?
            ''', (nickname, assetkey))
            self.conn.commit()
            return True
        except sqlite3.OperationalError:
            return False

    def delete_my_asset(self, assetkey):
        """
        Delete an assetkey from my_assets
        """
        try:
            self.cur.execute(
            '''
            DELETE FROM
                my_assets
            WHERE
                assetkey = ?
            ''', (assetkey,))
            self.conn.commit()
            return True
        except sqlite3.OperationalError:
            return False

    def is_registered_asset(self, asset_key):
        """
        Verify if asset is registred
        """
        res = self.cur.execute(
        '''
        SELECT
            EXISTS (
                SELECT
                    1
                FROM
                    my_assets
                WHERE
                    assetkey = ?
            )
        ''', (asset_key,))
        fres = res.fetchone()[0]
        return fres == 1

    ## ASSET

    def get_asset(self, asset_key, last_only=False, timestamp_interval=[]):
        """
        Get asset
        last_only and timestamp_interval are not compatible
        """
        try:
            if last_only:
                res = self.cur.execute(
                f'''
                SELECT
                    timestamp, packettype, seqnb, metadata
                FROM
                    asset_{asset_key}
                ORDER BY timestamp DESC
                LIMIT 1
                ''')
                return res.fetchone()
            if timestamp_interval:
                res = self.cur.execute(
                f'''
                SELECT
                    timestamp, packettype, seqnb, metadata
                FROM
                    asset_{asset_key}
                WHERE
                    timestamp > ? AND timestamp < ?
                ORDER BY timestamp DESC
                ''', (timestamp_interval[0], timestamp_interval[1]))
                return res.fetchall()
            res = self.cur.execute(
            f'''
            SELECT
                timestamp, packettype, seqnb, metadata
            FROM
                asset_{asset_key}
            ORDER BY timestamp DESC
            ''')
            return res.fetchall()
        except sqlite3.OperationalError:
            return None

    def insert_asset(self, table_name, Timestamp, PacketType, PacketTypeId, Subtype, SeqNb, Metadata):
        """
        Insert new entry in an existing asset
        """
        self.cur.execute(
        f'''
        INSERT
        or IGNORE into {table_name} (
            timestamp,
            packettype,
            packettypeid,
            subtype,
            seqnb,
            metadata
        )
        VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
        ''', (Timestamp, PacketType, PacketTypeId, Subtype, SeqNb, Metadata))
        self.conn.commit()

    def delete_asset_log(self, assetkey, timestamp_interval=[]):
        """
        Delete a timestamped interval of log
        """
        try:
            self.cur.execute(
            f'''
            DELETE FROM
                asset_{assetkey}
            WHERE
                timestamp > ? AND timestamp < ?
            ''', (timestamp_interval[0], timestamp_interval[1]))
            return True
        except sqlite3.OperationalError:
            return False

    ## LOST ASSETS

    def get_lost_assets(self):
        """
        Get all lost assets
        """
        res = self.cur.execute(
        '''
        SELECT
            timestamp, assetkey, packettype, seqnb, metadata
        FROM
            lost
        ORDER BY timestamp DESC
        ''')
        return res.fetchall()

    def insert_lost_asset(self, asset_key, Timestamp, PacketType, PacketTypeId, Subtype, SeqNb, Metadata):
        """
        Insert new entry infos
        """
        is_exists = self.cur.execute(
        '''
        SELECT count(*)
        FROM lost
        WHERE assetkey = ?
        ''', (asset_key,)).fetchone()
        if is_exists[0] == 1:
            self.cur.execute(
            '''
            UPDATE lost
            SET
                timestamp = ?,
                metadata = ?
            WHERE
                assetkey = ?
            ''', (Timestamp, Metadata, asset_key))
        else:
            self.cur.execute(
            '''
            INSERT
            or IGNORE into lost (
                assetkey,
                timestamp,
                packettype,
                packettypeid,
                subtype,
                seqnb,
                metadata
            )
            VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
            ''', (asset_key, Timestamp, PacketType, PacketTypeId, Subtype, SeqNb, Metadata))
        self.conn.commit()

    def delete_lost_asset(self, timestamp=None, asset_key=None):
        """
        Delete lost asset for all asset older than timestamp or directly an assetkey
        """
        try:
            if timestamp is not None:
                self.cur.execute(
                '''
                DELETE FROM
                    lost
                WHERE
                    timestamp < ?
                ''', (timestamp,))
                self.conn.commit()
                return True
            if asset_key is not None:
                self.cur.execute(
                '''
                DELETE FROM
                    lost
                WHERE
                    assetkey = ?
                ''', (asset_key,))
                self.conn.commit()
                return True
            return False
        except sqlite3.OperationalError:
            return False

    ## DEVICE ALERTING

    def get_device_alerting(self, asset_key=None):
        """
        Get asset device alerting
        """
        try:
            if asset_key is None:
                res = self.cur.execute(
                '''
                SELECT
                    assetkey, functions
                FROM
                    device_alerting
                ''')
                return res.fetchall()
            res = self.cur.execute(
            '''
            SELECT
                functions
            FROM
                device_alerting
            WHERE
                assetkey = ?
            ''', (asset_key,))
            return res.fetchone()
        except sqlite3.OperationalError:
            return None

    ## TIME ALERTING

    def get_time_alerting(self):
        """
        Get time alerting
        """
        try:
            res = self.cur.execute(
            '''
            SELECT
                assetkey, functions
            FROM
                time_alerting
            ''')
            return res.fetchall()
        except sqlite3.OperationalError:
            return None

    def update_timealerting_asssetkey(self, old_asset, new_asset):
        """
        Update the assetkey of a time alert
        """
        try:
            self.cur.execute(
            '''
            UPDATE
                time_alerting
            SET
                assetkey = ?
            WHERE
                assetkey = ?
            ''', (new_asset, old_asset))
            self.conn.commit()
            return True
        except sqlite3.OperationalError:
            return False

    def __del__(self):
        try:
            self.cur.close()
            self.conn.close()
        except:
            pass

    def SQLiteClose(self):
        self.__del__()
