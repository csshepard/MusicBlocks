#!/usr/bin/env python

"""
Manage Music Blocks

Usage:
  manage_songs.py add -b <block_number> [-t <title>] -f <file_name> [--uid=<tag_id>]
  manage_songs.py replace -b <block_number> [-t <title>] -f <file_name>
  manage_songs.py remove -b <block_number>
  manage_songs.py status
  manage_songs.py history
  manage_songs.py -h | --help

Options:
  -h --help                                  Show this screen.
  -b <block_number>, --block=<block_number>  Integer printed on block.
  -t <title>, --title=<title>                (optional) Song Title.
  -f <file_name>, --file=<file_name>         File name of song.
  --uid=<tag_id>                             (optional) uid of NFC tag
"""

from __future__ import print_function
import nxppy
import os
import shutil
import time
from docopt import docopt
import sys
from datetime import datetime
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from models import *


PATH = os.path.dirname(os.path.realpath(__file__))

engine = create_engine('sqlite:///'+PATH+'/MusicBlocks.db')
if not os.path.isfile(PATH+'/MusicBlocks.db'):
    Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()


def file2title(file_name):
    title = os.path.splitext(file_name)[0]
    title = title.replace('.', ' ').replace('_', ' ').title()
    return title


def replace_song(title, file_name, block_num):
    block = db.query(Block).filter_by(number=block_num).one_or_none()
    if block is not None:
        filename = os.path.basename(file_name)
        song = db.query(Song).filter_by(file=filename).one_or_none()
        if song:
            block.song = song
            db.commit()
            print('Block Updated')
            return True
        if title is None:
            title = file2title(song)
        try:
            shutil.copyfile(file_name, PATH+'/Music/%s' % filename)
        except IOError as e:
            print(e)
            return False
        song = Song(title=title, file=filename)
        db.add(song)
        block.song = song
        db.commit()
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
    block = db.query(Block).filter(or_(Block.number == block_num, Block.tag_uuid == tag_id)).first()
    if block is None:
        block = Block(number=block_num, tag_uuid=tag_id, type='song')
        basename = os.path.basename(file_name)
        song = db.query(Song).filter_by(file=basename).one_or_none()
        if song:
            block.song = song
        else:
            if title is None:
                title = file2title(basename)
            try:
                shutil.copyfile(file_name, PATH+'/Music/%s' % basename)
            except IOError as e:
                db.rollback()
                print(e)
                return False
            song = Song(title=title, file=basename)
            db.add(song)
            block.song = song
            db.add(block)
        db.commit()
        print('Block Added')
        return True
    else:
        if block.number == int(block_num):
            print('Block already in use')
        if block.tag_uuid == tag_id:
            print('Tag already in use')
        return False


def remove_block(block_num):
    block = db.query(Block).filter_by(number=block_num).one_or_none()
    if block is not None:
        db.delete(block)
        db.commit()
        print('Block %s Deleted' % block_num)
        return True
    else:
        print('Block %s not found' % block_num)
        return False


def status():
    blocks = db.query(Block).order_by(Block.number)
    row = '{:^14}{:^32}{:^16}'
    print(row.format('Block Number', 'Song', 'Tag ID'))
    for block in blocks:
        print(row.format(block.number, block.song.title,
                         block.tag_uuid))


def history():
    history = db.query(PlayHistory).order_by(PlayHistory.time_played)
    row = '{:^21}{:^32}'
    print(row.format('Date/Time', 'Song'))
    for entry in history:
        print(row.format(entry.time_played.strftime('%m/%d/%y %I:%M:%S %p'), entry.song_title))


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
    elif args['history']:
        history()
    db.close()
