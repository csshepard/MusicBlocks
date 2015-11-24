"""
Manage Song Blocks

Usage:
  manage_songs.py add --block=<block_number> --title=<title> --file=<file_name> [--uid=<tag_id>]
  manage_songs.py replace --block=<block_number> --title=<title> --file=<file_name>
  manage_songs.py -h | --help

Options:
  -h --help               Show this screen.
  --block=<block_number>  Integer printed on block.
  --title=<title>         Song Title.
  --file=<file_name>      File name of song.
  --uid=<tag_id>          (optional) uid of NFC tag
"""

from __future__ import print_function
import sqlite3
#import nxppy
import os
import shutil
import time
from docopt import docopt


db = sqlite3.connect('SongBlocks.db')
db.row_factory = sqlite3.Row

def replace_song(title, file_name, block_num):
    cursor = db.cursor()
    cursor.execute('SELECT * FROM block_table WHERE block_number=?',block_num)
    if cursor.fetchone() is not None and os.path.isfile(file_name):
        cursor.execute('SELECT file_name FROM song_table WHERE block_number=?',block_num)
        old_file = cursor.fetchone()['file_name']
        shutil.copyfile(file_name, '/home/chris/media/SongBlocks/%s' % file_name)
        cursor.execute('UPDATE song_table SET song_name=?, file_name=? WHERE block_number=?', (title, file_name, block_num))
        db.commit()
        os.remove('/home/chris/media/SongBlocks/%s' % old_file)
        print('Block Updated')
        return True
    else:
        print('File or Block not found')
        return False


def add_block(title, file_name, block_num, tag_id=None):
    if tag_id is None:
        nfc = nxppy.Mifare()
        while True:
            try:
                tag_id = nfc.select()
                break
            except nxppy.SelectError:
                pass
            time.sleep(1)
    cursor = db.cursor()
    cursor.execute('SELECT * FROM block_table WHERE tag_id=? OR block_number=?', (tag_id, block_num))
    if cursor.fetchone() is None and os.path.isfile(file_name):
        cursor.execute('INSERT INTO block_table (block_number, tag_id) VALUES (?, ?)', (block_num, tag_id))
        cursor.execute('INSERT INTO song_table (song_name, file_name, block_number) VALUES (?, ?, ?)', (title, file_name, block_num))
        shutil.copyfile(file_name, '/home/chris/media/SongBlocks/%s' % file_name)
        db.commit()
        print('Block Added')
        return True
    else:
        print('Block or Tag already in use or File not Found')
        return False


if __name__ == '__main__':
    arguments = docopt(__doc__)
    if arguments['add']:
        add_block(arguments['--title'], arguments['--file'], arguments['--block'], arguments['--uid'])
    elif arguments['replace']:
        replace_song(arguments['--title'], arguments['--file'], arguments['--block'])