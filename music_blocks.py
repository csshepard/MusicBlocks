import nxppy
import sqlite3
import os
from subprocess import Popen, PIPE
from time import sleep
import datetime

db = sqlite3.Connection('MusicBlocks.db')
db.row_factory = sqlite3.Row

def play_song(block_num):
    query = db.execute('SELECT * FROM song_table WHERE block_number=?', (block_num,))
    song = query.fetchone()['file_name']
    if os.path.isfile('/home/pi/Music/MusicBlocks/%s' % song):
        player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=PIPE)
        player.stdin.write('L /home/pi/Music/MusicBlocks/%s\n' % song)
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
    while True:
        try:
            uid = nfc.select()
            query = db.execute('SELECT block_table.block_number AS block_number, song_table.song_name AS song_name FROM block_table INNER JOIN song_table ON song_table.block_number = block_table.block_number WHERE block_table.tag_id=?', (uid,))
            block = query.fetchone()
            if block and player is None:
                player = play_song(block['block_number'])
                #db.execute('INSERT INTO play_history_table (time_played, song_name) VALUES (?, ?)', (datetime.datetime.now(), block['song_name']))
                #db.commit()
                print('Playing %s' % block['song_name'])
        except nxppy.SelectError:
            if player is not None:
                stop_song(player)
                player = None
                print('Stopped Song')
        sleep(1)


if __name__ == '__main__':
    main_loop()
