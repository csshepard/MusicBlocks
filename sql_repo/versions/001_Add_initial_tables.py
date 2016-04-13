from sqlalchemy import Column, Integer, String, Text, DateTime, Interval, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Block(Base):
    __tablename__ = 'blocks'

    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    type = Column(Enum('unset', 'song', 'command', name='block_types'))
    tag_uuid = Column(String(16))
    song_id = Column(Integer, ForeignKey('songs.id'))
    command_id = Column(Integer, ForeignKey('commands.id'))

    song = relationship('Song', back_populates='blocks')
    command = relationship('Command', back_populates='blocks')


class Song(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    file = Column(Text)

    blocks = relationship('Block', back_populates='song')


class Command(Base):
    __tablename__ = 'commands'

    id = Column(Integer, primary_key=True)
    function = Column(Text)
    args = Column(Text)

    blocks = relationship('Block', back_populates='command')


class PlayHistory(Base):
    __tablename__ = 'play_history'

    id = Column(Integer, primary_key=True)
    song_title = Column(Text)
    block_number = Column(Integer)
    time_played = Column(DateTime)
    length_played = Column(Interval)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    Block.__table__.create(migrate_engine)
    Song.__table__.create(migrate_engine)
    Command.__table__.create(migrate_engine)
    PlayHistory.__table__.create(migrate_engine)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    Block.__table__.drop(migrate_engine)
    Song.__table__.drop(migrate_engine)
    Command.__table__.drop(migrate_engine)
    PlayHistory.__table__.drop(migrate_engine)
