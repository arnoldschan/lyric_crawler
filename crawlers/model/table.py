from __future__ import absolute_import

from sqlalchemy import Column, Integer, String, Text, DateTime,ForeignKey,Sequence
from crawlers.util.db import ORMBaseClass


class Artist(ORMBaseClass):
    __tablename__ = "artist"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer(), primary_key=True)
    name = Column(String(255))
    def __init__(self,name):
        self.id = None
        self.name = name

class Song(ORMBaseClass):
    __tablename__ = "song"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer(), primary_key=True)
    artist_id = Column(Integer(), ForeignKey('artist.id'))
    title = Column(String(255))
    distributor_id = Column(Integer(),ForeignKey('distributor.id'))
    label_id = Column(Integer(),ForeignKey('label.id'))
    release_date = Column(DateTime())
    spotify_link = Column(String(255), unique=True)
    def __init__(self,title,spotify_link):
        self.id = None
        self.artist_id = None
        self.title = title
        self.spotify_link = spotify_link
        self.distributor_id = None
        self.label_id = None
        self.release_date = None

class Chart(ORMBaseClass):
    __tablename__ = "chart"
    __table_args__ = {'extend_existing': True}
    record_id = Column(Integer(), primary_key=True)
    rank = Column(Integer(), primary_key=True)
    date = Column(DateTime(), primary_key=True)
    song_id = Column(Integer(), ForeignKey("song.id"))
    stream = Column(Integer())
    def __init__(self):
        self.record_id = None
        self.rank = None
        self.date = None
        self.song_id = None
        self.stream = None

class Lyric(ORMBaseClass):
    __tablename__ = "lyric"
    __table_args__ = {'extend_existing': True}
    song_id = Column(Integer(), ForeignKey('song.id'), primary_key=True)
    lyric = Column(Text())
    def __init__(self,song_id,lyric):
        self.song_id = song_id
        self.lyric = lyric

class Album(ORMBaseClass):
    __tablename__ = "album"
    __table_args__ = {'extend_existing': True}
    song_id = Column(Integer(), ForeignKey('song.id'), primary_key=True)
    artist_id = Column(Integer(), ForeignKey('artist.id'), primary_key=True)
    title = Column(String(255))
    def __init__(self,title):
        self.song_id = None
        self.artist_id = None
        self.title = title

class Writer(ORMBaseClass):
    __tablename__ = "writer"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer(), primary_key=True)
    name = Column(String(255))
    def __init__(self,name):
        self.id = None
        self.name = name
    
class SongWriterMap(ORMBaseClass):
    __tablename__ = "song_writer_map"
    __table_args__ = {'extend_existing': True}
    song_id = Column(Integer(), ForeignKey('song.id'), primary_key=True)
    writer_id = Column(Integer(), ForeignKey('writer.id'), primary_key=True)
    def __init__(self,song_id,writer_id):
        self.song_id = song_id
        self.writer_id = writer_id

class Distributor(ORMBaseClass):
    __tablename__ = "distributor"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer(), primary_key=True)
    name = Column(String(255))
    def __init__(self,name):
        self.id = None
        self.name = name

class SongDistributorMap(ORMBaseClass):
    __tablename__ = "song_distributor_map"
    __table_args__ = {'extend_existing': True}
    song_id = Column(Integer(), ForeignKey('song.id'), primary_key=True)
    distributor_id = Column(Integer(), ForeignKey('distributor.id'), primary_key=True)
    def __init__(self,song_id,distributor_id):
        self.song_id = song_id
        self.distributor_id = distributor_id

class Label(ORMBaseClass):
    __tablename__ = "label"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer(), primary_key=True)
    name = Column(String(255))
    def __init__(self,name):
        self.id = None
        self.name = name
    
class SongLabelMap(ORMBaseClass):
    __tablename__ = "song_label_map"
    __table_args__ = {'extend_existing': True}
    song_id = Column(Integer(), ForeignKey('song.id'), primary_key=True)
    label_id = Column(Integer(), ForeignKey('label.id'),primary_key=True)
    def __init__(self,label_id):
        self.song_id = None
        self.label_id = label_id

    
    
