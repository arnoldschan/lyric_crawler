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
    def __init__(self,artist_obj,song_obj):
        self.artist_obj = artist_obj
        self.song_obj = song_obj
        self.artist_name = self.artist_obj.name
        self.song_title = self.song_obj.title
        self.session = db_session()
        super().__init__(self.lyric_url)

    @property
    def lyric_url(self):
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

    def crawl(self):
        self.get_soup()
        paragraph = self.soup.find('div',class_="lyrics").find('p')
        [ads.extract() for ads in paragraph.find_all('defer-compile')];
        lyric = paragraph.text.strip().replace('\u2005',' ')
        album= self.soup.find(text="Album").parent.nextSibling.nextSibling.text.strip()

        new_lyric = Lyric(self.song_obj.id,lyric)
        new_album = Album(album)
        new_album.song_id = self.song_obj.id
        new_album.artist_id = self.artist_obj.id

        self.session.merge(new_lyric)
        self.session.merge(new_album)
        
        content_info = self.soup.find('div',{"initial-content-for":"track_info"})
        written_soup = content_info.find(text="Written By")
        if written_soup is not None:
            writers = written_soup.parent.nextSibling.nextSibling.text.strip()
            for writer in writers.replace('&',',').split(","):
                new_writer = Writer(writer.strip())
                new_writer = self.session.merge(new_writer)
                self.commit()
                new_songwriter_map = SongWriterMap(self.song_obj.id,new_writer.id)
                self.session.merge(new_songwriter_map)
            self.commit()
        else:
            print(f'writer not found for: {self.artist_name}-{self.song_title}')
        
        distributor_soup = content_info.find(text="Distributor")
        if distributor_soup is not None:
            distributor = distributor_soup.parent.nextSibling.nextSibling.text.strip()
            new_distributor = Distributor(distributor)
            new_distributor = self.session.merge(new_distributor)
            self.commit()
            self.song_obj.distributor_id = new_distributor.id
        else:
            print(f'distributor not found for: {self.artist_name}-{self.song_title}')
        
        label_soup = content_info.find(text="Label")
        if label_soup is not None:
            label = label_soup.parent.nextSibling.nextSibling.text.strip()
            new_label = Label(label)
            new_label = self.session.merge(new_label)
            self.commit()
            self.song_obj.label_id = new_label.id
        else:
            print(f'label not found for: {self.artist_name}-{self.song_title}')
        
        release_date_soup = content_info.find(text="Release Date")
        if release_date_soup is not None:
            release_date = dateparser.parse(release_date_soup.parent.nextSibling.nextSibling.text.strip())
            self.song_obj.release_date = release_date
        else:
            print(f'release date not found for: {self.artist_name}-{self.song_title}')
        self.commit()

    def commit(self):
        self._commit(self.session)
