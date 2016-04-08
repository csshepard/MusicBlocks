import atexit
import nxppy
import sqlite3
import os
import sys
from subprocess import Popen, PIPE
from time import sleep
from datetime import datetime


PATH = os.path.dirname(os.path.realpath(__file__))


class Player(object):
    def __init__(self):
        self._playing = False
        self._quit = False
        self.current_file = ''
        try:
            self._player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=PIPE)
            self._player.stdin.write('SILENCE\n')
            self._player.stdin.flush()
        except OSError:
            sys.exit("Error Running mpg123.\n Run 'apt-get install mpg123'")
        self.volume = 100.0


    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        if self._quit:
            return
        if value < 0.0:
            self._volume = 0.0
        elif value > 100.0:
            self._volume = 100.0
        else:
            self._volume = float(value)
        self._player.stdin.write('V %f\n' % self._volume)
        self._player.stdin.flush()


    def play_song(self, path):
        if self._quit or not os.path.isfile(path):
            return False
        if self.is_playing():
            self.stop_song()
        self._player.stdin.write('L %s\n' % path)
        self._player.stdin.flush()
        self._playing = True
        self.current_file = path
        return True


    def stop_song(self):
        if self._quit or not self.is_playing():
            return False
        self._player.stdin.write('S\n')
        self._player.stdin.flush()
        self._player.stdout.flush()
        self._playing = False
        self.current_file = ''
        return True


    def is_playing(self):
        return self._playing


    def quit(self):
        if not self._quit:
            self._player.communicate('S\nQ\n')
            self._quit = True


def get_db(path):
    if not os.path.isfile(path):
        sys.exit("Database not found.\n"
                 "Run 'python manage_songs.py' to create db and insert songs")
    db = sqlite3.connect(PATH+'/MusicBlocks.db', detect_types=sqlite3.PARSE_DECLTYPES,
                         isolation_level=None)
    db.row_factory = sqlite3.Row
    return db


def quitblocks(db, player):
    db.close()
    player.quit()


def main_loop():
    nfc = nxppy.Mifare()
    db = get_db(PATH+'/MusicBlocks.db')
    player = Player()
    playing_uid = ''
    atexit.register(quitblocks, db, player)
    while True:
        try:
            uid = nfc.select()
            if playing_uid != uid:
                player.stop_song()
                query = db.execute("""\
                    SELECT block_table.block_number AS block_number,
                    song_table.song_name AS song_name,
                    song_table.file_name AS file_name FROM block_table
                    INNER JOIN song_table
                    ON song_table.block_number = block_table.block_number
                    WHERE block_table.tag_id=?
                    """, (uid,))
                block = query.fetchone()
                if block:
                    player.play_song(PATH+'/Music/%s' % block['file_name'])
                    db.execute("""\
                        INSERT INTO play_history_table (time_played, song_name)
                        VALUES (?, ?)
                        """, (datetime.now(), block['song_name']))
                    playing_uid = uid
                    print('Playing %s' % block['song_name'])
        except nxppy.SelectError:
            if player.stop_song():
                print('Stopped Song')
                playing_uid = ''
        sleep(1)


if __name__ == '__main__':
    main_loop()
