import requests
from urllib.parse import quote
import pandas as pd
from io import StringIO
from unidecode import unidecode
import re
import dateparser
import json
from crawlers.util.db import db_session
from crawlers.model.crawler import CrawlerBase
from crawlers.model.table import (
    Chart, Artist, Song, Lyric, Album, Writer, SongWriterMap, Distributor, SongDistributorMap, Label, SongLabelMap)
from crawlers.util.db import ORMBaseClass, engine
# ORMBaseClass.metadata.drop_all(bind=engine)
# ORMBaseClass.metadata.create_all(bind=engine)
class LyricCrawler(CrawlerBase):
    """Crawling Lyric from www.genius.com
    Default input from Spotify's data
    However, if the crawler couldn't find the default lyric,
    it would fetch lyric from the first search result
    in genius.
    Parameter:
    :artist_name: singer name
    :song_title: title of the song"""

    def __init__(self,artist_name,song_title)    :
        self.artist_name = artist_name
        self.song_title = song_title
        self.album = None
        self.writer = None
        self.distributor = None
        self.label = None
        self.lyric = None
        self.release_date = None
        super().__init__(self.lyric_url)

    @property
    def lyric_url(self):
        """generate the default form of lyric's link"""
        def combine_with_dash(list_,first_cap=True):
            def remove_symbol(word,symbols):
                for symbol in symbols:
                    word = word.replace(symbol,'')
                return word
            result = ""
            symbols = ["'",'"',"/",".",","]
            if first_cap:
                result += remove_symbol(list_[0].capitalize(),symbols)
                list_.pop(0)
            for member in list_:
                result+="-"+ remove_symbol(member.lower(),symbols)
            return result
        artist_coded = combine_with_dash(self.artist_name.split())
        clean_track_name = self.song_title.replace(r"\(.*\)","")
        track_name_coded = combine_with_dash(clean_track_name.split(),False)
        artist_and_track = artist_coded + track_name_coded
        return unidecode("https://genius.com/" + artist_and_track +"-"+"lyrics")
    
    @property
    def fallback_url(self):
        """if the default url couldn't be found, it'll use search result"""
        combine = self.song_title + self.artist_name
        return unidecode("https://genius.com/search?q="+quote(combine))

    def get_soup(self):
        response = self.get()
        if response.status_code != 200:
            self.url = self.fallback_url
            html = self.get()
            if html.status_code != 200:
                raise "URL NOT FOUND"
            self.url = json.loads(html.text)['response']['sections'][0]['hits'][0]['result']['url']
            print(f"this {self.url}")
            response = self.get()
            if response.status_code != 200:
                raise "URL NOT FOUND"

    def run(self):
        """get, and save the information in self.result
        
        Returns:
            [self] -- [LyricCrawler object]
        """        
        #do the request
        self.get_soup()

        paragraph = self.soup.find('div',class_="lyrics").find('p')
        [ads.extract() for ads in paragraph.find_all('defer-compile')];

        # saving lyric and album
        self.lyric = paragraph.text.strip().replace('\u2005',' ')
        self.album= self.soup.find(text="Album").parent.nextSibling.nextSibling.text.strip()
        
        content_info = self.soup.find('div',{"initial-content-for":"track_info"})
        writer_soup = content_info.find(text="Written By")

        # saving song writer
        if writer_soup is not None:
            writers = writer_soup.parent.nextSibling.nextSibling.text.strip()
            self.writer = []
            for writer in writers.replace('&',',').split(","):
                self.writer.append(writer)
        else:
            print(f'writer not found for: {self.artist_name}-{self.song_title}')
        
        # save song's distributor
        distributor_soup = content_info.find(text="Distributor")
        if distributor_soup is not None:
            self.distributor = distributor_soup.parent.nextSibling.nextSibling.text.strip()
        else:
            print(f'distributor not found for: {self.artist_name}-{self.song_title}')
        # save song's label
        label_soup = content_info.find(text="Label")
        if label_soup is not None:
            self.label = label_soup.parent.nextSibling.nextSibling.text.strip()
        else:
            print(f'label not found for: {self.artist_name}-{self.song_title}')
        # save song's release date
        release_date_soup = content_info.find(text="Release Date")
        if release_date_soup is not None:
            self.release_date = dateparser.parse(release_date_soup.parent.nextSibling.nextSibling.text.strip())
        else:
            print(f'release date not found for: {self.artist_name}-{self.song_title}')
        self.result = {"artist_name": self.artist_name,
                "song_title": self.song_title,
                "album": self.album,
                "writer": self.writer,
                "distributor": self.distributor,
                "label": self.label,
                "lyric": self.lyric,
                "release_date": self.release_date
                }
        self.status = True
        return self

    def to_db(self,song_obj, artist_obj, db_session):
        """Saving information to database
        
        Arguments:
            song_obj {[Song]} -- [needed to update the song object]
            artist_obj {[Artist]} -- [needed to update the artist object]
            db_session {[mysqlalchemy.session]} -- [SQL session engine connector]
        """        
        self.session = db_session
        # write lyric
        new_lyric = Lyric(song_obj.id,self.lyric)
        self.session.merge(new_lyric)

        # write album
        new_album = Album(self.album)
        new_album.song_id = song_obj.id
        new_album.artist_id = artist_obj.id
        self.session.merge(new_album)

        # write writer
        if isinstance(self.writer, str):
            self.writer = list(self.writer)
        if isinstance(self.writer, list):
            for writer in self.writer:
                new_writer = Writer(writer)
                new_writer = self.session.merge(new_writer)
                self.session.commit()
                new_songwriter_map = SongWriterMap(song_obj.id,new_writer.id)
                self.session.merge(new_songwriter_map)

        # distributor
        if self.distributor is not None:
            new_distributor = Distributor(self.distributor)
            new_distributor = self.session.merge(new_distributor)
            self.session.commit()

        # label
        if self.label is not None:
            new_label = Label(self.label)
            new_label = self.session.merge(new_label)
            self.session.commit()

        # add attribute in song obj
        if self.label is not None:
            song_obj.label_id = new_label.id
        if self.distributor is not None:
            song_obj.distributor_id = new_distributor.id
        song_obj.release_date = self.release_date
        self.session.commit()
