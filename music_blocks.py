import nxppy
import sqlite3
import os
from subprocess import Popen
from time import sleep
import datetime

db = sqlite3.connection('MusicBlocks.db')
db.row_factory = sqlite.Row

def play_song(block_num):
    query = db.execute('SELECT * FROM song_table WHERE block_number=?',block_num)
    song = query.fetchone()['file_name']
    if os.path.isfile('/media/MusicBlocks/%' % song):
        player = Popen(['mpg123', '-R', '-F', 'Player'], stdin=PIPE, stdout=PIPE)
        player.stdin.write('L /media/MusicBlocks/%\n' % song)
        player.stdin.flush()
        return player
    return None


def stop_song(player):
    player.stdin.write('STOP\nQUIT\n')
    player.stdin.flush()
    player.terminate()


def main_loop():
    nfc = nxppy.Mifare()
    player = None
    While True:
        try:
            uid = mifare.select()
            query = db.execute('SELECT block_table.block_number AS block_number, song_table.song_name AS song_name FROM block_table INNER JOIN song_table ON song_table.block_number = block_table.block_number WHERE block_table.tag_id=?', uid)
            block = query.fetchone()['block_number']
            if block and playing is None:
                player = play_song(block)
                db.execute('INSERT INTO play_history_table (time_played, song_name) VALUES (?, ?)', datetime.now(), song_name)
                db.commit()
        except nxppy.SelectError:
            if player:
                stop_song(player)
                player = None
        sleep(1)


if __name__ == '__main__':
    main_loop()
