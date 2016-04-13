import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from models import *

PATH = os.path.dirname(os.path.realpath(__file__))
engine = create_engine('sqlite:///'+PATH+'/MusicBlocks.db')
Session = sessionmaker(bind=engine)
new_db = Session()
old_db = sqlite3.connect(PATH+'/OldMusicBlocks.db', detect_types=sqlite3.PARSE_DECLTYPES)
old_db.row_factory = sqlite3.Row

song_query = old_db.execute('SELECT * FROM song_table').fetchall()
block_query = old_db.execute('SELECT * FROM block_table').fetchall()
for old_block in block_query:
    new_db.add(Block(number=old_block['block_number'], tag_uuid=old_block['tag_id'], type='song'))
for old_song in song_query:
    new_song = Song(title=old_song['song_name'], file=old_song['file_name'])
    new_db.add(new_song)
    block = new_db.query(Block).filter_by(number=old_song['block_number']).first()
    block.song = new_song
history_query = old_db.execute('SELECT * FROM play_history_table').fetchall()
for old_history in history_query:
    new_db.add(PlayHistory(song_title=old_history['song_name'], time_played=old_history['time_played']))
new_db.commit()
