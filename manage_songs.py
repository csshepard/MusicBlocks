#!/usr/bin/env python

"""
Manage Music Blocks

Usage:
  manage_songs.py add --block=<block_number> --title=<title> --file=<file_name> [--uid=<tag_id>]
  manage_songs.py replace --block=<block_number> --title=<title> --file=<file_name>
  manage_songs.py remove --block=<block_number>
  manage_songs.py status
  manage_songs.py -h | --help

Options:
  -h --help                                  Show this screen.
  -b <block_number>, --block=<block_number>  Integer printed on block.
  -t <title>, --title=<title>                Song Title.
  -f <file_name>, --file=<file_name>         File name of song.
  --uid=<tag_id>                             (optional) uid of NFC tag
"""

from __future__ import print_function
import sqlite3
import nxppy
import os
import shutil
import time
from docopt import docopt
import sys

if not os.path.isfile('/home/pi/MusicBlocks/MusicBlocks.db'):
    db = sqlite3.connect('/home/pi/MusicBlocks/MusicBlocks.db', detect_types=sqlite3.PARSE_DECLTYPES)
    db.executescript("""
                     CREATE TABLE block_table(
                         block_number INTEGER PRIMARY KEY,
                         tag_id TEXT);
                     CREATE TABLE song_table(
                         song_name TEXT,
                         file_name TEXT,
                         block_number INTEGER,
                         FOREIGN KEY(block_number) REFERENCES block_table(block_number));
                     CREATE TABLE play_history_table(
                         time_played TIMESTAMP,
                         song_name TEXT);
                     """)
    db.commit()
else:
    db = sqlite3.connect('/home/pi/MusicBlocks/MusicBlocks.db', detect_types=sqlite3.PARSE_DECLTYPES)
db.row_factory = sqlite3.Row


def replace_song(title, file_name, block_num):
    cursor = db.cursor()
    cursor.execute('SELECT * FROM block_table WHERE block_number=?', block_num)
    if cursor.fetchone() is not None:
        song = os.path.split(file_name)[1]
        cursor.execute('SELECT file_name FROM song_table WHERE block_number=?', block_num)
        old_file = cursor.fetchone()['file_name']
        try:
            shutil.copyfile(file_name, '/home/pi/Music/MusicBlocks/%s' % song)
        except IOError as e:
            print(e)
            return False
        cursor.execute('UPDATE song_table SET song_name=?, file_name=? WHERE block_number=?', (title, song, block_num))
        db.commit()
        try:
            os.remove('/home/pi/Music/MusicBlocks/%s' % old_file)
        except OSError:
            pass
        print('Block Updated')
        return True
    else:
        print('Block not found')
        return False


def add_block(title, file_name, block_num, tag_id=None):
    if tag_id is None:
        nfc = nxppy.Mifare()
        print('Place Tag on reader\n')
        for _ in range(10):
            try:
                print('Reading...')
                tag_id = nfc.select()
                print('Tag UID: %s' % tag_id)
                break
            except nxppy.SelectError:
                pass
            time.sleep(1)
    if tag_id is None:
        print('No Tag Detected')
        return False
    cursor = db.cursor()
    cursor.execute('SELECT * FROM block_table WHERE tag_id=? OR block_number=?', (tag_id, block_num))
    block = cursor.fetchone()
    if block is None:
        song = os.path.split(file_name)[1]
        cursor.execute('INSERT INTO block_table (block_number, tag_id) VALUES (?, ?)', (block_num, tag_id))
        cursor.execute('INSERT INTO song_table (song_name, file_name, block_number) VALUES (?, ?, ?)', (title, song, block_num))
        try:
            shutil.copyfile(file_name, '/home/pi/Music/MusicBlocks/%s' % song)
        except IOError as e:
            db.rollback()
            print(e)
            return False
        db.commit()
        print('Block Added')
        return True
    else:
        if block['block_number'] == block_num:
            print('Block already in use')
        else:
            print('Tag already in use')
        return False


def remove_block(block_num):
    query = db.execute('SELECT file_name FROM song_table WHERE block_number=?',
                       block_num)
    song = query.fetchone()
    if song is not None:
        try:
            os.remove('/home/pi/Music/MusicBlocks/%s' % song['file_name'])
        except OSError:
            print('Song File Not Found')
        db.execute('DELETE FROM song_table WHERE block_number=?', block_num)
        db.execute('DELETE FROM block_table WHERE block_number=?', block_num)
        db.commit()
        print('Block %s Deleted' % block_num)
        return True
    else:
        print('Block %s not found' % block_num)
        return False


def status():
    query = db.execute("""\
        SELECT song_table.song_name AS song_name,
        block_table.block_number AS block_number,
        block_table.tag_id AS tag_id FROM song_table
        INNER JOIN block_table
        ON block_table.block_number=song_table.block_number
        ORDER BY block_number
        """)
    row = '{:^14}{:^25}{:^16}'
    print(row.format('Block Number', 'Song', 'Tag ID'))
    for block in query.fetchall():
        print(row.format(block['block_number'], block['song_name'],
                         block['tag_id']))


if __name__ == '__main__':
    args = docopt(__doc__)
    if args['add']:
        add_block(args['--title'], args['--file'],
                  args['--block'], args['--uid'])
    elif args['replace']:
            replace_song(args['--title'], args['--file'], args['--block'])
    elif args['status']:
        status()
    elif args['remove']:
        remove_block(args['--block'])
